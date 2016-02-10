import iso8601
import datetime

class PFIGFileHeader:
    __INSERT_QUERY = "INSERT INTO logger_log (user, timestamp, action, target, referrer, agent) VALUES (?, ?, ?, ?, ?, ?)"
    __METHOD_DECLARATION_OFFSETS_DESC_UNTIL_TIME_QUERY = "SELECT timestamp, action, target, referrer FROM logger_log WHERE action = 'Method declaration offset' and timestamp < ? ORDER BY timestamp DESC"


    @staticmethod
    def addPFIGJavaFileHeader(conn, navigation, projectFolderPath, langHelper):
        # We will replace the fromNav in the navigation with a pfisHeader
        className = langHelper.normalize(navigation.fromFileNav.filePath)
        #print "Class name normalized: " + className
        #className, _, _ = navEntry.prevEntry.method.split(",")
        #ts = navEntry.timestamp
        #print navigation.toStr()
        #print "From timestamp:", navigation.fromFileNav.timestamp
        #print "To (query) timestamp:", navigation.toFileNav.timestamp
    
        classFilePath = langHelper.getFileName(projectFolderPath, className, langHelper.FileExtension)
        
        c = conn.cursor()
        c.execute(PFIGFileHeader.__METHOD_DECLARATION_OFFSETS_DESC_UNTIL_TIME_QUERY, [navigation.toFileNav.timestamp])
        lowestOffset = -1
        fqn = None
        out = None
        
        for row in c:
            methodFqn, offset = row['target'], int(row['referrer'])
            
            # Get the class of the method    
            if className == langHelper.normalize(methodFqn):
                if lowestOffset == -1 or offset < lowestOffset:
                    lowestOffset = offset
                    fqn = methodFqn[0:methodFqn.rfind('.')]
                    
        c.close()
        #print "Lowest offset =", lowestOffset
        
        if lowestOffset > -1:
            fqn = fqn + '.pfigheader()V'
            dt = iso8601.parse_date(navigation.fromFileNav.timestamp)
            dt += datetime.timedelta(milliseconds=1)
            
            pfigHeader = HeaderData(fqn, lowestOffset, dt)
            PFIGFileHeader.__insertHeaderIntoDb(pfigHeader, classFilePath, conn)
            out = pfigHeader.fqn
        
        return out
    
    @staticmethod
    def __insertHeaderIntoDb(pfigHeader, classFilePath, conn):
        #print "Reading file contents..."
        f = open(classFilePath, 'r')
        # TODO: Verify that contents is being handled by the predictive
        # algorithms correctly. They currently contain newlines, which the graph
        # producing code may be sensitive to.
        contents = f.read(pfigHeader.length)
        #print "Done reading file contents."
        #print "Adding header to database..."
        
        dummy = "auto-generated"
        timestamp = pfigHeader.timestamp
        
        c = conn.cursor()
        c.execute(PFIGFileHeader.__INSERT_QUERY, [dummy, timestamp, 'Method declaration', pfigHeader.fqnClass, pfigHeader.fqn, dummy])
        c.execute(PFIGFileHeader.__INSERT_QUERY, [dummy, timestamp, 'Method declaration offset', pfigHeader.fqn, str(0), dummy])
        c.execute(PFIGFileHeader.__INSERT_QUERY, [dummy, timestamp, 'Method declaration length', pfigHeader.fqn, str(pfigHeader.length), dummy])
        c.execute(PFIGFileHeader.__INSERT_QUERY, [dummy, timestamp, 'Method declaration scent', pfigHeader.fqn, contents, dummy])
        conn.commit()
        c.close()
        #print "Done adding header to database."
        
class HeaderData:
    def __init__(self, fqn, length, dt):
        self.fqn = fqn
        self.fqnClass = fqn[0:fqn.find(';') + 1]
        self.length = length
        ms = dt.microsecond / 1000
        self.timestamp = dt.strftime("%Y-%m-%d %H:%M:%S." + str(ms))
        
    def isOffsetInHeader(self, offset):
        raise NotImplementedError