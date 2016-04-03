from AbstractLanguageHelper import AbstractLanguageHelper
import os
import re
from jsAdditionalDbProcessor import JSAdditionalDbProcessor


class JavaScriptHelper (AbstractLanguageHelper):

    JS_STD_LIB = 'LJS_Std_lib;.'
    METHOD_TARGET_REGEX = re.compile(r'L/hexcom/(.*?)/.*?([a-z|A-Z]+).js.*?;.(.*?)\(.*')

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

    def isMethodFqn(self, filePathOrFqn):
        if self.METHOD_TARGET_REGEX.match(filePathOrFqn) != None:
            return True
        return False

    def getFileName(self, projectFolderPath, className, extn):
        return os.path.join(projectFolderPath, className[1:])

    def excludeMethod(self, node):
        if node.startswith(self.JS_STD_LIB):
            return True
        return False

    def performDBPostProcessing(self, db):
        JSAdditionalDbProcessor(db).process()

    def isVariantOf(self, fqn1, fqn2):
        #/hexcom/2014-05-26-10:18:35/js/view.js;.renderText(x"," y"," fontSize"," color"," text)
        #L/hexcom/Current/js_v9/Hex.js/Hex(sideLength);.rotate() -- nested methods

        FILE_TARGET_REGEX = re.compile(r'L/hexcom/(.*?)/.*?([a-z|A-Z]+).js.*')

        #They are not FQNs of non-std methods in the topology
        if FILE_TARGET_REGEX.match(fqn1) == None or FILE_TARGET_REGEX.match(fqn2) == None:
            return False

        match1 = FILE_TARGET_REGEX.match(fqn1).groups()
        match2 = FILE_TARGET_REGEX.match(fqn2).groups()

        # Return false if both are in same variant
        if match1[0] == match2[0]:
            return False

        #Return false if not same file
        elif match1[1] != match2[1]:
            return False

        else:
            #If both are not method FQN, return False -- incorrect strings
            if not (self.isMethodFqn(fqn1) and self.isMethodFqn(fqn2)):
                return False

            #If both are method FQN, return if they are same methods in same files
            else:

                match1 = self.METHOD_TARGET_REGEX.match(fqn1).groups()
                match2 = self.METHOD_TARGET_REGEX.match(fqn2).groups()

                return match1[1] == match2[1] and match1[2] == match2[2]