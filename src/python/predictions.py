class Prediction:
    def __init__(self, navNum, rank, length, numTies, fromLoc, toLoc, timestamp):

        self.navNum = str(navNum)
        self.rank = str(rank)
        self.length = str(length)
        self.numTies = str(numTies)
        self.fromLoc = fromLoc
        self.toLoc = toLoc
        self.timestamp = str(timestamp)

    def __str__(self):
        return self.navNum + '\t' + self.timestamp + '\t' + self.rank + '\t' \
            + self.length + '\t' + self.numTies + '\t' \
            + self.fromLoc + '\t' + self.toLoc

class Predictions:
    def __init__(self, filePath):
        self.filePath = filePath;
        self.entries = []

    def getHeaderString(self):
        return "Prediction"+ '\t' + "Timestamp" + '\t' + "Rank" + '\t' \
            + "Out of" + '\t' + "No. of Ties" + '\t' \
            + "From loc" + '\t' + "To loc"

    def addPrediction(self, logEntry):
        self.entries.append(logEntry);

    def saveToFile(self):
        print 'Saving results to ' + self.filePath + '...'
        logFile = open(self.filePath, 'w');
        logFile.write(self.getHeaderString())
        for entry in self.entries:
            logFile.write(str(entry) + '\n');
        logFile.close();
        print 'Done.'

