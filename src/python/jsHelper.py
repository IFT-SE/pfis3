from AbstractLanguageHelper import AbstractLanguageHelper
import os
from jsAdditionalDbProcessor import JSAdditionalDbProcessor


class JavaScriptHelper (AbstractLanguageHelper):

    JS_STD_LIB = 'LJS_Std_lib;.'

    def __init__(self):
        fileExtension = ".js"
        normalizedPathRegex = r"(.*)\.js"
        packageRegex = r"(.*?)\/"
        AbstractLanguageHelper.__init__(self, fileExtension, normalizedPathRegex, packageRegex)


    def normalize(self, string):
        # Return the class indicated in the string. Empty string returned on fail.
        # File-name example:
        # Raw file name: jEdit/src/org/gjt/sp/jedit/gui/StatusBar.java
        # Normalized file name: org/gjt/sp/jedit/gui/StatusBar

        m = self.REGEX_NORM_ECLIPSE.match(string)
        if m:
            return m.group(1)

        filepath = self.fixSlashes(string)
        n = self.REGEX_NORM_PATH.match(filepath)
        if n:
            return filepath

    def getFileName(self, projectFolderPath, className, extn):
        return os.path.join(projectFolderPath, className[1:])

    def excludeMethod(self, node):
        if node.startswith(self.JS_STD_LIB):
            return True
        return False

    def performDBPostProcessing(self, db):
        JSAdditionalDbProcessor(db).process()
