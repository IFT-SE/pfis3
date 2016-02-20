import os

def main():
    outputDir = '/Users/Dave/Desktop/output'
    outputFileName = 'combinedModels.txt'
    mergedFileName = 'combined.txt'
    hitThreshold = 10
    
    confFolders = [os.path.join(outputDir, d) \
                   for d in os.listdir(outputDir) \
                   if os.path.isdir(os.path.join(outputDir, d))]


    for confFolder in confFolders:
        participantFolders = [os.path.join(confFolder, f) \
                              for f in os.listdir(confFolder) \
                              if os.path.isdir(os.path.join(confFolder, f))]
        for participantFolder in participantFolders:
            mergedFilePath = os.path.join(participantFolder, mergedFileName)
            
            if os.path.exists(mergedFilePath):
                outputFilePath = os.path.join(participantFolder, outputFileName)
                headers, mapData = combineModels(mergedFilePath)
                writeOutputFile(headers, mapData, outputFilePath, hitThreshold)
            else:
                print "Warning: Could not find: " + mergedFilePath
                
def writeOutputFile(headers, mapData, outputFilePath, hitThreshold):
    f = open(outputFilePath, 'w')
    numRows = len(mapData[headers[0]])
    numCols = len(headers)
    hitRates = ['','','','Hit rates =']
    
    for col in range(0, numCols):
        f.write(headers[col])
        hitRates.append(0.0)
        if col < numCols - 1:
            f.write('\t')
        else:
            f.write('\n')
    
    for row in range(0, numRows):
        for col in range(0, numCols):
            value = mapData[headers[col]][row]
            
            if col > 3 and float(value) <= hitThreshold:
                hitRates[col] += 1
            
            f.write(value)
            if col < numCols - 1:
                f.write('\t')
            else:
                f.write('\n')
    
    for i in range(4, len(headers)):
        hitRates[i] = hitRates[i] / numRows
        
    for col in range(0, numCols):
        f.write(str(hitRates[col]))
        if col < numCols - 1:
            f.write('\t')
    
    f.close()
            
def combineModels(mergedFilePath):
    headers, mapData = getData(mergedFilePath)
    
    # headers[4] onwards contains the models and their results
    
    if len(headers) < 2:
        raise RuntimeError("Error: Combined file has fewer than two models' results")
    
    singleModelHeaders = headers[5:]
    newModelHeaders = singleModelHeaders
    allHeaders = []
    
    for header in headers:
        allHeaders.append(header)
    
    for _ in range(0, len(singleModelHeaders) - 1):
        newModelHeaders = doCombinations(singleModelHeaders, newModelHeaders, mapData)
        for header in newModelHeaders:
            allHeaders.append(header)
            
    return allHeaders, mapData
    
def doCombinations(singleModelHeaders, multiModelHeaders, mapData):
    newModelHeaders = []
    
    for m1 in range(0, len(singleModelHeaders)):
        for m2 in range(0, len(multiModelHeaders)):
            m1Name = singleModelHeaders[m1]
            m2Name = multiModelHeaders[m2]
            
            if 'pfis' in m1Name or 'pfis' in m2Name: continue
            
            modelName = m1Name + '&' + m2Name
            nameTokens = m2Name.split('&')
            
            if m1Name in nameTokens: continue
            
            print 'Combining: ' + modelName
            newModelHeaders.append(modelName)
            m1Ranks = mapData[m1Name]
            m2Ranks = mapData[m2Name]
            mapData[modelName] = []
            
            for i in range(0, len(m1Ranks)):
                m1Rank = float(m1Ranks[i])
                m2Rank = float(m2Ranks[i])
                mapData[modelName].append(str(min(m1Rank, m2Rank)))
    
    return newModelHeaders
            
    
def getData(mergedFilePath):
    mapData = {}
    f = open(mergedFilePath, 'r')
    makeHeader = True
    headers = []
    
    for line in f:
        tokens = line.split('\t')
        if makeHeader:
            for token in tokens:
                mapData[token.strip()] = []
                headers.append(token.strip())
            makeHeader = False
        else:
            if tokens[0].strip() != '':
                for i in range(0, len(headers)):
                    mapData[headers[i]].append(tokens[i].strip())
    f.close()
    return headers, mapData


if __name__ == '__main__':
    main()