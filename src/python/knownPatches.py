from patches import MethodPatch

class KnownPatches(object):
    # This class keeps track of the classes that the programmers "knows about."
    # It is used primarily to map from Text selection offset events to actual
    # methods.

    def __init__(self, languageHelper):
        self.langHelper = languageHelper
        self.files = {}
        
    def addFilePatch(self, filePathOrFqn):
        # Add a file to the known files. Each file is stored according to its
        # normalized path so that later when we query by FQN, we can quickly
        # retrieve a file's contents. This is because a normalized FQN should
        # match a normalized path if both are representing the same class.
        norm = self.langHelper.normalize(filePathOrFqn)
        if norm != '':
            # Get the outer class because the data structure is by file name
            norm = self.langHelper.getOuterClass(norm)
            
            # Set up the initial empty list if this is the first instance of the
            # file
            if norm not in self.files:
                self.files[norm] = []
                
            # Add the method if it doesn't already exist in the file
            if self.langHelper.isMethodFqn(filePathOrFqn):
                if self.__getMethodInMethodList(filePathOrFqn, self.files[norm]) is None:
                    self.files[norm].append(MethodPatch(filePathOrFqn))

    def findMethodByFqn(self, fqn):
        # Query the known patches by a method's FQN. Returns the MethodData
        # object if it was found, or None if it wasn't. The MethodData object
        # can then be updated as necessary.
        norm = self.langHelper.normalize(fqn)
        
        # Get the outer class because the data structure is by file name
        norm = self.langHelper.getOuterClass(norm)
        if norm in self.files:
            return self.__getMethodInMethodList(fqn, self.files[norm])
        return None
                    
    def findMethodByOffset(self, filePath, offset):
        
        # Query the known patches by an offset. If a method corresponds to this
        # offset in the given file, then its corresponding MethodData object is
        # returned, otherwise, None is returned.
            
        norm = self.langHelper.normalize(filePath)
        
        if norm == '' or norm not in self.files:
            return None
        
        methods = self.files[norm]

        surroundingMethods = [method for method in methods if method.isOffsetInMethod(offset)]

        if surroundingMethods is not None and len(surroundingMethods) > 0:
            sortedSurroundingMethods = sorted(surroundingMethods, key=lambda method:method.startOffset, reverse=True)
            return sortedSurroundingMethods[0]

        return None
    
    def isOffsetInGap(self, filePath, offset):
        # Because there is no gap between the file header and the 1st method, we
        # only need to consider gaps from the 1st declaration onwards
        norm = self.langHelper.normalize(filePath)
        
        if norm == '' or norm not in self.files:
            raise RuntimeError('isOffsetInGap: knownPatches does not contain the normalized file: ' + norm)
        
        methods = self.files[norm]
        if len(methods) == 0:
            return False
        
        lowestOffset = methods[0].startOffset
        
        for method in methods:
            if method.startOffset < lowestOffset:
                lowestOffset = method.startOffset
            if method.isOffsetInMethod(offset):
                return False
        
        if offset < lowestOffset:
            # We are in what will eventually be the header, so return False
            return False
        
        return True
            
    
    def getAdajecentMethods(self):
        # Returns a list of method lists where each inner list is the set of
        # methods in a file ordered by offset.
        adjacentMethodLists = []
        
        for norm in self.files:
            sortedMethods = sorted(self.files[norm], key=lambda method: method.startOffset)
            adjacentMethodLists.append(sortedMethods)
            
        return adjacentMethodLists
            

    def __getMethodInMethodList(self, methodFqn, methodList):
        # Return the method data object in the list that matches the desired FQN
        for method in methodList:
            if method.fqn == methodFqn:
                return method
        return None
    
    def __str__(self):
        s = ''
        for norm in self.files:
            s += norm + '\n'
            for methodPatch in self.files[norm]:
                s += str(methodPatch) + '\n'
                
        return s
