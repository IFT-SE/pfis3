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
    
def query(docsPath, text):
    # Original java method header
    #    public TFIDFIndex(String pathToSomeDirectoryOfFiles, String filenameEnding,
    #        boolean recurse) throws Exception
    import TFIDFIndex
    tfidf = TFIDFIndex(docsPath, ".txt", 0)
    return tfidf.query(text)
    
def resultsSorter (x,y):
    return x.goodnessOfMatch < y.goodnessOfMatch
    
def getTopHit(qrList, ftm):
    #print "Rank 1:", ftm[qrList[0].fileIdentifier], qrList[0].goodnessOfMatch
    #print "Rank 2:", ftm[qrList[1].fileIdentifier], qrList[1].goodnessOfMatch
    #print "Rank 3:", ftm[qrList[2].fileIdentifier], qrList[2].goodnessOfMatch
    #print "Rank 4:", ftm[qrList[3].fileIdentifier], qrList[3].goodnessOfMatch
    return  ftm[qrList[0].fileIdentifier], qrList[0].goodnessOfMatch
    
def writeResults(qrList, path):
    f = open(path, 'w')
    for result in qrList:
        f.write("agentString" + '\t' + str(result.fileIdentifier) + '\t' + str(result.goodnessOfMatch) + '\n')
    f.close
    
def getClass(fqn):
    classEnd = fqn.find(';')
    return fqn[0:classEnd]

def main():
    if len(sys.argv) == 3:
        docsPath = os.path.abspath(sys.argv[1])
        navList = os.path.abspath(sys.argv[2])
        
        if docsPath[-1] != '/':
            docsPath += '/'
        setClassPath()
        #fileToMethod = readIndex(docsPath, "index.idx")
        classContents = "";
        
        navs = []
        visitedNavs = []
        num = 0;
        
        #Build class navigation list
        f = open(navList)
        for line in f.readlines():
            nav = getClass(line)
            if len(navs) == 0 or navs[-1][1] != nav:
                navs.append((num, nav))
                visitedNavs.append(nav)
            num += 1
        
        #Test how similar each class is to the other classes we've seen so far
        for (num, nav) in navs:
            navPath = docsPath + "nav_" + str(num) + "/"
            currClassFile = navPath + nav.replace('/', '.') + ".txt"
            
            g = open(currClassFile)
            for line in g.readlines():
                classContents += line + ' '
            g.close()
            
            queryResultsList = query(navPath, classContents)
            queryResultsList = sorted(queryResultsList, resultsSorter)
            writeResults(queryResultsList, navPath + "list.ranks")
        f.close()
    else:
        print "\tUsage: jython tfidfCurrentClass.py <path to root of documents directory> <path to nav list>"
        
    sys.exit(0)

if __name__ == "__main__":
    main()
