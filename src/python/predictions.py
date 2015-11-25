class PredictionEntry:
    def __init__(self, navNum, timestamp, rank, numTies, length,
                 fromLoc, toLoc, classLoc, packageLoc):
        self.navNum = str(navNum)
        self.timestamp = str(timestamp)
        self.rank = str(rank)
        self.numTimes = str(numTies)
        self.length = str(length)
        self.fromLoc = fromLoc
        self.classLoc = str(classLoc)
        self.packageLoc = str(packageLoc)

    def getString(self):
        return self.navNum + '\t' + self.timestamp + '\t' + self.rank + '\t' \
            + self.numTimes + '\t' + self.length + '\t' + self.fromLoc + '\t' \
            + self.classLoc + '\t' + self.packageLoc

class Predictions:
    def __init__(self, filePath):
        self.filePath = filePath;
        self.entries = []

    def addEntry(self, logEntry):
        self.entries.append(logEntry);

    def saveLog(self):
        logFile = open(self.filePath, 'w');
        for entry in self.entries:
            logFile.write(entry.getString() + '\n');
        logFile.close();

