import sqlite3
import iso8601
from pfigFileHeader import PFIGFileHeader
from knownPatches import KnownPatches
from navigation import Navigation
from navigation import FileNavigation

class NavigationPath(object):

    DEFAULT = "Default"
    VARIANT_AWARE = "VariantAware"
    VARIANT_AWARE_COLLAPSED = "VariantAwareCollapsed"
    TEXT_SELECTION_OFFSET_QUERY = "SELECT timestamp, action, target, referrer FROM logger_log WHERE action = 'Text selection offset' ORDER BY timestamp"
    METHOD_DECLARATIONS_QUERY = "SELECT timestamp, action, target, referrer from logger_log WHERE action IN ('Method declaration', 'Method declaration offset', 'Method declaration length') AND timestamp <= ? ORDER BY timestamp"

    def __init__(self, dbFilePath, langHelper, projectFolderPath, verbose = False):
        self.dbFilePath = dbFilePath
        self.langHelper = langHelper
        self.projectFolderPath = projectFolderPath
        self.VERBOSE_PATH = verbose

        self.__fileNavigations = []
        self._navigations = []

        self._name = NavigationPath.DEFAULT
        #Do not account for similar patches across variants
        self.knownPatches = KnownPatches(langHelper)

        conn = sqlite3.connect(self.dbFilePath)
        conn.row_factory = sqlite3.Row

        if self.VERBOSE_PATH:
            print 'Building path...'
        self.__findFileNavigationsInDb(conn)
        self.__findMethodsForFileNavigations(conn)
        if self.VERBOSE_PATH:
            print 'Done building path.'
        self._printNavigations()
        conn.close()


    def getNavPathType(self):
        return self._name

    def __findFileNavigationsInDb(self, conn):
        # Here, we find all the instances of Text selection offset actions in
        # the PFIG log. These are stored into the self.__fileNavigations list. We
        # remove any obvious duplicates that have the same file path and offset
        # in this function. We store time stamps here since they will be used to
        # determine if self.knownMethods entries need to be added or updated.
        c = conn.cursor()
        c.execute(self.TEXT_SELECTION_OFFSET_QUERY)

        prevFilePath = None
        prevOffset = None

        for row in c:
            timestamp, filePath, offset = str(iso8601.parse_date(row['timestamp'])), row['target'], int(row['referrer'])

            if prevFilePath != filePath or prevOffset != offset: #This is for a Java PFIG bug / peculiarity -- duplicate navs to same offset in  Java DB
                    if self.langHelper.isNavToValidFileType(filePath):
                        #TODO: implement this!
                        #patchType = self.langHelper.getPatchType(filePath)
                        patchType=None
                        self.__fileNavigations.append(FileNavigation(timestamp, filePath, offset, patchType))

            prevFilePath = filePath
            prevOffset = offset
        c.close()

    def __findMethodsForFileNavigations(self, conn):
        # Here we map the file paths and offsets in the fileNavigations list to
        # FQNs of methods. This is done by querying for all the Method
        # declarations within the database and storing that data to the
        # self.knownMethods object. The insertions into knownMethods will create
        # entries if they are new or update them if they already exist. Since
        # code can be changed between navigations, we need to update
        # self.knownMethods to reflect the most recent state of the code up to
        # each navigation.
        # After building the known methods, we test an entry from
        # fileNavigations against the set of known methods by offset. This is
        # what maps Text selection offsets to methods.
        prevNavigation = None
        postProcessing = False

        # Iterate over the data gathered from the Text selection offsets
        for i in range(len(self.__fileNavigations)):
            toFileNavigation = self.__fileNavigations[i]
            if self.VERBOSE_PATH:
                print '\tProcessing text selection offset: ' + str(toFileNavigation)

            # For every navigation's timestamp, we fill the knownMethods object
            # with the details of every method declaration up to the timestamp
            # of the toFileNavigation. The knownMethods object will be queried to
            # determine in which method (if any) a text selection offset occurs.

            # Note that the queries here are by a method's FQN. This allows us
            # to update the method's declaration info if it gets updated at some
            # point in the future.

            c = conn.execute(self.METHOD_DECLARATIONS_QUERY, [toFileNavigation.timestamp])
            for row in c:
                action, target, referrer = row['action'], row['target'], row['referrer']

                if action == 'Method declaration' or action=='Changelog declaration':
                    self.knownPatches.addFilePatch(referrer)
                elif action == 'Method declaration offset':
                    method = self.knownPatches.findMethodByFqn(target)
                    if method is not None:
                        method.startOffset = int(referrer)
                elif action == 'Method declaration length':
                    method = self.knownPatches.findMethodByFqn(target)
                    if method is not None:
                        method.length = int(referrer)

            # Recall that navigations contains the navigation data after its
            # been translated to methods and headers

            # If there was at least 1 navigation already, the to destination
            # from the previous navigation serves as this navigations from. A
            # clone is necessary since this may be later transformed into a
            # PFIG header and we don't want to affect the to destination from
            # the previous navigation.

            fromFileNavigation = None
            fromMethodPatch = None

            if len(self._navigations) > 0:
                prevNavigation = self._navigations[-1]
                fromFileNavigation = prevNavigation.toFileNav.clone()
                #TODO: remove this hardcoded js debug thingy!
                if 'js' in fromFileNavigation.filePath:
                    self.__addPFIGFileHeadersIfNeeded(conn, prevNavigation, toFileNavigation)
                fromMethodPatch = self.knownPatches.findPatchByOffset(fromFileNavigation.filePath, fromFileNavigation.offset)


            # We query known methods here to see if the offset of the current
            # toFileNavigation is among the known patches.
            toMethodPatch = self.knownPatches.findPatchByOffset(toFileNavigation.filePath, toFileNavigation.offset)


            # Create the navigation object representing this navigation
            navigation = Navigation(fromFileNavigation, toFileNavigation.clone())

            # Set method FQN data
            if navigation.fromFileNav is not None and fromMethodPatch is not None:
                navigation.fromFileNav.methodFqn = fromMethodPatch.fqn
            if navigation.toFileNav is not None and toMethodPatch is not None:
                navigation.toFileNav.methodFqn = toMethodPatch.fqn

            if not navigation.isToSameMethod():
                self._navigations.append(navigation)

                if navigation.fromFileNav is not None:
                    if navigation.fromFileNav.methodFqn is None:
                        postProcessing = True
                        navigation.fromFileNav.isGap = True
                        prevNavigation.toFileNav.isGap = True
            c.close()

        if postProcessing:
            self.__removeGapNavigations()

    def __removeGapNavigations(self):
        # We do a second pass over the navigations so that we remove any
        # parts of the navigation that have been previously identified as being
        # a navigation to a gap (a space between two method definitions).
        finalNavigations = []
        fromNav = None
        toNav = None
        foundGap = False

        for navigation in self._navigations:
            #TODO: SS|BP: externalize hard-coded changelog file name to config.
            # May be do a "patch-type" and use that for this check.
            if 'changes.txt' in navigation.toFileNav.filePath:
                navigation.toFileNav.isGap = False
            if not foundGap:
                if navigation.fromFileNav is None:
                    if navigation.toFileNav.isGap:
                        fromNav = navigation.fromFileNav
                        foundGap = True
                    else:
                        finalNavigations.append(navigation)
                elif not navigation.fromFileNav.isGap and navigation.toFileNav.isGap:
                    fromNav = navigation.fromFileNav
                    foundGap = True
                elif navigation.fromFileNav.isGap and navigation.toFileNav.isGap:
                    raise RuntimeError('removeGapNavigations: cannot have a navigation with a fromFileNav that is a gap without a prior navigation with a gap in the toFileNav')
                else:
                    if not navigation.isToSameMethod():
                        finalNavigations.append(navigation)
            elif foundGap:
                if navigation.fromFileNav.isGap and not navigation.toFileNav.isGap:
                    toNav = navigation.toFileNav
                    foundGap = False
                    newNavigation = Navigation(fromNav, toNav)
                    if not newNavigation.isToSameMethod():
                        finalNavigations.append(Navigation(fromNav, toNav))
                elif navigation.fromFileNav.isGap and navigation.toFileNav.isGap:
                    continue
                else:
                    raise RuntimeError('removeGapNavigations: cannot have a fromFileNav without a gap if the prior navigation had a gap in the toFileNav')

        self._navigations = finalNavigations

    def __addPFIGFileHeadersIfNeeded(self, conn, prevNav, currToFileNav):
        # If it's the first navigation, don't do anything
        if prevNav is None:
            return

        # If the previous navigation's to is not a known method and the current
        # navigation's from is the same unknown method, then this might need to
        # be converted to a header.
        #TODO: Sruti: Can this be otherwise? why this equality check?

        if prevNav.isToUnknown():
            previousNavToMethod = self.knownPatches.findPatchByOffset(prevNav.toFileNav.filePath, prevNav.toFileNav.offset)
            if previousNavToMethod is None:
                if self.VERBOSE_PATH:
                        print '\tChecking if ' + str(prevNav.toFileNav) + ' is a header...'
                headerData = PFIGFileHeader.addPFIGJavaFileHeader(conn, prevNav, currToFileNav, self.projectFolderPath, self.langHelper)

                # If headerData comes back as not None, then it was indeed a
                # header and needs to be added to navigation and
                # knownPatches.
                if headerData is not None:
                    if self.VERBOSE_PATH:
                        print '\tConverted to ' + headerData.fqn

                    # Add to the knownPatches
                    self.knownPatches.addFilePatch(headerData.fqn)

                    # Update the properties
                    method = self.knownPatches.findMethodByFqn(headerData.fqn)
                    method.startOffset = 0
                    method.length = headerData.length

                elif self.VERBOSE_PATH:
                    print '\tNot a header.'

    def getNavigation(self, i):
        return self._navigations[i]

    def getLength(self):
        return len(self._navigations)

    def _printNavigations(self):
        print "Navigation path:"
        for i in range(len(self._navigations)):
            navigation = self._navigations[i]
            print '\t' + str(i) + ':\t' + str(navigation)

    def getPriorNavToSimilarPatchIfAny(self, navNumber):
        raise Exception("Looking for similar patch in default navpath: ", navNumber)

    def getDefaultNavigation(self,i):
        return self._navigations[i]
