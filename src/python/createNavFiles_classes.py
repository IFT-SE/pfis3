#!/usr/bin/env jython
import sys
import sqlite3
import os
import shutil
import re

# This regular expression captures forward and backward slashes
# It is used to convert Windows style slashes '\' to a single
# consistent UNIX style path with '/'
fix_regex = re.compile(r'[\\/]+')

def fix(string):
    return fix_regex.sub('/',string)

def makeDocumentFilesForNavs(db, navdir, navList):
# Creates a directory of files for TF-IDF.  The root directory passed
# in is where the files are created.  Each file created contains the
# contents of a method as it was stored by the PFIG database.  Duplicates
# are handled by overwriting older method entries with newer ones.
# Also creates an index file, index.idx in the root directory that maps
# file paths to method names
# ===== Variables =====
# sourcefile = path to PFIG database
# outfile = path to where to create the current nav
    if navdir[-1] != '/':
        navdir += '/'

    navs = []
    visitedNavs = []
    num = 0;
        
    f = open(navList)
    for line in f.readlines():
        nav = getClass(line)
        if len(navs) == 0 or navs[-1][1] != nav:
            navs.append((num, nav))
            visitedNavs.append(nav)
        num += 1
            
    conn = sqlite3.connect(db)
    conn.row_factory = sqlite3.Row
    
    for (num, nav) in navs:
        c = conn.cursor()
        c.execute('''select timestamp from logger_log where action in ('Text selection offset') order by timestamp asc limit ''' + str(num + 1))
        for row in c:
            ts = row['timestamp']
        c.close()
    
        c = conn.cursor()
        c.execute("select target, referrer from logger_log where action in ('Method declaration scent') and timestamp < '" + ts + "' order by timestamp asc")
        for row in c:
            cls = getClass(fix(row['target']))
            if cls in visitedNavs:
                content = fix(row['referrer'])
                try:
                    os.mkdir(navdir + "nav_" + str(num) + '/')
                except OSError as e:
                    pass
                addToFile(navdir + "nav_" + str(num) + '/', cls.replace('/','.') + ".txt", content) 
        c.close()
    
def getClass(fqn):
    classEnd = fqn.find(';')
    return fqn[0:classEnd]
    
def addToFile(navdir, file, content):
    if navdir[-1] != '/':
        navdir[-1] = '/'
    try:
        f = open(navdir + file, 'a')
        f.write(content.replace('/u000a', '\n'))
        f.close()
    except IOError as e:
        print "uh oh"
    

def main():
    if len(sys.argv) == 4:
    	makeDocumentFilesForNavs(sys.argv[1], sys.argv[2], sys.argv[3])
    else:
    	print "\tUsage: python createNavFiles_classes.py <pfig db> <nav dir> <nav list>"
    	
    sys.exit(0)


if __name__ == "__main__":
    main()
