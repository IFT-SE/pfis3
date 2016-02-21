import getopt
import os
import subprocess
import sys

def main():
    args = parseArgs()
    if args['mode'] == None:
        print 'Missing mode. Include -R(un) or -C(ombine) or -M(ulit-factor) -A(ll) in args.'
        sys.exit(2)
        
    elif args['mode'] == '-R':
        if args["executable"] is None or args["dbDirPath"] is None \
            or args["stopWordsPath"] is None or args["language"] is None \
            or args["projectSrcFolderPath"] is None \
            or args["outputPath"] is None or args["xml"] is None:
            print 'Missing parameters for run mode.'
            sys.exit(2)
        runMode(args)
    elif args['mode'] == '-C':
        if args["outputPath"] is None or args["combinedFileName"] is None \
            or args["hitRateThreshold"] is None or args['multiModelFileName'] is None:
            print 'Missing parameters for combine mode.'
            sys.exit(2)
        combineMode(args)
    elif args['mode'] == '-M':
        if args["outputPath"] is None or args["combinedFileName"] is None \
            or args["hitRateThreshold"] is None or args['multiModelFileName'] is None:
            print 'Missing parameters for multi-factor model mode.'
            sys.exit(2)
        multiFactorModelMode(args)
    elif args['mode'] == '-A':
        for key in args:
            if args[key] is None: 
                print 'Missing parameters for all mode.'
                sys.exit(2)
        runMode(args)
        combineMode(args)
        multiFactorModelMode(args)            
    sys.exit(0)

def runMode(args):
    print "runScript.py is running models..."

    d = args['dbDirPath']
    p = args['projectSrcFolderPath']
    l = args['language']
    s = args['stopWordsPath']
    o = args['outputPath']
    x = args['xml']
    
    db_fileNames = [f for f in os.listdir(d) if os.path.isfile(os.path.join(d, f)) and f.endswith('.db')]
    # Make the output subdirectory
    dbDirName = os.path.basename(os.path.normpath(d))
    subDir = os.path.join(o, d)
    if not os.path.exists(subDir):
        os.makedirs(subDir)
    
    for db in db_fileNames:
        
        name = db[0:db.index('.')]
        dbPath = os.path.join(d, db)
        dbOutputPath = os.path.join(o, dbDirName, name)
        if not os.path.exists(dbOutputPath):
            os.makedirs(dbOutputPath)
        
        print "Running data for " + dbPath + '...'
        
        subprocess.call(['python',
                        '/Users/Dave/Desktop/code/pfis3/src/python/pfis3.py', \
                        '-d', dbPath, \
                        '-p', p, \
                        '-l', l, \
                        '-s', s, \
                        '-o', dbOutputPath, \
                        '-x', x])
        
    print "runScript.py finished running models."
        
def combineMode(args):
    def combineResultsFiles(outputFiles, participantFolder, outputFileName, hitRateThreshold):
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
                    if float(tokens[2]) <= hitRateThreshold:
                        numHits[index] += 1
                index +=1
            combinedOutputFile.write('\n')
            
        combinedOutputFile.write('\t\t\tHit Rates:')
        for n in numHits:
            combinedOutputFile.write('\t' + str(float(n) / (numLines - 1)))
            
        combinedOutputFile.write('\n')
        
        for handler in fileHandlers:
            handler.close()
            
    print "runScript.py is combining models' results..."
    
    outputDir = args['outputPath']
    outputFileName = args['combinedFileName']
    hitRateThreshold = float(args['hitRateThreshold'])
    multiModelFileName = args['multiModelFileName']
    
    subFolders = [os.path.join(outputDir, d) \
                   for d in os.listdir(outputDir) \
                   if os.path.isdir(os.path.join(outputDir, d))]


    for subFolder in subFolders:
        dbResultsFolders = [os.path.join(subFolder, f) \
                              for f in os.listdir(subFolder) \
                              if os.path.isdir(os.path.join(subFolder, f))]
        for dbResultsFolder in dbResultsFolders:
            outputFiles = [os.path.join(dbResultsFolder, f) \
                              for f in os.listdir(dbResultsFolder) \
                              if os.path.isfile(os.path.join(dbResultsFolder, f))
                              and f.endswith('.txt') \
                              and not f.endswith(multiModelFileName) \
                              and not f.endswith(outputFileName)]
            if len(outputFiles) > 0:
                print "Combining results in " + dbResultsFolder
                combineResultsFiles(outputFiles, dbResultsFolder, outputFileName, hitRateThreshold)
            else:
                print "Warning: No model results found in " + dbResultsFolder
    print "runScript.py finished combining models' results."
        
def multiFactorModelMode(args):
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
    
    print "runScript.py is creating multi-factor models' results..."
    
    outputDir = args['outputPath']
    outputFileName = args['multiModelFileName']
    combinedFileName = args['combinedFileName']
    hitThreshold = float(args['hitRateThreshold'])
    
    subFolders = [os.path.join(outputDir, d) \
                   for d in os.listdir(outputDir) \
                   if os.path.isdir(os.path.join(outputDir, d))]


    for subFolder in subFolders:
        dbResultsFolders = [os.path.join(subFolder, f) \
                              for f in os.listdir(subFolder) \
                              if os.path.isdir(os.path.join(subFolder, f))]
        for dbResultsFolder in dbResultsFolders:
            print "Creating multi-factor model results in " + dbResultsFolder
            mergedFilePath = os.path.join(dbResultsFolder, combinedFileName)
            
            if os.path.exists(mergedFilePath):
                outputFilePath = os.path.join(dbResultsFolder, outputFileName)
                headers, mapData = combineModels(mergedFilePath)
                writeOutputFile(headers, mapData, outputFilePath, hitThreshold)
            else:
                print "Warning: Could not find: " + mergedFilePath
                
    print "runScript.py finished creating multi-factor models' results..."
   
def print_usage():
    print "runScript allows a user to execute PFIS3 over a directory containing"
    print "SQLite3 PFIG databases. For each database, the pfis3.py script is run"
    print "and a folder containing the model results for each database is is"
    print "created in the output dir. After results have been created, this script"
    print "also allows the user to combine those results in a single file in each"
    print "of the database results' directories and also create optimal multi-"
    print "factor model results."
    print ""
    print "Usage:"
    print "python runScript.py -R(un) or -C(ombine) or -M(ulit-factor) or -A(ll):"
    print ""
    print "    if -R:"
    print "                    -e <path to pfis3.py>"
    print "                    -d <directory containing PFIG databases (*.db)>"
    print "                    -s <path to stop words file>"
    print "                    -l <language> "
    print "                    -p <path to project source folder>"
    print "                    -o <path to output folder> "
    print "                    -x <xml options file>"
    print "    if -C:"
    print "                    -o <path to output folder> "
    print "                    -c <name of combined results file>"
    print "                    -m <name of multi-factor model results file>"
    print "                    -h <hit rate threshold>"
    print "    if -M:"
    print "                    -o <path to output folder> "
    print "                    -c <name of combined results file>"
    print "                    -m <name of multi-factor model results file>"
    print "                    -h <hit rate threshold>"
    print "    if -A:          all parameters required"
    print "for language : say JAVA or JS"

def parseArgs():

    arguments = {
        "executable" : None,
        "dbDirPath" : None,
        "stopWordsPath" : None,
        "language": None,
        "projectSrcFolderPath": None,
        "outputPath" : None,
        "xml" : None,
        "combinedFileName" : None,
        "hitRateThreshold" : None,
        "multiModelFileName" : None,
        "mode" : None
    }

    def assign_argument_value(argsMap, option, value):
        if option == '-R' or option == '-C' or option == '-M' or option =='-A':
            arguments['mode'] = option
            return
        
        optionKeyMap = {
            "-e" : "executable",
            "-d" : "dbDirPath",
            "-s" : "stopWordsPath",
            "-l" : "language",
            "-p" : "projectSrcFolderPath",
            "-o" : "outputPath",
            "-x" : "xml",
            "-c" : "combinedFileName",
            "-h" : "hitRateThreshold",
            "-m" : "multiModelFileName"
        }

        key = optionKeyMap[option]
        arguments[key] = value

    try:
        opts, _ = getopt.getopt(sys.argv[1:], "RCMe:d:s:l:p:o:x:c:h:m:")
    except getopt.GetoptError as err:
        print str(err)
        print("Invalid args passed to runScript.py")
        print_usage()
        sys.exit(2)
    for option, value in opts:
        assign_argument_value(arguments, option, value)

    return arguments


if __name__ == '__main__':
    main()