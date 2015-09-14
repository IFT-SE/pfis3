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

def makeDocumentFilesForTFIDF(sourcefile, rootdir):
# Creates a directory of files for TF-IDF.  The root directory passed
# in is where the files are created.  Each file created contains the
# contents of a method as it was stored by the PFIG database.  Duplicates
# are handled by overwriting older method entries with newer ones.
# Also creates an index file, index.idx in the root directory that maps
# file paths to method names
# ===== Variables =====
# sourcefile = path to PFIG database
# rootdir = path to where to create the root document directory

    if os.path.exists(rootdir):
        shutil.rmtree(rootdir)
    os.makedirs(rootdir)
    	
    if rootdir[-1] != '/':
        rootdir += '/'
        
    # Create the index that maps file names to method names
    idx = open(rootdir + "index.idx", 'w')
    methodToFileNum = {}

    '''Load just the scent portion of the graphs'''
    conn = sqlite3.connect(sourcefile)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute('''select user,action,target,referrer,agent from logger_log where action in ('Method declaration scent')''')
    i = 0
    fileNum = 0
    for row in c:
        user, action, target, referrer, agent = (row['user'][0:3],
                                                 row['action'],
                                                 fix(row['target']),
                                                 fix(row['referrer']),
                                                 row['agent'])
        if not os.path.exists(rootdir + agent):
		    os.makedirs(rootdir + agent)
                                                 
        if target not in methodToFileNum:
            methodToFileNum[target] = agent + '/' + str(i)
            fileNum = agent + '/' + str(i)
       	    i += 1
        else:
            #print "\tOverwriting", target
            fileNum = methodToFileNum[target]
        
	    # referrer will have our code
        idx.write(str(fileNum) + ".txt\t" + target + "\n")
        file = open(rootdir + str(fileNum) + '.txt', 'w')
        
        # Replace unicode newlines with ascii newlines
        file.write(referrer.replace('/u000a', '\n'))
        file.close
    c.close
    idx.close
    print rootdir, "Created",i,"documents"

def main():
    if len(sys.argv) == 3:
    	makeDocumentFilesForTFIDF(sys.argv[1], sys.argv[2])
    else:
    	print "\tUsage: python createDocs.py <PFIG database> <output directory>"
    	
    sys.exit(0)


if __name__ == "__main__":
    main()
