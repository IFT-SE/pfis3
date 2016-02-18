import sys
import shutil
import getopt

from languageHelperFactory import LanguageHelperFactory
from algorithmPFIS import PFIS
from algorithmPFISTouchOnce import PFISTouchOnce
from algorithmAdjacency import Adjacency
from algorithmFrequency import Frequency
from algorithmRecency import Recency
from algorithmCallDepth import CallDepth
from algorithmSourceTopology import SourceTopology
from pfisGraph import PfisGraph

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
    
    # Initialize the predictive algorithms.
    # TODO: Replace these with a config file whose path is given as an argument
    # on the command line
    pfisWithHistory = PFIS(langHelper, 'PFIS with history', 'pfis_history.txt', history=True)
    pfisWithoutHistory = PFIS(langHelper, 'PFIS without history', 'pfis_no_history.txt')
    pfisTouchOnceWithHistory = PFISTouchOnce(langHelper, 'PFIS touch once with history', 'pfis_touch_once_with_history.txt')
    pfisTouchOnceWithoutHistory = PFISTouchOnce(langHelper, 'PFIS touch once no history', 'pfis_touch_once_no_history.txt')
    adjacency = Adjacency(langHelper, 'Adjacency', 'adjacency.txt')
    recency = Recency(langHelper, 'Recency', 'recency.txt')
    frequency = Frequency(langHelper, 'Frequency', 'frequency.txt')    
    callDepth = CallDepth(langHelper, 'Undirected Call Depth', 'undirected_call_depth.txt')
    sourceTopology = SourceTopology(langHelper, 'Source Topology', 'source_topology.txt')
    algorithms = [pfisWithHistory, pfisWithoutHistory, pfisTouchOnceWithHistory, pfisTouchOnceWithoutHistory, frequency, adjacency, recency, callDepth, sourceTopology]
#     algorithms = [pfisTouchOnceWithHistory, pfisTouchOnceWithoutHistory]

    stopWords = loadStopWords(args['stopWordsPath'])

    graph = PfisGraph(args['tempDbPath'], langHelper, args['projectSrcFolderPath'], stopWords = stopWords)
    results = graph.makeAllPredictions(algorithms, args['outputPath'])
    savePredictionsToFiles(results)
    sys.exit(0)
    
def savePredictionsToFiles(results):
    for algorithm in results:
        results[algorithm].saveToFile()

def loadStopWords(path):
    # Load the stop words from a file. The file is expected to have one stop
    # word per line. Stop words are ignored and not loaded into the PFIS graph.
    words = []
    f = open(path)
    for word in f:
        words.append(word.lower())
    return words

def copyDatabase(dbpath, newdbpath):
    print "Making a working copy of the database..."
    shutil.copyfile(dbpath, newdbpath)
    print "Done."

if __name__ == "__main__":
    main()
