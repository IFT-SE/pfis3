import getopt
import os
import subprocess
import sys

def main():
    args = parseArgs()
    if args['mode'] == None:
        print 'Missing mode. Include -R(un) or -C(ombine) or -M(ulit-factor) -A(ll) in args.'
        sys.exit(2)
        
    if args['mode'] == '-R':
        if args["executable"] is None or args["dbDirPath"] is None \
            or args["stopWordsPath"] is None or args["language"] is None \
            or args["projectSrcFolderPath"] is None \
            or args["outputPath"] is None or args["xml"] is None:
            print 'Missing parameters for run mode.'
            sys.exit(2)
        runMode(args)
    if args['mode'] == '-C':
        if args["outputPath"] is None or args["combinedFileName"] is None \
            or args["hitRateThreshold"] is None or args['multiModelFileName'] is None:
            print 'Missing parameters for combine mode.'
            sys.exit(2)
        combineMode(args)
    if args['mode'] == '-M':
        if args["outputPath"] is None or args["combinedFileName"] is None \
            or args["hitRateThreshold"] is None or args['multiModelFileName'] is None:
            print 'Missing parameters for multi-factor model mode.'
            sys.exit(2)
        multiFactorModelMode(args)
    if args['mode'] == '-F':
        if args["outputPath"] is None or args["finalResultsFileName"] is None \
            or args['multiModelFileName'] is None:
            print 'Missing parameters for final results mode.'
            sys.exit(2)
        finalResultsMode(args)
    if args['mode'] == '-A':
        for key in args:
            if args[key] is None: 
                print 'Missing parameters for all mode.'
                sys.exit(2)
        runMode(args)
        combineMode(args)
        multiFactorModelMode(args)
        finalResultsMode(args)          
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
            
        combinedOutputFile.write('\t\t\tHit rates')
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
        hitRates = ['','','','Hit rates']
        
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
            
    def combineModels(combinedFilePath):
        headers, mapData = getData(combinedFilePath)
        
        # headers[4] onwards contains the models and their results
        
        if len(headers) < 2:
            raise RuntimeError("Error: Combined file has fewer than two models' results")
        
        singleModelHeaders = sorted(headers[4:])
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
                
                if 'pfis' in m1Name or 'pfis' in m2Name or m1Name in m2Name: 
                    continue
                
                modelName = ''
                nameTokens = m2Name.split('&')
                nameTokens.append(m1Name)
                sortedTokens = sorted(nameTokens)
                
                for token in sortedTokens:
                    modelName += token + '&'
                modelName = modelName[0:-1]
                
                if modelName in newModelHeaders:
                    continue
                
                newModelHeaders.append(modelName)
                m1Ranks = mapData[m1Name]
                m2Ranks = mapData[m2Name]
                mapData[modelName] = []
                
                for i in range(0, len(m1Ranks)):
                    m1Rank = float(m1Ranks[i])
                    m2Rank = float(m2Ranks[i])
                    mapData[modelName].append(str(min(m1Rank, m2Rank)))
        
        return newModelHeaders
                
        
    def getData(combinedFilePath):
        mapData = {}
        f = open(combinedFilePath, 'r')
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
    multiModelFileName = args['multiModelFileName']
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
            combinedFilePath = os.path.join(dbResultsFolder, combinedFileName)
            
            if os.path.exists(combinedFilePath):
                outputFilePath = os.path.join(dbResultsFolder, multiModelFileName)
                headers, mapData = combineModels(combinedFilePath)
                writeOutputFile(headers, mapData, outputFilePath, hitThreshold)
            else:
                print "Warning: Could not find: " + combinedFilePath
                
    print "runScript.py finished creating multi-factor models' results..."
    
def finalResultsMode(args):
    def getHeader(filePath):
        f = open(filePath, 'r')
        line = f.readline()
        
        # Models start in tokens[4]
        tokens = line.strip().split('\t')
        f.close()
        
        return tokens[4:]
    
    def getHitRates(filePath):
        hitRates = None
        f = open(filePath, 'r')
        
        for line in f:
            tokens = line.split('\t')
            if len(tokens) > 3 and tokens[3] == 'Hit rates':
                hitRates = tokens[4:]
                break
        
        f.close()
        
        return hitRates
    
    def writeResults(header, mapPathToHitRates, outputPath):
        f = open(outputPath, 'w')
        f.write('path')
        for item in header:
            f.write('\t' + item)    
        f.write('\n')
        
        for path in mapPathToHitRates:
            f.write(path)
            for hitRate in mapPathToHitRates[path]:
                f.write('\t' + hitRate)
            f.write('\n')
        
        f.close()
    
    print "runScript.py is creating final results..."
    
    outputDir = args['outputPath']
    finalResultsFileName = args['finalResultsFileName']
    multiModelFileName = args['multiModelFileName']
    outputFilePath = os.path.join(outputDir, finalResultsFileName)
    mapPathToHitRates = {}
    
    header = None
    subFolders = [os.path.join(outputDir, d) \
                   for d in os.listdir(outputDir) \
                   if os.path.isdir(os.path.join(outputDir, d))]

    for subFolder in subFolders:
        dbResultsFolders = [os.path.join(subFolder, f) \
                              for f in os.listdir(subFolder) \
                              if os.path.isdir(os.path.join(subFolder, f))]
        for dbResultsFolder in dbResultsFolders:
            print "Gathering hit rates from " + dbResultsFolder
            multiModelFilePath = os.path.join(dbResultsFolder, multiModelFileName)
            
            if os.path.exists(multiModelFilePath):
                if header is None:
                    header = getHeader(multiModelFilePath)
                    
                hitRates = getHitRates(multiModelFilePath)
                if hitRates is None:
                    print "Couldn't find hit rates in " + multiModelFilePath
                    sys.exit(2)
                    
                mapPathToHitRates[dbResultsFolder] = hitRates
            else:
                print "Warning: Could not find: " + multiModelFileName
    
    writeResults(header, mapPathToHitRates, outputFilePath)
    print "runScript.py finished creating final results..."
   
def print_usage():
    print "runScript has four modes:"
    print "-R allows a user to execute PFIS3 over a directory containing"
    print "SQLite3 PFIG databases. For each database, the pfis3.py script is run"
    print "and a folder containing the model results for each database is is"
    print "created in the output dir."
    print ""
    print "-C allows a user to combine the results generated after Run mode. It"
    print "will create a new file in each results folder that combines the ranks"
    print "of all the results text files in that folder. It will also calculate"
    print "hit rates for the given threshold. Results are saved in the results"
    print "directory."
    print ""
    print "-M allows a user to create optimal multi-factor models after Combine"
    print "mode. It will look for the combined results file in each results"
    print "folder and use it to find the ranks and hits rates of optimal model"
    print "combinations. Results are then saved in the same directory as each"
    print "combined results file found."
    print ""
    print "-F allows a user to create a final results file for each multi-factor"
    print "model results file. It must be run after Multi-factor mode. This takes"
    print "the hit rate data from each multi-factor model results file and places"
    print "it in the output directory."
    print ""
    print "-A is the same as:"
    print "    python runscript.py -R -C -M -F <required arguments>"
    print ""
    print "All results file names should end in '.txt'. PFIG databases are"
    print "assumed to end in '.db'"
    print "Usage:"
    print "python runScript.py -R(un), -C(ombine), -M(ulit-factor), -(F)inal or -A(ll):"
    print ""
    print "    if -R:"
    print "                    -e <path to pfis3.py>"
    print "                    -d <directory containing PFIG databases (*.db)>"
    print "                    -s <path to stop words file>"
    print "                    -l <language> "
    print "                    -p <path to project source folder>"
    print "                    -o <path to output folder> "
    print "                    -x <xml options file>"
    print "    (Note: language must be 'JAVA' or 'JS')"
    print "    if -C:"
    print "                    -o <path to output folder> "
    print "                    -c <name of combined results file (xxx.txt)>"
    print "                    -m <name of multi-factor model results file (yyy.txt)>"
    print "                    -h <hit rate threshold>"
    print "    if -M:"
    print "                    -o <path to output folder> "
    print "                    -m <name of multi-factor model results file (yyy.txt)>"
    print "                    -c <name of combined results file (xxx.txt)>"
    print "                    -h <hit rate threshold>"
    print "    if -F:"
    print "                    -o <path to output folder> "
    print "                    -f <name of the final results file (zzz.final)>"
    print "                    -m <name of multi-factor model results file (yyy.txt)>"
    print "    if -A:"
    print "                    all parameters required"

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
        "finalResultsFileName" : None,
        "mode" : None
    }

    def assign_argument_value(argsMap, option, value):
        if option == '-R' or option == '-C' or option == '-M' or option == '-F' or option =='-A':
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
            "-m" : "multiModelFileName",
            "-f" : "finalResultsFileName"
        }

        key = optionKeyMap[option]
        arguments[key] = value

    try:
        opts, _ = getopt.getopt(sys.argv[1:], "RCMFAe:d:s:l:p:o:x:c:h:m:f:")
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