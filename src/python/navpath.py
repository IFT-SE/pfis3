import sqlite3
import iso8601
from pfigFileHeader import PFIGFileHeader
from knownPatches import KnownPatches

class NavigationPath(object):
    
    TEXT_SELECTION_OFFSET_QUERY = "SELECT timestamp, action, target, referrer FROM logger_log WHERE action = 'Text selection offset' ORDER BY timestamp"
    METHOD_DECLARATIONS_QUERY = "SELECT timestamp, action, target, referrer from logger_log WHERE action IN ('Method declaration', 'Method declaration offset', 'Method declaration length') AND timestamp <= ? ORDER BY timestamp"
    
    def __init__(self, dbFilePath, langHelper, projectFolderPath, verbose = False):
        self.navigations = []
        self.fileNavigations = []
        self.dbFilePath = dbFilePath
        self.knownPatches = KnownPatches(langHelper)
        self.langHelper = langHelper
        self.projectFolderPath = projectFolderPath
        self.VERBOSE_PATH = verbose

        conn = sqlite3.connect(self.dbFilePath)
        print conn

        conn.row_factory = sqlite3.Row
        
        if self.VERBOSE_PATH:
            print 'Building path...'
        self.__findFileNavigationsInDb(conn)
        self.__findMethodsForFileNavigations(conn)
        if self.VERBOSE_PATH:
            print 'Done building path.'
        self.__printNavigations()
        conn.close()
        
    def __findFileNavigationsInDb(self, conn):
        # Here, we find all the instances of Text selection offset actions in
        # the PFIG log. These are stored into the self.fileNavigations list. We
        # remove any obvious duplicates that have the same file path and offset
        # in this function. We store time stamps here since they will be used to
        # determine if self.knownMethods entries need to be added or updated.
        c = conn.cursor()
        c.execute(self.TEXT_SELECTION_OFFSET_QUERY)
        
        prevFilePath = None
        prevOffset = None
        
        for row in c:
            timestamp, filePath, offset = \
                str(iso8601.parse_date(row['timestamp'])), row['target'], int(row['referrer'])

            if prevFilePath != filePath:
                if prevOffset != offset: #This is for a Java PFIG bug / peculiarity -- duplicate navs to same offset in  Java DB
                    if self.langHelper.hasCorrectExtension(filePath):
                        self.fileNavigations.append(FileNavigation(timestamp, filePath, offset))
                
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
        for i in range(len(self.fileNavigations)):
            toNavigation = self.fileNavigations[i]
            if self.VERBOSE_PATH:
                print '\tProcessing text selection offset: ' + str(toNavigation)
            
            # For every navigation's timestamp, we fill the knownMethods object
            # with the details of every method declaration up to the timestamp
            # of the toNavigation. The knownMethods object will be queried to
            # determine in which method (if any) a text selection offset occurs.
            
            # Note that the queries here are by a method's FQN. This allows us
            # to update the method's declaration info if it gets updated at some
            # point in the future.

            c = conn.execute(self.METHOD_DECLARATIONS_QUERY, [toNavigation.timestamp])
            for row in c:
                action, target, referrer = row['action'], \
                    row['target'], row['referrer']
                
                if action == 'Method declaration':
                    self.knownPatches.addFilePatch(referrer)
                elif action == 'Method declaration offset':
                    method = self.knownPatches.findMethodByFqn(target)
                    if method is not None:
                        method.startOffset = int(referrer)
                elif action == 'Method declaration length':
                    method = self.knownPatches.findMethodByFqn(target)
                    if method is not None:
                        method.length = int(referrer);
                        
            # We query known methods here to see if the offset of the current
            # toNavigation is among the known patches.
            toMethodPatch = self.knownPatches.findMethodByOffset(toNavigation.filePath, toNavigation.offset)
            fromNavigation = None
            fromMethodPatch = None
            
            # Recall that navigations contains the navigation data after its
            # been translated to methods and headers
            
            # If there was at least 1 navigation already, the to destination
            # from the previous navigation serves as this navigations from. A
            # clone is necessary since this may be later transformed into a 
            # PFIG header and we don't want to affect the to destination from
            # the previous navigation.
            
            if len(self.navigations) > 0:
                prevNavigation = self.navigations[-1]
                fromNavigation = prevNavigation.toFileNav.clone()
                fromMethodPatch = self.knownPatches.findMethodByOffset(fromNavigation.filePath, fromNavigation.offset)
            
            # Create the navigation object representing this navigation
            navigation = Navigation(fromNavigation, toNavigation.clone())
            
            # Set method FQN data
            if navigation.fromFileNav is not None and fromMethodPatch is not None:
                navigation.fromFileNav.methodFqn = fromMethodPatch.fqn
            if navigation.toFileNav is not None and toMethodPatch is not None:
                navigation.toFileNav.methodFqn = toMethodPatch.fqn
            
            if not navigation.isToSameMethod():
                self.__addPFIGFileHeadersIfNeeded(conn, prevNavigation, navigation)
                self.navigations.append(navigation)
                
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
        
        for navigation in self.navigations:
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
                    
        self.navigations = finalNavigations
        
    def __addPFIGFileHeadersIfNeeded(self, conn, prevNav, currNav):
        # If it's the first navigation, don't do anything
        if prevNav is None:
            return 
        
        # If the previous navigation's to is not a known method and the current
        # navigation's from is the same unknown method, then this might need to
        # be converted to a header.
        if prevNav.isToUnknown() and currNav.isFromUnknown():
            if self.knownPatches.findMethodByOffset(currNav.fromFileNav.filePath, currNav.fromFileNav.offset) is None:
                if prevNav.toFileNav.filePath == currNav.fromFileNav.filePath and prevNav.toFileNav.offset == currNav.fromFileNav.offset:
                    if self.VERBOSE_PATH:
                            print '\tChecking if ' + str(prevNav.toFileNav) + ' is a header...'
                    headerData = PFIGFileHeader.addPFIGJavaFileHeader(conn, currNav, self.projectFolderPath, self.langHelper)
                    
                    # If headerData comes back as not None, then it was indeed a
                    # header and needs to be added to navigation and 
                    # knownPatches.
                    if headerData is not None:
                        if self.VERBOSE_PATH:
                            print '\tConverted to ' + headerData.fqn
                        
                        # Add to the navigation and the knownPatches
                        currNav.fromFileNav.methodFqn = headerData.fqn
                        self.knownPatches.addFilePatch(headerData.fqn)
                        
                        # Update the properties
                        method = self.knownPatches.findMethodByFqn(headerData.fqn)
                        method.startOffset = 0
                        method.length = headerData.length
                    
                    elif self.VERBOSE_PATH:
                        print '\tNot a header.'
            
    
    def __printNavigations(self):
        print "Navigation path:"
        for i in range(len(self.navigations)):
            navigation = self.navigations[i]
            print '\t' + str(i) + ':\t' + str(navigation)
            
    def getLength(self):
        return len(self.navigations)

class Navigation(object):
    # A navigation is a tuple representing one programmer navigation through the
    # code. fromFileNav represents the where the programmer navigated from and 
    # toFileNav represents where the programmer navigated to. Both of these
    # parameters should be FileNavigation objects.
    def __init__(self, fromFileNav, toFileNav):
        self.fromFileNav = fromFileNav
        self.toFileNav = toFileNav
        
    def isToSameMethod(self):
        if self.fromFileNav is not None and self.toFileNav is not None:
            if self.fromFileNav.methodFqn is not None and self.toFileNav.methodFqn is not None:
                return self.fromFileNav.methodFqn == self.toFileNav.methodFqn
        return False
    
    def isFromUnknown(self):
        if self.fromFileNav is not None and self.fromFileNav.methodFqn is not None:
            return False
        return True
    
    def isToUnknown(self):
        if self.toFileNav is not None and self.toFileNav.methodFqn is not None:
            return False
        return True
    
    def clone(self):
        return Navigation(self.fromFileNav.clone(), self.toFileNav.clone())
        
    def __str__(self):
        fromLoc = None
        toLoc = None
        
        if self.fromFileNav is not None:
            fromLoc = str(self.fromFileNav)
        if self.toFileNav is not None:
            toLoc = str(self.toFileNav)
            
        return str(fromLoc) + ' --> ' + str(toLoc)
        
class FileNavigation(object):
    # A file navigation represents the Text selection offset data that was 
    # captured by PFIG. The Text selection offset occurs any time a programmer's
    # text cursor position changes. If we determine that the text cursor is in a
    # method that the programmer has knowledge of then, methodFqn has that info.
    # If methodFqn is none, then this was a navigation to an 'unknown location'
    def __init__(self, timestamp, filePath, offset):
        self.timestamp = timestamp
        self.filePath = filePath;
        self.offset = offset
        self.methodFqn = None
        self.isGap = False
        
    def clone(self):
        fileNavClone = FileNavigation(self.timestamp, self.filePath, self.offset)
        fileNavClone.methodFqn = self.methodFqn
        return fileNavClone
        
    def __str__(self):
        if self.methodFqn is not None:
            return self.methodFqn
        return str(self.filePath) + ' at ' + str(self.offset)
        