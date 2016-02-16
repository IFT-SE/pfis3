class PredictionEntry:
    def __init__(self, navNum, rank, length,
                 fromLoc, toLoc, classLoc, packageLoc, timestamp, predictions=[]):

        self.navNum = str(navNum)
        self.timestamp = str(timestamp)
        self.rank = str(rank)
        self.numTimes = str(len(predictions))
        self.length = str(length)
        self.fromLoc = fromLoc
        self.toLoc = toLoc
        self.classLoc = str(classLoc)
        self.packageLoc = str(packageLoc)
        self.predictions = predictions


    def __str__(self):
        return self.navNum + '\t' + self.timestamp + '\t' + self.rank + '\t' \
            + self.numTimes + '\t' + self.length + '\t' \
            + self.fromLoc + '\t' + self.toLoc + '\t' \
            + self.classLoc + '\t' + self.packageLoc + '\t' \
            + str(len(self.predictions)) + '\t' + str(self.predictions)

class Predictions:
    def __init__(self, filePath):
        self.filePath = filePath;
        self.entries = []

    def getHeaderString(self):
        return "Nav No"+ '\t' + "Timestamp" + '\t' + "Rank" + '\t' \
            + "Times" + '\t' + "Length" + '\t' \
            + "From loc" + '\t' + "To loc" + '\t'\
            + "Class loc" + '\t' + "Package loc" + "\t" +  \
             "No of ties" + "\t" + "Predictions" + "\n"

    def addEntry(self, logEntry):
        self.entries.append(logEntry);

    def saveLog(self):
        logFile = open(self.filePath, 'w');
        logFile.write(self.getHeaderString())
        for entry in self.entries:
            logFile.write(str(entry) + '\n');
        logFile.close();

