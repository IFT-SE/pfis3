import os

class Prediction:
    def __init__(self, navNum, rank, length, numTies, fromLoc, toLoc, timestamp, topPredictions=[]):

        self.navNum = str(navNum)
        self.rank = str(rank)
        self.length = str(length)
        self.numTies = str(numTies)
        self.fromLoc = fromLoc
        self.toLoc = toLoc
        self.timestamp = str(timestamp)
        self.topPredictions = topPredictions

    def __str__(self):
        return self.navNum + '\t' + self.timestamp + '\t' + self.rank + '\t' \
            + self.length + '\t' + self.numTies + '\t' \
            + self.fromLoc + '\t' + self.toLoc

    def getTopPredictionString(self, topPrediction):
        return self.navNum + "\t"+ self.timestamp + "\t" +\
            self.fromLoc + "\t" + self.toLoc + "\t" + \
            str(topPrediction[0]) + "\t" + str(topPrediction[1])

class Predictions:
    def __init__(self, algName, outputFolder, fileName, includeTop=False, topPredictionsFolder = None):
        self.algName = algName
        self.entries = []

        self.outputFolder = outputFolder
        self.filePath = os.path.join(outputFolder, fileName)

        self.includeTop = includeTop
        self.topPredictionsFileName = None

        if self.includeTop:
            self.topPredictionsFileName = os.path.join(topPredictionsFolder, fileName)

    def getPredictionsFileHeader(self):
        return "Prediction"+ '\t' + "Timestamp" + '\t' + self.algName + " Rank" + "\t" \
            + "Out of" + '\t' + "No. of Ties" + '\t' \
            + "From loc" + '\t' + "To loc"

    def getTopNPredictionsFileHeader(self):
        return "NavNum" + "\t"+ "Timestamp" + "\t"\
            + "From" + "\t" + "To" + "\t" \
            + "Rank" + "\t" + "Prediction"

    def addPrediction(self, logEntry):
        self.entries.append(logEntry)

    def saveToFile(self):
        print 'Saving results to ' + self.filePath + '...'
        
        logFile = open(self.filePath, 'w')
        logFile.write(self.getPredictionsFileHeader() + "\n")

        for entry in self.entries:
            logFile.write(str(entry) + '\n')
        logFile.close()


        if self.includeTop:
            print "Writing top results to: ", self.topPredictionsFileName

            topPredictionsFile = open(self.topPredictionsFileName, 'w')
            topPredictionsFile.write(self.getTopNPredictionsFileHeader() + "\n")

            for entry in self.entries:
                for topPrediction in entry.topPredictions:
                    topPredictionsFile.write(entry.getTopPredictionString(topPrediction) + "\n")

            topPredictionsFile.close()


        print 'Done.'
