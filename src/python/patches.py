# TODO: Can this class and the HeaderData class be replaced/merged with the
# FileNavigation class? They all seem to hold the same data...

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

    def __str__(self):
        return str(self.startOffset) + ' to ' + str(self.startOffset + self.length - 1) + ': ' + self.fqn
