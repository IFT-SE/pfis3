class KnownPatches(object):

    def __init__(self, languageHelper):
        self.langHelper = languageHelper
        self.methodToFileMap = {}
        self.files = {}
        
    def addFilePatch(self, filePathOrFqn):
        norm = self.langHelper.normalize(filePathOrFqn)
        if norm != '':
            if norm not in self.files:
                self.files[norm] = []
                #print "Added class", norm
                
            if self.__isMethodFqn(filePathOrFqn):
                if not self.__getMethodInMethodList(filePathOrFqn, self.files[norm]):
                    self.files[norm].append(MethodPatch(filePathOrFqn))
                    #print "    Added method", filePathOrFqn
                    
    def findMethodByFqn(self, fqn):
        norm = self.langHelper.normalize(fqn)
        if norm in self.files:
            return self.__getMethodInMethodList(fqn, self.files[norm])
                    
    def findMethodByOffset(self, filePath, offset):
        #print "Looking for ", filePath, offset
        norm = self.langHelper.normalize(filePath)
        
        if norm == '' or norm not in self.files:
            return None
        
        methods = self.files[norm]
        for method in methods:
            if method.isOffsetInMethod(offset):
                return method
        return None

    def __isMethodFqn(self, filePathOrFqn):
        if filePathOrFqn.startswith('L') \
            and ';' in filePathOrFqn \
            and '.' in filePathOrFqn:
            return True
        return False
    
    def __getMethodInMethodList(self, methodFqn, methodList):
        for method in methodList:
            if method.fqn == methodFqn:
                return method
        return None
    
class MethodPatch(object):
    
    def __init__(self, fqn):
        self.fqn = fqn
        self.startOffset = -1
        self.length = -1
        
    def isOffsetInMethod(self, offset):
        endOffset = self.startOffset + self.length
        if self.startOffset < 0 or self.length < 0:
            return False
        
        if offset >= self.startOffset and offset < endOffset:
            return True
        return False
        