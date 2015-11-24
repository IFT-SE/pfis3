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

        if method.startswith("UNKNOWN"):
            self.unknownMethod = True;
