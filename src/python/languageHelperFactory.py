from java_processor import JavaHelper
from js_processor import JavaScriptHelper

class Languages:
        JAVA = "JAVA"
        JS = "JS"

class LanguageHelperFactory:

    @staticmethod
    def getLanguageHelper(language):

        processor = None

        if(language == Languages.JAVA):
            processor = JavaHelper()
        elif (language == Languages.JS):
            processor = JavaScriptHelper()
        return processor

