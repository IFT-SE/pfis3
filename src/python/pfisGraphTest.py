from pfisGraph import PfisGraph
from languageHelperFactory import LanguageHelperFactory, Languages
import shutil
from algorithmRecency import Recency
from algorithmAdjacency import Adjacency
from algorithmPFIS import PFIS


def main():    
    db = '/Users/Dave/Desktop/code/icsme16/p8l_debug.db'
    db_copy = '/Users/Dave/Desktop/code/PFIG_temp.db'
    copyDatabase(db, db_copy)
    
    langHelper = LanguageHelperFactory.getLanguageHelper(Languages.JAVA)
    projSrc = langHelper.fixSlashes('/Users/Dave/Desktop/code/p8l-vanillaMusic/src')
#     projSrc = langHelper.fixSlashes('/Users/Dave/Documents/workspace/jEdit-2548764/src')
    stopWords = loadStopWords('/Users/Dave/Desktop/code/pfis3/data/je.txt')
    
    pfis = PFIS(langHelper)
    
    graph = PfisGraph(db_copy, langHelper, projSrc, stopWords = stopWords)
    graph.updateGraphByOneNavigation()
    graph.makePrediction(pfis)
    graph.updateGraphByOneNavigation()
    graph.makePrediction(pfis)
    graph.updateGraphByOneNavigation()
    graph.makePrediction(pfis)
    graph.updateGraphByOneNavigation()
    graph.makePrediction(pfis)
#     prediction = graph.makePrediction(Adjacency(langHelper))
#     print str(prediction)
#     prediction = graph.makePrediction(Recency(langHelper))
#     print str(prediction)
    
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