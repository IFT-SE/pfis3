from AbstractLanguageHelper import AbstractLanguageHelper

class JavaHelper(AbstractLanguageHelper):

    def __init__(self):
        fileExtension = ".java"
        normalizedPathRegex = r".*src\/(.*)\.java"
        packageRegex = r"(.*)/[a-zA-Z0-9]+"
        AbstractLanguageHelper.__init__(self, fileExtension, normalizedPathRegex, packageRegex)


    def normalize(self, s):
        # Return the class indicated in the string. Empty string returned on fail.
        # File-name example:
        # Raw file name: jEdit/src/org/gjt/sp/jedit/gui/StatusBar.java
        # Normalized file name: org/gjt/sp/jedit/gui/StatusBar

        m = self.REGEX_NORM_ECLIPSE.match(s)
        if m:
            return m.group(1)
        n = self.REGEX_NORM_PATH.match(self.fixSlashes(s))
        if n:
            return n.group(1)
        return ''

    def getOuterClass(self, loc):
        # This split allows inner classes to be handled properly, by setting the
        # class to the outer class instead of the inner one.
        loc2 = loc.split('$')[0]
        return loc2

    def isMethodFqn(self, filePathOrFqn):
        # Check if this FQN is a method.
        # TODO: Move this to the langHelper?
        if filePathOrFqn.startswith('L') \
            and ';' in filePathOrFqn \
            and '.' in filePathOrFqn:
            return True
        return False