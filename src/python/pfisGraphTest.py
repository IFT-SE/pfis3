from pfisGraph import PfisGraph
from languageHelperFactory import LanguageHelperFactory, Languages
import shutil
from algorithmRecency import Recency
from algorithmAdjacency import Adjacency
from algorithmPFIS import PFIS
from algorithmCallDepth import CallDepth
from algorithmSourceTopology import SourceTopology


def main():    
    db = '/Users/srutis90/Projects/VFT/Cryo2Pfig/output_d12_db'
    db_copy = '/Users/srutis90/Projects/VFT/Cryo2Pfig/output_d12_db_copy'
    copyDatabase(db, db_copy)
    
    langHelper = LanguageHelperFactory.getLanguageHelper(Languages.JS)
    projSrc = langHelper.fixSlashes('/Users/srutis90/Projects/VFT/Cryo2Pfig/jsparser/src')
    stopWords = loadStopWords('/Users/srutis90/Projects/VFT/Cryo2Pfig/PFIS/je.txt')

    pfisWithHistory = PFIS(langHelper, 'PFIS with history', history=True)
    pfisWithoutHistory = PFIS(langHelper, 'PFIS without history')
    pfisWithoutHistoryWithGoal = PFIS(langHelper, 'PFIS without history, with goal', goal = ['textarea', 'fold', 'delete', 'line'], stopWords=stopWords)
    adjacency = Adjacency(langHelper, 'Adjacency')
    recency = Recency(langHelper, 'Recency')
    callDepth = CallDepth(langHelper, 'Undirected Call Depth')
    sourceTopology = SourceTopology(langHelper, 'Source Topology')
    algorithms = [pfisWithHistory]
    # , pfisWithoutHistory, pfisWithoutHistoryWithGoal, adjacency, recency, callDepth, sourceTopology]
    
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