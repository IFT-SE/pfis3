from AbstractLanguageHelper import AbstractLanguageHelper
import os
import re
from patches import PatchType
from jsAdditionalDbProcessor import JSAdditionalDbProcessor


class JavaScriptHelper (AbstractLanguageHelper):

	JS_STD_LIB = 'LJS_Std_lib;.'
	CHANGELOG_TARGET_REGEX = re.compile(r'L/hexcom/(.*?)/.*?([a-z|A-Z]+).txt')
	CHANGELOG_TYPE_REGEX = re.compile(r'(.*.txt)')
	METHOD_TARGET_REGEX = re.compile(r'L/hexcom/(.*?)/.*?([a-z|A-Z]+).js.*?;.(.*?)\(.*')
	OUTER_CLASS_REGEX = re.compile(r'(.*.js|.*.txt).*')
	REGEX_NORM_ECLIPSE = re.compile(r"L([^;]+).*")

	def __init__(self):
		fileExtension = ".js"
		normalizedPathRegex = r"(.*)\.[js|txt]"
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
		hasMatch = self.REGEX_NORM_PATH.match(filepath)
		if hasMatch:
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

	def isChangelogFqn(self, filePathOrFqn):
		if self.CHANGELOG_TARGET_REGEX.match(filePathOrFqn) != None:
			return True
		return False

	def getFileName(self, projectFolderPath, className, extn):
		return os.path.join(projectFolderPath, className[1:])

	def isLibMethodWithoutSource(self, node):
		if node.startswith(self.JS_STD_LIB):
			return True
		return False

	def performDBPostProcessing(self, db):
		JSAdditionalDbProcessor(db).process()

	def isNavToValidFileType(self, filePath):
		if self.CHANGELOG_TYPE_REGEX.match(filePath) != None:
			return True
		return self.hasLanguageExtension(filePath)

	def isVariantOf(self, fqn1, fqn2):
		#L/hexcom/2014-05-26-10:18:35/js/view.js;.renderText(x"," y"," fontSize"," color"," text)
		#L/hexcom/Current/js_v9/Hex.js/Hex(sideLength);.rotate() -- nested methods

		#FILE_TARGET_REGEX = re.compile(r'L/hexcom/(.*?)/(.*)') - matches entire path to method
		FILE_TARGET_REGEX = re.compile(r'L/hexcom/(.*?)/(.*);.(.*)\(')

		#They are not FQNs of non-std methods in the topology
		if FILE_TARGET_REGEX.match(fqn1) == None or FILE_TARGET_REGEX.match(fqn2) == None:
			return False

		match1 = FILE_TARGET_REGEX.match(fqn1).groups()
		match2 = FILE_TARGET_REGEX.match(fqn2).groups()

		# Return false if both are in same variant
		if match1[0] == match2[0]:
			return False

		else:
			#Right now it is just FQN
			#TODO: Queer case of headers!!!
			#return match1[1] == match2[1] # Match for entire path
			return match1[2] == match2[2] #Match just method name

	def getPatchType(self, filePath):
		if self.CHANGELOG_TYPE_REGEX.match(filePath) != None:
			return PatchType.CHANGELOG
		elif self.hasLanguageExtension(filePath):
			return PatchType.SOURCE

		return None
