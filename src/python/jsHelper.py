from AbstractLanguageHelper import AbstractLanguageHelper
import os

class JavaScriptHelper (AbstractLanguageHelper):

    JS_STD_PREFIX = "JS_Std_lib/"

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
        n = self.REGEX_NORM_PATH.match(self.fixSlashes(string))
        pos = string.rfind(".js")
        if pos:
            return string[:pos]
        return ''

    def getFileName(self, projectFolderPath, className, extn):
        return os.path.join(projectFolderPath, className[1:] + extn)

    def ignore_rank(self, target):
        is_std = target.startswith(JavaScriptHelper.JS_STD_PREFIX)
        return is_std
