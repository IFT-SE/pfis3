class Navigation(object):
    # A navigation is a tuple representing one programmer navigation through the
    # code. fromFileNav represents the where the programmer navigated from and
    # toFileNav represents where the programmer navigated to. Both of these
    # parameters should be FileNavigation objects.
    def __init__(self, fromFileNav, toFileNav):
        self.fromFileNav = fromFileNav
        self.toFileNav = toFileNav

    def isToSameMethod(self):
        if self.fromFileNav is not None and self.toFileNav is not None:
            if 'changes.txt' in self.toFileNav.filePath and 'changes.txt' in self.fromFileNav.filePath:
                firstVar = self.toFileNav.filePath
                secondVar = self.fromFileNav.filePath
                firstVar = firstVar[8:]
                firstVar = firstVar[:-12]
                secondVar = secondVar[8:]
                secondVar = secondVar[:-12]
                if firstVar == secondVar:
                    return True
            if self.fromFileNav.methodFqn is not None and self.toFileNav.methodFqn is not None:
                return self.fromFileNav.methodFqn == self.toFileNav.methodFqn
        return False

    def isFromUnknown(self):
        if self.fromFileNav is not None and self.fromFileNav.methodFqn is not None:
            return False
        return True

    def isToUnknown(self):
        if self.toFileNav is not None and self.toFileNav.methodFqn is not None:
            return False
        return True

    def clone(self):
        fromNav = None
        toNav = None
        if self.fromFileNav is not None:
            fromNav = self.fromFileNav.clone()
        if self.toFileNav is not None:
            toNav = self.toFileNav.clone()

        return Navigation(fromNav, toNav)

    def __str__(self):
        fromLoc = None
        toLoc = None

        if self.fromFileNav is not None:
            fromLoc = str(self.fromFileNav)
        if self.toFileNav is not None:
            toLoc = str(self.toFileNav)

        return str(fromLoc) + ' --> ' + str(toLoc)

class PatchType(object):
    METHOD = 'method'
    CHANGELOG = 'change_log'

class FileNavigation(object):
    # A file navigation represents the Text selection offset data that was
    # captured by PFIG. The Text selection offset occurs any time a programmer's
    # text cursor position changes. If we determine that the text cursor is in a
    # method that the programmer has knowledge of then, methodFqn has that info.
    # If methodFqn is none, then this was a navigation to an 'unknown location'
    def __init__(self, timestamp, filePath, offset, patchType):
        self.timestamp = timestamp
        self.filePath = filePath
        self.patchType = patchType
        self.offset = offset
        self.isGap = False
        self.methodFqn = None
        #TODO: make sure methodFqn is same as filePath for changelog patch types

    def clone(self):
        fileNavClone = FileNavigation(self.timestamp, self.filePath, self.offset)
        fileNavClone.methodFqn = self.methodFqn
        fileNavClone.patchType = self.patchType
        return fileNavClone

    def __str__(self):
        if self.methodFqn is not None:
            return self.methodFqn
        return str(self.filePath) + ' at ' + str(self.offset)
