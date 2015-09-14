#!/usr/bin/env jython
import sys
import os
import copy

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
    if len(sys.argv) == 3:
        docsPath = os.path.abspath(sys.argv[1])
        currPath = os.path.abspath(sys.argv[2])
        #print "currPath =", currPath
        
        if docsPath[-1] != '/':
            docsPath += '/'
        setClassPath()
        fileToMethod = readIndex(docsPath, "index.idx")
        methodContents = "";
        
        currMethod = open(currPath)
        for line in currMethod.readlines():
            methodContents += line + ' '
        
        for agent in fileToMethod:
            queryResultsList = query(docsPath, methodContents, agent)
            queryResultsList = sorted(queryResultsList, resultsSorter)
            #Find and remove the current method from the list
            
            writeResults(queryResultsList, docsPath + agent + "/list.ranks", fileToMethod, agent)
    else:
        print "\tUsage: jython tfidf.py <path to root of documents directory> <path to current method contents file>"
        
    sys.exit(0)

if __name__ == "__main__":
    main()
