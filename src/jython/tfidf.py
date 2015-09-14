#!/usr/bin/env jython
import sys
import os

def setClassPath():
    sys.path.append("lib/TFIDF.jar")
    
def readIndex(docsPath, file):
    rv = {}

    idx = open(docsPath + file, 'r')
    for line in idx:
        filepath, method = line.rstrip('\n').split('\t')
        agent, filename = filepath.split('/')
        if not agent in rv:
            rv[agent] = {}
        rv[agent][docsPath + agent + '/' + filename] = method
    return rv
    
def query(docsPath, text, agent):
    # Original java method header
    #    public TFIDFIndex(String pathToSomeDirectoryOfFiles, String filenameEnding,
    #        boolean recurse) throws Exception
    import TFIDFIndex
    tfidf = TFIDFIndex(docsPath + agent, ".txt", 0)
    return tfidf.query(text)
    
def resultsSorter (x,y):
    return x.goodnessOfMatch < y.goodnessOfMatch
    
def getTopHit(qrList, ftm):
    #print "Rank 1:", ftm[qrList[0].fileIdentifier], qrList[0].goodnessOfMatch
    #print "Rank 2:", ftm[qrList[1].fileIdentifier], qrList[1].goodnessOfMatch
    #print "Rank 3:", ftm[qrList[2].fileIdentifier], qrList[2].goodnessOfMatch
    #print "Rank 4:", ftm[qrList[3].fileIdentifier], qrList[3].goodnessOfMatch
    return  ftm[qrList[0].fileIdentifier], qrList[0].goodnessOfMatch
    
def writeResults(qrList, path, ftm, agent):
    f = open(path, 'w')
    for result in qrList:
        f.write(agent + '\t' + ftm[agent][result.fileIdentifier] + '\t' + str(result.goodnessOfMatch) + '\n')
    f.close

def main():
    if len(sys.argv) == 2:
        docsPath = os.path.abspath(sys.argv[1])
        
        if docsPath[-1] != '/':
            docsPath += '/'
        setClassPath()
        fileToMethod = readIndex(docsPath, "index.idx")
        
        for agent in fileToMethod:
        
            queryResultsList = query(docsPath, '''BUG: Problem with character-offset counter.
In the lower left corner of the jEdit window, there are two counters that describe the position of the text cursor. The first counter gives the number of the line that cursor is on. The second counter gives the character offset into the line.
The character-offset counter is broken. When the cursor is at the beginning of a line (i.e., before the first character in the line), jEdit shows the offset as 1. However, the offset should begin counting from 0. Thus, when the cursor is at the end of the line, it will display the number of characters in the line rather than the number of characters plus 1.''', agent)
            queryResultsList = sorted(queryResultsList, resultsSorter)
            writeResults(queryResultsList, docsPath + agent + "/list.ranks", fileToMethod, agent)
    else:
        print "\tUsage: jython tfidf.py <path to root of documents directory>"
        
    sys.exit(0)

if __name__ == "__main__":
    main()
