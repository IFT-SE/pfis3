import os

def main():
    outputDir = '/Users/Dave/Desktop/output'
    outputFileName = 'combined.txt'
    
    confFolders = [os.path.join(outputDir, d) \
                   for d in os.listdir(outputDir) \
                   if os.path.isdir(os.path.join(outputDir, d))]


    for confFolder in confFolders:
        participantFolders = [os.path.join(confFolder, f) \
                              for f in os.listdir(confFolder) \
                              if os.path.isdir(os.path.join(confFolder, f))]
        for participantFolder in participantFolders:
            outputFiles = [os.path.join(participantFolder, f) \
                              for f in os.listdir(participantFolder) \
                              if os.path.isfile(os.path.join(participantFolder, f))
                              and f.endswith('.txt') \
                              and not f.endswith('all.txt') \
                              and not f.endswith(outputFileName)]
            mergeResults(outputFiles, participantFolder, outputFileName)
        
def mergeResults(outputFiles, participantFolder, outputFileName):
    combinedOutputFile = open(os.path.join(participantFolder, outputFileName), 'w')
    combinedOutputFile.write('Prediction\tTimestamp\tFrom loc\tTo loc')

    # open one file and check the number of lines and get non rank data
    dataRows = []
    f = open(outputFiles[0])
    numLines = 0
    for line in f: 
            numLines += 1
            tokens = line.split('\t')
            dataRows.append([tokens[0], tokens[1], tokens[5], tokens[6]])
    f.close()
    
    fileHandlers = []
    numHits = []
    for outputFile in outputFiles:
        f = open(outputFile, 'r')
        f.readline()
        fileHandlers.append(f)
        numHits.append(0)
        combinedOutputFile.write('\t' + outputFile[(outputFile.rfind(os.sep) + 1):outputFile.rfind('.')])
        
    combinedOutputFile.write('\n')
    
    for i in range(1, numLines):
        combinedOutputFile.write(dataRows[i][0] + '\t' + dataRows[i][1] + '\t' + dataRows[i][2] + '\t' + dataRows[i][3])
        index = 0
        for handler in fileHandlers:
            line = handler.readline()
            tokens = line.split('\t')
            if len(tokens) > 2:
                combinedOutputFile.write('\t' + tokens[2])
                if float(tokens[2]) <= 10:
                    numHits[index] += 1
            index +=1
        combinedOutputFile.write('\n')
        
    combinedOutputFile.write('\t\t\tHit Rates:')
    for n in numHits:
        combinedOutputFile.write('\t' + str(float(n) / (numLines - 1)))
        
    combinedOutputFile.write('\n')
    
    for handler in fileHandlers:
        handler.close()
    

if __name__ == '__main__':
    main()
