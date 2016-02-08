import sqlite3
import iso8601
from pfigFileHeader import PFIGFileHeader
from knownPatches import KnownPatches

class NavPath:
    def __init__(self):
        self.navPath = []

    def addEntry(self, entry):
        self.navPath.append(entry)
        l = len(self.navPath)
        if l > 1:
            entry.prevEntry = self.navPath[l - 2]

    def __iter__(self):
        return self.navPath.__iter__()

    def isUnknownMethodAt(self, index):
        return self.navPath[index].unknownMethod

    def getLength(self):
        return len(self.navPath)

    def getEntryAt(self, index):
        return self.navPath[index]

    def getMethodAt(self, index):
        return self.navPath[index].method

    def getTimestampAt(self, index):
        return self.navPath[index].timestamp

    def getPrevEntryAt(self, index):
        return self.navPath[index].prevEntry

    def removeAt(self, index):
        del self.navPath[index]

    def toStr(self):
        out = 'NavPath:\n'
        for entry in self.navPath:
            out += '\t' + entry.method + ' at ' + entry.timestamp +'\n'
        return out

class NavPathEntry:
    def __init__(self, timestamp, method):
        self.timestamp = str(timestamp)
        self.method = method
        self.prevEntry = None
        self.unknownMethod = False

        if method.__contains__("UNKNOWN"):
            self.unknownMethod = True;
            
### REFACTORING STARTS HERE
            
class NavigationPath(object):
    
    TEXT_SELECTION_OFFSET_QUERY = "SELECT timestamp, action, target, referrer FROM logger_log WHERE action = 'Text selection offset' ORDER BY timestamp"
    METHOD_DECLARATIONS_QUERY = "SELECT timestamp, action, target, referrer from logger_log WHERE action IN ('Method declaration', 'Method declaration offset', 'Method declaration length') AND timestamp <= ? ORDER BY timestamp"
    
    def __init__(self, dbFilePath, langHelper, projectFolderPath):
        self.navigations = []
        self.fileNavigations = []
        self.dbFilePath = dbFilePath
        self.knownPatches = KnownPatches(langHelper)
        self.langHelper = langHelper
        self.projectFolderPath = projectFolderPath
        
        conn = sqlite3.connect(self.dbFilePath)
        conn.row_factory = sqlite3.Row
        self.__findFileNavigationsInDb(conn)
        self.__findMethodsForFileNavigations(conn)
        self.__printNavigations()
        conn.close()
        
    def __findFileNavigationsInDb(self, conn):
        c = conn.cursor()
        c.execute(self.TEXT_SELECTION_OFFSET_QUERY)
        
        prevFilePath = None
        prevOffset = None
        
        for row in c:
            timestamp, filePath, offset = \
                str(iso8601.parse_date(row['timestamp'])), row['target'], int(row['referrer'])
            
            if prevFilePath != filePath or prevOffset != offset:
                if self.langHelper.hasCorrectExtension(filePath):
                    self.fileNavigations.append(FileNavigation(timestamp, filePath, offset))
                
            prevFilePath = filePath
            prevOffset = offset
        c.close()
        
    def __findMethodsForFileNavigations(self, conn):
        prevNavigation = None
        
        for toNavigation in self.fileNavigations:
            c = conn.execute(self.METHOD_DECLARATIONS_QUERY, [toNavigation.timestamp])
            for row in c:
                action, target, referrer = row['action'], row['target'], row['referrer']
                
                if action == 'Method declaration':
                    self.knownPatches.addFilePatch(referrer)
                elif action == 'Method declaration offset':
                    method = self.knownPatches.findMethodByFqn(target)
                    if method:
                        method.startOffset = int(referrer);
                elif action == 'Method declaration length':
                    method = self.knownPatches.findMethodByFqn(target)
                    if method:
                        method.length = int(referrer);
            
            toMethodPatch = self.knownPatches.findMethodByOffset(toNavigation.filePath, toNavigation.offset)
            fromNavigation = None
            fromMethodPatch = None
            
            if len(self.navigations) > 0:
                prevNavigation = self.navigations[-1]
                fromNavigation = prevNavigation.toFileNav.clone()
                fromMethodPatch = self.knownPatches.findMethodByOffset(fromNavigation.filePath, fromNavigation.offset)
            navigation = Navigation(fromNavigation, toNavigation.clone())
            
            if navigation.fromFileNav and fromMethodPatch:
                navigation.fromFileNav.methodFqn = fromMethodPatch.fqn
            if navigation.toFileNav and toMethodPatch:
                navigation.toFileNav.methodFqn = toMethodPatch.fqn
            
            if not navigation.isToSameMethod():
                self.__addPFIGFileHeadersIfNeeded(conn, prevNavigation, navigation)
                self.navigations.append(navigation)
        c.close()
        
    def __addPFIGFileHeadersIfNeeded(self, conn, prevNav, currNav):
        if not prevNav:
            return 
        
        if prevNav.isToUnknown() and currNav.isFromUnknown():
            if self.knownPatches.findMethodByOffset(currNav.fromFileNav.filePath, currNav.fromFileNav.offset) is None:
                if prevNav.toFileNav.filePath == currNav.fromFileNav.filePath and prevNav.toFileNav.offset == currNav.fromFileNav.offset:
                    print prevNav.toFileNav.toStr(), 'is being converted to header: '
                    header = PFIGFileHeader.addPFIGJavaFileHeader(conn, currNav, self.projectFolderPath, self.langHelper)
                    currNav.fromFileNav.methodFqn = header
                    print header
                    self.knownPatches.addFilePatch(header)
            
    
    def __printNavigations(self):
        for i in range(len(self.navigations)):
            navigation = self.navigations[i]
            print str(i), navigation.toStr()

class Navigation(object):
    def __init__(self, fromFileNav, toFileNav):
        self.fromFileNav = fromFileNav
        self.toFileNav = toFileNav
        
    def isToSameMethod(self):
        if self.fromFileNav and self.toFileNav:
            if self.fromFileNav.methodFqn and self.toFileNav.methodFqn:
                return self.fromFileNav.methodFqn == self.toFileNav.methodFqn
        return False
    
    def isFromUnknown(self):
        if self.fromFileNav and self.fromFileNav.methodFqn:
            return False
        return True
    
    def isToUnknown(self):
        if self.toFileNav and self.toFileNav.methodFqn:
            return False
        return True
    
    def clone(self):
        return Navigation(self.fromFileNav.clone(), self.toFileNav.clone())
        
    def toStr(self):
        fromLoc = None
        toLoc = None
        
        if self.fromFileNav:
            fromLoc = self.fromFileNav.toStr()
        if self.toFileNav:
            toLoc = self.toFileNav.toStr()
            
        return str(fromLoc) + ' --> ' + str(toLoc)
        
class FileNavigation(object):
    def __init__(self, timestamp, filePath, offset):
        self.timestamp = timestamp
        self.filePath = filePath;
        self.offset = offset
        self.methodFqn = None
        
    def clone(self):
        fileNavClone = FileNavigation(self.timestamp, self.filePath, self.offset)
        fileNavClone.methodFqn = self.methodFqn
        return fileNavClone
        
    def toStr(self):
        if self.methodFqn:
            return self.methodFqn
        return str(self.filePath) + ' at ' + str(self.offset)
        