class PredictionEntry:
    def __init__(self, navNum, rank, old_rank, old_numTies, length, old_length,
                 fromLoc, toLoc, classLoc, packageLoc, timestamp, predictions=[]):

        def formatOld(o):
            return " (" + str(o) + ")"

        self.navNum = str(navNum)
        self.timestamp = str(timestamp)
        self.rank = str(rank) + formatOld(old_rank)
        self.numTimes = str(len(predictions)) + formatOld(old_numTies)
        self.length = str(length) + formatOld(old_length)
        self.fromLoc = fromLoc
        self.toLoc = toLoc
        self.classLoc = str(classLoc)
        self.packageLoc = str(packageLoc)
        self.predictions = predictions



    def getString(self):
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
            + "From loc" + "To loc" + '\t'\
            + "Class loc" + '\t' + "Package loc" + "\t" +  \
             "No of ties" + "\t" + "Predictions" + "\n"

    def addEntry(self, logEntry):
        self.entries.append(logEntry);

    def saveLog(self):
        logFile = open(self.filePath, 'w');
        logFile.write(self.getHeaderString())
        for entry in self.entries:
            logFile.write(entry.getString() + '\n');
        logFile.close();

