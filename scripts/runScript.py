import os
import subprocess

def main():
#     -d "/Users/Dave/Desktop/code/icsme15/p5.db" 
#     -p "/Users/Dave/Documents/workspace/jEdit-2548764/src" 
#     -l JAVA 
#     -s "/Users/Dave/Desktop/code/pfis3/data/je.txt" 
#     -o "/Users/Dave/Desktop/output/icsme15/p5"

    d = '/Users/Dave/Desktop/code'
    p = '/Users/Dave/Documents/workspace/jEdit-2548764/src'
#     p = '/Users/Dave/Desktop/code/p8l-vanillaMusic/src'
    l = 'JAVA'
    s = '/Users/Dave/Desktop/code/pfis3/data/je.txt'
    o = '/Users/Dave/Desktop/output'
    x = '/Users/Dave/Desktop/code/pfis3/data/javaAlgorithmOptions.xml'
    
    db_dirName = 'icsme15'
    
    d = os.path.join(d, db_dirName)
    db_fileNames = [f for f in os.listdir(d) if os.path.isfile(os.path.join(d, f)) and f.endswith('.db')]
    
    for db in db_fileNames:
        name = db[0:db.index('.')]
        d_participant = os.path.join(d, db)
        o_participant = os.path.join(o, db_dirName, name)
        
        print "Running data for " + d_participant + '...'
        
        subprocess.call(['python',
                        '/Users/Dave/Desktop/code/pfis3/src/python/pfis3.py', \
                        '-d', d_participant, \
                        '-p', p, \
                        '-l', l, \
                        '-s', s, \
                        '-o', o_participant, \
                        '-x', x])


if __name__ == '__main__':
    main()