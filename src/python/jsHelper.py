from AbstractLanguageHelper import AbstractLanguageHelper
import os
import re
from jsAdditionalDbProcessor import JSAdditionalDbProcessor


class JavaScriptHelper (AbstractLanguageHelper):

    JS_STD_LIB = 'LJS_Std_lib;.'
    METHOD_TARGET_REGEX = re.compile(r'L/hexcom/(.*?)/.*?([a-z|A-Z]+).js.*?;.(.*?)\(.*')
    OUTER_CLASS_REGEX = re.compile(r'(.*.js).*')

    def __init__(self):
        fileExtension = ".js"
        normalizedPathRegex = r"(.*)\.js"
        packageRegex = r"(.*?)\/"
        AbstractLanguageHelper.__init__(self, fileExtension, normalizedPathRegex, packageRegex)


    def normalize(self, string):
        # Return the immediate container of the method
        # L/hexcom/Current/js_v9/Hex.js/Hex(sideLength);.rotate() -- nested methods
        # returns: L/hexcom/Current/js_v9/Hex.js/Hex(sideLength)

        m = self.REGEX_NORM_ECLIPSE.match(string)
        if m:
            return m.groups()[0]

        filepath = self.fixSlashes(string)
        n = self.REGEX_NORM_PATH.match(filepath)
        if n:
            return filepath

    def getOuterClass(self, fqnToContainer):
        m = self.OUTER_CLASS_REGEX.match(fqnToContainer)
        if m:
            return m.groups()[0]
        else:
            raise Exception("Incorrect fqn: ", fqnToContainer)


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
