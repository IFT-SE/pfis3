import sys
import sqlite3
import shutil
import datetime
import iso8601
import re

fix_regex = re.compile(r'[\\/]+')

normalize_eclipse = re.compile(r"L([^;]+);.*")
normalize_path = re.compile(r".*src\/(.*)\.java")
package_regex = re.compile(r"(.*)/[a-zA-Z0-9]+")
project_regex = re.compile(r"\/(.*)\/src/.*")


def fix(string):
    return fix_regex.sub('/',string)

def normalize(string):
    '''
    Return the class indicated in the string.
    File-name example:
    Raw file name: jEdit/src/org/gjt/sp/jedit/gui/StatusBar.java
    Normalized file name: org/gjt/sp/jedit/gui/StatusBar

    '''
    #print "In normalize string=", string
    m = normalize_eclipse.match(string)
    if m:
        return m.group(1)
    n = normalize_path.match(fix(string))
    if n:
        return n.group(1)
    return ''

def package(string):
    '''Return the package.'''
    m = package_regex.match(normalize(string))
    if m:
        return m.group(1)
    return ''

def project(string):
    '''Return the project.'''
    m = project_regex.match(fix(string))
    if m:
        return m.group(1)
    return ''

    
conn = ''
c = ''
id = 0
user = 'c4f2437e-6d7b-4392-b68c-0fa7348facbd'
agent = 'a23fe51d-196a-45b3-addf-3db4e8423e4f'

def readScrollingEventsIntoDb(path):
    global conn, c, id, user, agent
        
    c.execute("delete from logger_log where action in ('Text selection', 'Text selection offset');")
    conn.commit()
    
    navData = open(path)
    for line in navData:
        cols = line.split('\t')
        
        dt = convertManualTimeToPFIGTime(cols[2])
        
        c.execute('insert into logger_log values (?, ?, ?, ?, ?, ?, ?);', 
            (id, user, dt, "Text selection offset", cols[0], cols[1], agent))
        conn.commit()
        id += 1
    
    
def readNewNavsFileIntoDb(path):
    global id
    navData = open(path)
    
    for line in navData:
        cols = line.rstrip('\r\n').split('\t')
        
        dt = convertManualTimeToPFIGTime(cols[0])
        
        if cols[1] == 'New folder':
            newFolder(dt, cols[2], cols[3])
        elif cols[1] == 'New package':
            newPackage(dt, cols[2], cols[3])
        elif cols[1] == 'New java file':
            newJavaFile(dt, cols[2], cols[3])
        elif cols[1] == 'New file header':
            newFileHeader(dt, cols[2], cols[3])
        elif cols[1] == 'Open call hierarchy':
            openCallHierarchy(dt, cols[2], cols[3])
        else:
            other(dt, cols[1], cols[2], cols[3])
        id += 1
            
    navData.close 
    
def convertVideoTimeToPFIGTime(vidTime):
    #Expected format: HH:MM:SS.mmm
    #Video time at 00:00:00.000 = PFIG time at 2010-01-25 15:01:00.200 = 1264460460200ms
    dt = datetime.datetime.fromtimestamp(1264460460)
    vidTime = vidTime.split(':')
    hr = int(vidTime[0])
    min = int(vidTime[1])
    vidTime = vidTime[2].split('.')
    sec = int(vidTime[0])
    ms = int(vidTime[1])
    delta = datetime.timedelta(hours=hr, minutes=min, seconds=sec, milliseconds=ms)
    dt = dt + delta
    
    return dt
    
def convertManualTimeToPFIGTime(vidTime):
    #Expected format: HH:MM:SS.mmm
    #Video time at 00:00:00.000 = PFIG time at 2010-01-25 00:00:00.000 = 1264406400000ms
    #print "Checking:", vidTime
    dt = datetime.datetime.fromtimestamp(1264406400)
    vidTime = vidTime.split(':')
    hr = int(vidTime[0])
    min = int(vidTime[1])
    vidTime = vidTime[2].split('.')
    sec = int(vidTime[0])
    ms = int(vidTime[1])
    delta = datetime.timedelta(hours=hr, minutes=min, seconds=sec, milliseconds=ms)
    dt = dt + delta
    
    return dt
    
def other(timestamp, action, target, referrer):
    global conn, c, id, user, agent
    c.execute('insert into logger_log values (?, ?, ?, ?, ?, ?, ?);', 
        (id, user, timestamp, action, target, referrer, agent))
    conn.commit()
    
def newFolder(timestamp, path, folderName):
    global conn, c, id, user, agent
    c.execute('insert into logger_log values (?, ?, ?, ?, ?, ?, ?);', 
        (id, user, timestamp, "New folder", path, folderName, agent))
    conn.commit()
    
def newPackage(timestamp, path, packageName):
    global conn, c, id, user, agent
    c.execute('insert into logger_log values (?, ?, ?, ?, ?, ?, ?);', 
        (id, user, timestamp, "New package", path, packageName, agent))
    conn.commit()
    
def newJavaFile(timestamp, path, fileName):
    global conn, c, id, user, agent
    nPath = normalize(path)
    fakeHeader = 'L' + nPath + ';.PFIGFileHeader()V'
    
    c.execute('insert into logger_log values (?, ?, ?, ?, ?, ?, ?);', 
        (id, user, timestamp, "New java file", path, fileName, agent))
    id += 1
    c.execute('insert into logger_log values (?, ?, ?, ?, ?, ?, ?);', 
        (id, user, timestamp, "Method declaration", nPath, fakeHeader, agent))
    id += 1
    c.execute('insert into logger_log values (?, ?, ?, ?, ?, ?, ?);', 
        (id, user, timestamp, "Method declaration offset", fakeHeader, 0, agent))
    id += 1
    c.execute('insert into logger_log values (?, ?, ?, ?, ?, ?, ?);', 
        (id, user, timestamp, "Method declaration length", fakeHeader, len(fileName), agent))
    id += 1
    c.execute('insert into logger_log values (?, ?, ?, ?, ?, ?, ?);', 
        (id, user, timestamp, "Method declaration scent", fakeHeader, fileName, agent))
    conn.commit()

def newFileHeader(timestamp, path, contents):
    global conn, c, id, user, agent
    nPath = normalize(path)
    fakeHeader = 'L' + nPath + ';.PFIGFileHeader()V'
    
    c.execute('insert into logger_log values (?, ?, ?, ?, ?, ?, ?);', 
        (id, user, timestamp, "New file header", fakeHeader, contents, agent))
    
def openCallHierarchy(timestamp, path, method):
    global conn, c, id, user, agent
    c.execute('insert into logger_log values (?, ?, ?, ?, ?, ?, ?);', 
        (id, user, timestamp, "Open call hierarchy", path, method, agent))
    conn.commit()

def copyAndOpenDb(source, dest):
    global conn, c, id
    shutil.copyfile(source, dest)
    conn = sqlite3.connect(dest)
    c = conn.cursor()
    c.execute('select distinct id from logger_log order by id desc;')
    id = c.next()[0] + 1
    
def closeDb():
    conn.close
    
def printDateTimes():
    global conn, c
    c = conn.cursor()
    c.execute("select distinct timestamp from logger_log where action not in ('Text selection offset') order by timestamp;")
    for cols in c:
        timestamp = iso8601.parse_date(cols[0])
        print timestamp, datetime.datetime.tzname(timestamp)
    


def main():
    if len(sys.argv) == 5:
        sourceFile = sys.argv[1]
        scrollFile = sys.argv[2]
        navFile = sys.argv[3]
        outputFile = sys.argv[4]
        
        copyAndOpenDb(sourceFile, outputFile)
        #printDateTimes()
        readScrollingEventsIntoDb(scrollFile)
        readNewNavsFileIntoDb(navFile)
        closeDb()
    else:
        print "\tUsage: python buildCorrectDb.py <PFIG database> <scroll events text file> <new navigation events text file> <output database path>"
        
    sys.exit(0)

if __name__ == "__main__":
    main()
