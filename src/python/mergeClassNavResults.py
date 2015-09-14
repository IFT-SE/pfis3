import sys

def mergeFiles(navList, resultsDir, outFile):
    if resultsDir[-1] != '/':
        resultsDir += '/'

    navs = []
    visitedNavs = []
    allScores = []
    num = 0

    f = open(navList)
    for line in f.readlines():
        nav = getClass(line)
        if len(navs) == 0 or navs[-1][1] != nav:
            navs.append((num, nav))
            visitedNavs.append(nav)
        num += 1
    f.close()

    for (num, nav) in navs:
        f = open(resultsDir + "nav_" + str(num) + "/list.ranks")
        ranks = {}
        rank = 0
        for line in f.readlines():
            vals = line.split('\t')
            idx = vals[1].rindex('/') + 1
            cls = vals[1][idx:-4].replace('.', '/')
            ranks[rank] = cls
            rank += 1
        allScores.append(ranks)
        f.close()
        
    rank = 1
    
    f = open(outFile, "w")
    for i in range(len(navs)):
        for r in range(len(allScores[i])):
            #print "Comparing", navs[i][1], allScores[i][r]
            if navs[i][1] == allScores[i][r]:
                hitRank = r
        f.write("%s,%d,%d\n" % (navs[i][1], hitRank, len(allScores[i])))

    f.close()
            
def getClass(fqn):
    classEnd = fqn.find(';')
    return fqn[0:classEnd]

def main():
    if len(sys.argv) == 4:
    	mergeFiles(sys.argv[1], sys.argv[2], sys.argv[3])
    else:
        print "Usage: python mergeClassNavResults.py <nav list> <results dir> <output file>"
        
    sys.exit(0)        

if __name__ == "__main__":
    main()
