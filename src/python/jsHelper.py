from AbstractLanguageHelper import AbstractLanguageHelper
import os
import re
from patches import PatchType
from jsAdditionalDbProcessor import JSAdditionalDbProcessor


class JavaScriptHelper (AbstractLanguageHelper):

	JS_STD_LIB = 'LJS_Std_lib;.'

	CHANGELOG_TYPE_REGEX = re.compile(r'(.*changes\.txt)')
	CHANGELOG_FQN_REGEX = re.compile(r'L/hexcom/(.*?)/.*?([a-z|A-Z]+).txt')

	OUTPUT_TYPE_REGEX = re.compile(r'(.*\.output)')
	OUTPUT_FQN_REGEX = re.compile(r'L/hexcom/(.*?)/index\.html\.output')

	METHOD_FQN_REGEX = re.compile(r'L/hexcom/(.*?)/.*?([a-z|A-Z]+).js.*?;.(.*?)\(.*')
	FILE_FQN_REGEX = re.compile(r'(.*.js|.*.txt|.*.output).*')

	REGEX_NORM_ECLIPSE = re.compile(r"L([^;]+).*")

	PATCH_HIERARCHY_REGEX = re.compile(r'L/hexcom/(.*?)/(.*)')

	def __init__(self):
		fileExtension = ".js"
		normalizedPathRegex = r"(.*)\.[js|txt|output]"
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
		m = self.FILE_FQN_REGEX.match(fqnToContainer)
		if m:
			return m.groups()[0]
		else:
			raise Exception("Incorrect fqn: ", fqnToContainer)


	def isMethodFqn(self, filePathOrFqn):
		if self.METHOD_FQN_REGEX.match(filePathOrFqn) != None:
			return True
		return False

	def isChangelogFqn(self, filePathOrFqn):
		if self.CHANGELOG_FQN_REGEX.match(filePathOrFqn) != None:
			return True
		return False

	def isOutputFqn(self, filePathOrFqn):
		if self.OUTPUT_TYPE_REGEX.match(filePathOrFqn) != None:
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

	def isVariantOf(self, fqn1, fqn2):
		if self.isMethodFqn(fqn1) and self.isMethodFqn(fqn2):
			return self._checkMethodSimilarity(fqn1, fqn2)
		elif (self.isChangelogFqn(fqn1) and self.isChangelogFqn(fqn2)) \
				or (self.isOutputFqn(fqn1) and self.isOutputFqn(fqn2)):
			return self._checkChangelogAndOutputSimilarity(fqn1, fqn2)

	def _checkMethodSimilarity(self, fqn1, fqn2):
		# Check if fqns are from different variants, folder paths and method names.
		# Method names could have different parameters, but they are still similar.
		match1 = self.METHOD_FQN_REGEX.match(fqn1).groups()
		match2 = self.METHOD_FQN_REGEX.match(fqn2).groups()

		# Same FQN and method names, but different variant names
		return match1[0] != match2[0] and match1[1] == match2[1] and match1[2] == match2[2]

	def _checkChangelogAndOutputSimilarity(self, fqn1, fqn2):
		SIMILARITY_REGEX = re.compile('L/hexcom/(.*?)/')
		return SIMILARITY_REGEX.match(fqn1).groups()[0] != SIMILARITY_REGEX.match(fqn2).groups()[0]

	def getPatchType(self, filePath):
		if '[B]' not in filePath and '[P]' not in filePath:
			if self.hasLanguageExtension(filePath):
				return PatchType.SOURCE
			elif self.CHANGELOG_TYPE_REGEX.match(filePath) != None:
				return PatchType.CHANGELOG
			elif self.OUTPUT_TYPE_REGEX.match(filePath) != None:
				return PatchType.OUTPUT
		return  None

	def getPathRelativeToVariant(self, fqn):
		return self.PATCH_HIERARCHY_REGEX.match(fqn).groups()[1]

	def getVariantName(self, fqn):
		return self.PATCH_HIERARCHY_REGEX.match(fqn).groups()[0]