from pfisGraph import PfisGraph
from languageHelperFactory import LanguageHelperFactory, Languages
import shutil


def main():
    db = 'C:\Users\Dave\Desktop\p1f_debug.db'
    db_copy = 'C:\Users\Dave\Desktop\p8l_debug_copy.db'
    copyDatabase(db, db_copy)
    
    langHelper = LanguageHelperFactory.getLanguageHelper(Languages.JAVA)
    projSrc = langHelper.fixSlashes('C:\Users\Dave\Desktop\p8l-vanillaMusic\src')
    stopWords = loadStopWords('C:\Users\Dave\Desktop\pfis3\data\je.txt')
    
    graph = PfisGraph(db_copy, langHelper, projSrc, stopWords = stopWords, verbose=True)
    
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