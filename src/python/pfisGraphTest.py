from pfisGraph import PfisGraph
from languageHelperFactory import LanguageHelperFactory, Languages
import shutil
from algorithmRecency import Recency
from algorithmAdjacency import Adjacency
from algorithmPFIS import PFIS
from algorithmCallDepth import CallDepth
from algorithmSourceTopology import SourceTopology
from algorithmFrequency import Frequency


def main():    
    db = '/Users/Dave/Desktop/code/icsme16/p8l_debug.db'
    db_copy = '/Users/Dave/Desktop/code/PFIG_temp.db'
    copyDatabase(db, db_copy)
    
    langHelper = LanguageHelperFactory.getLanguageHelper(Languages.JAVA)
    projSrc = langHelper.fixSlashes('/Users/Dave/Desktop/code/p8l-vanillaMusic/src')
#     projSrc = langHelper.fixSlashes('/Users/Dave/Documents/workspace/jEdit-2548764/src')
    stopWords = loadStopWords('/Users/Dave/Desktop/code/pfis3/data/je.txt')
    
    pfisWithHistory = PFIS(langHelper, 'PFIS with history', history=True)
    pfisWithoutHistory = PFIS(langHelper, 'PFIS without history')
    pfisWithoutHistoryWithGoal = PFIS(langHelper, 'PFIS without history, with goal', goal = ['textarea', 'fold', 'delete', 'line'], stopWords=stopWords)
    adjacency = Adjacency(langHelper, 'Adjacency')
    frequency = Frequency(langHelper, 'Frequency')
    recency = Recency(langHelper, 'Recency')
    callDepth = CallDepth(langHelper, 'Undirected Call Depth')
    sourceTopology = SourceTopology(langHelper, 'Source Topology')
#     algorithms = [pfisWithHistory, pfisWithoutHistory, adjacency, recency, callDepth, sourceTopology]
    algorithms = [adjacency]
    
    graph = PfisGraph(db_copy, langHelper, projSrc, stopWords = stopWords)
    results = graph.makeAllPredictions(algorithms)
    
    for algorithm in algorithms:
        print '=========='
        print 'Results for ' + algorithm.name
        for prediction in results[algorithm.name]:
            print str(prediction)
        print '=========='
    
def copyDatabase(dbpath, newdbpath):
    print "Making a working copy of the database..."
    shutil.copyfile(dbpath, newdbpath)
    print "Done."
    
def loadStopWords(path):
    # Load the stop words from a file. The file is expected to have one stop
    # word per line. Stop words are ignored and not loaded into the PFIS graph.
    words = []
    f = open(path)
    for word in f:
        words.append(word.lower())
    return words


if __name__ == '__main__':
    main()