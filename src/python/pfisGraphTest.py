from pfisGraph import PfisGraph
from languageHelperFactory import LanguageHelperFactory, Languages
import shutil
from navpath import NavigationPath
from algorithmRecency import Recency
import networkx as nx


def main():    
    db = '/Users/Dave/Desktop/code/p8l_debug.db'
    db_copy = '/Users/Dave/Desktop/code/p8l_debug_temp.db'
    copyDatabase(db, db_copy)
    
    langHelper = LanguageHelperFactory.getLanguageHelper(Languages.JAVA)
    projSrc = langHelper.fixSlashes('/Users/Dave/Desktop/code/p8l-vanillaMusic/src')
    stopWords = loadStopWords('/Users/Dave/Desktop/code/pfis3/data/je.txt')
    
    graph = PfisGraph(db_copy, langHelper, projSrc, stopWords = stopWords)
    graph.updateGraphByOneNavigation()
    graph.updateGraphByOneNavigation()
    graph.updateGraphByOneNavigation()
    graph.updateGraphByOneNavigation()
    graph.updateGraphByOneNavigation()
    
#     navPath = graph.getNavigationPath()
#     recency = Recency(navPath, langHelper)
#     for prediction in recency.getAllPredictions():
#         print prediction.getString()
    
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