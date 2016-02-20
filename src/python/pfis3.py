import sys
import os
import shutil
import getopt

from languageHelperFactory import LanguageHelperFactory
from algorithmPFIS import PFIS
from algorithmPFISTouchOnce import PFISTouchOnce
from algorithmAdjacency import Adjacency
from algorithmFrequency import Frequency
from algorithmRecency import Recency
from algorithmWorkingSet import WorkingSet
from algorithmCallDepth import CallDepth
from algorithmSourceTopology import SourceTopology
from pfisGraph import PfisGraph
from algorithmTFIDF import TFIDF

def print_usage():
    print "python pfis3.py -d <path to PFIG database> -s <path to stop words file>"
    print "                -l <language> -p <path to project source folder> "
    print "                -o <path to output folder>"
    print "for language : say JAVA or JS"

def parseArgs():

    arguments = {
        "outputPath" : None,
        "stopWordsPath" : True,
        "tempDbPath" : None,
        "dbPath" : None,
        "projectSrcFolderPath": None,
        "language": None
    }

    def assign_argument_value(argsMap, option, value):
        optionKeyMap = {
            "-s" : "stopWordsPath",
            "-d" : "dbPath",
            "-l" : "language",
            "-p" : "projectSrcFolderPath",
            "-o" : "outputPath"
        }

        key = optionKeyMap[option]
        arguments[key] = value

    def setConventionBasedArguments(argsMap):
        argsMap["tempDbPath"] = argsMap["dbPath"] + "_temp"

    try:
        opts, _ = getopt.getopt(sys.argv[1:], "d:s:l:p:o:")
    except getopt.GetoptError as err:
        print str(err)
        print("Invalid args passed to PFIS")
        print_usage()
        sys.exit(2)
    for option, value in opts:
        assign_argument_value(arguments, option, value)

    #TODO: currently, these are conventions, to avoid too many configurations. needs review.
    setConventionBasedArguments(arguments)

    return arguments

def main():

    args = parseArgs()

    #Initialize the processor with the appropriate language specific processor
    langHelper = LanguageHelperFactory.getLanguageHelper(args['language'])

    # Start by making a working copy of the database
    copyDatabase(args['dbPath'], args['tempDbPath'])
   
    #TODO: Specify this filename in a config file
    if (os.path.exists(args['outputPath'] + '/all.txt')):
        os.remove(args['outputPath'] + '/all.txt')
   
    # Initialize the predictive algorithms.
    # TODO: Replace these with a config file whose path is given as an argument
    # on the command line
    pfisWithHistory = PFIS(langHelper, 'PFIS with history, spread 2', 'pfis_history_spread2.txt', history = True)
    pfisWithoutHistory = PFIS(langHelper, 'PFIS without history, spread 2', 'pfis_no_history_spread2.txt')
    pfisConvergenceWithHistory = PFIS(langHelper, 'PFIS with history, spread 100', 'pfis_history_spread100.txt', history = True, numSpread = 100)
    pfisConvergenceWithoutHistory = PFIS(langHelper, 'PFIS without history, spread 100', 'pfis_no_history_spread100.txt', numSpread = 100)
    pfisTouchOnceWithHistory = PFISTouchOnce(langHelper, 'PFIS touch once with history', 'pfis_touch_once_with_history.txt', history = True)
    pfisTouchOnceWithoutHistory = PFISTouchOnce(langHelper, 'PFIS touch once no history', 'pfis_touch_once_no_history.txt')
    adjacency = Adjacency(langHelper, 'Adjacency', 'adjacency.txt')
    recency = Recency(langHelper, 'Recency', 'recency.txt')
    workingSet = WorkingSet(langHelper, 'Working Set', 'working_set10.txt')
    frequency = Frequency(langHelper, 'Frequency', 'frequency.txt')    
    callDepth = CallDepth(langHelper, 'Undirected Call Depth', 'undirected_call_depth.txt')
    sourceTopology = SourceTopology(langHelper, 'Source Topology', 'source_topology.txt')
    tfidf = TFIDF(langHelper, 'TF-IDF', 'tfidf.txt', args['tempDbPath'])
#     algorithms = [pfisTouchOnceWithHistory, pfisTouchOnceWithoutHistory, frequency, adjacency, recency, callDepth, sourceTopology]
#     algorithms = [pfisWithHistory, pfisWithoutHistory, pfisConvergenceWithHistory, pfisConvergenceWithoutHistory]
#     algorithms = [workingSet, pfisTouchOnceWithHistory, pfisTouchOnceWithoutHistory, pfisWithHistory, pfisWithoutHistory]
    algorithms = [tfidf]
        
    stopWords = loadStopWords(args['stopWordsPath'])
    graph = PfisGraph(args['tempDbPath'], langHelper, args['projectSrcFolderPath'], stopWords = stopWords)
    results = graph.makeAllPredictions(algorithms, args['outputPath'])
    savePredictionsToFiles(results)
#     __saveAlgorithmRanksToOneFile(results, '/Users/Dave/Desktop/combined.txt')
    sys.exit(0)
    
def savePredictionsToFiles(results):
    for algorithm in results:
        results[algorithm].saveToFile()
        
def __saveAlgorithmRanksToOneFile(results, filePath):
    f = open(filePath, 'w')
    algorithmNames = []
    
    for algorithmName in results:
        algorithmNames.append(algorithmName)
    
    f.write('Prediction' + '\t')
    for name in algorithmNames:
        f.write(name + '\t')
        
    f.write('From loc' + '\t' + 'To loc' + '\n')
    listOfPredictions = results[algorithmNames[0]].entries
    
    for i in range(0, len(listOfPredictions)):
        f.write(str(i + 1) + '\t')
        for name in algorithmNames:
            f.write(str(results[name].entries[i].rank) + '\t')
            
        f.write(listOfPredictions[i].fromLoc + '\t' + listOfPredictions[i].toLoc + '\n')
    f.close()

def loadStopWords(path):
    # Load the stop words from a file. The file is expected to have one stop
    # word per line. Stop words are ignored and not loaded into the PFIS graph.
    words = []
    f = open(path)
    for word in f:
        words.append(word.lower().strip())
    return words

def copyDatabase(dbpath, newdbpath):
    print "Making a working copy of the database..."
    shutil.copyfile(dbpath, newdbpath)
    print "Done."

if __name__ == "__main__":
    main()
