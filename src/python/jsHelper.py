from AbstractLanguageHelper import AbstractLanguageHelper
import os
import re
from patches import PatchType
from jsAdditionalDbProcessor import JSAdditionalDbProcessor


class JavaScriptHelper (AbstractLanguageHelper):

	JS_STD_LIB = 'LJS_Std_lib;.'
	REGEX_NORM_ECLIPSE = re.compile(r"L([^;]+).*")

	VARIANT_FQN_REGEX = re.compile(r'(L/hexcom/[^/]*)/*')
	FILE_FQN_REGEX = re.compile(r'L/hexcom/([^/]*)/([^/]*/)?(.*);$')
	CHANGELOG_FQN_REGEX = re.compile(r'L/hexcom/(.*?)/changes\.txt')
	OUTPUT_FQN_REGEX = re.compile(r'L/hexcom/(.*?)/index\.html\.output')
	METHOD_FQN_REGEX = re.compile(r'L/hexcom/([^/]*)/([^/]*/)?(.*\.js).*;\.(.*?)\(.*')
	#Groups are: Variant, folder+"/" if any, folder name in groups[1], file name, method name

	PATCH_HIERARCHY_REGEX = re.compile(r'L/hexcom/(.*?)/(.*)')

	def __init__(self):
		fileExtension = ".js"
		normalizedPathRegex = r"(.*)\.[js|txt|output]"
		packageRegex = r"(.*?)/[^/]*\.js.*"
		language = "JS"
		AbstractLanguageHelper.__init__(self, language, fileExtension, normalizedPathRegex, packageRegex)

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
		getNormalizedPatchContainerFqn = re.compile(r'(.*.js|.*.txt|.*.output).*')
		m = getNormalizedPatchContainerFqn.match(fqnToContainer)
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
		if self.OUTPUT_FQN_REGEX.match(filePathOrFqn) != None:
			return True
		return False

	def getFileName(self, projectFolderPath, className, extn):
		return os.path.join(projectFolderPath, className[1:])

	def isLibMethodWithoutSource(self, node):
		if node.startswith(self.JS_STD_LIB):
			return True
		elif ".min.js" in node:
			return True
		return False

	def performDBPostProcessing(self, db):
		JSAdditionalDbProcessor(db).process()

	def isVariantOf(self, fqn1, fqn2):
		# This will only take in valid FQNs for fqn1 and fqn2
		if self.isMethodFqn(fqn1) and self.isMethodFqn(fqn2):
			return self._checkMethodSimilarity(fqn1, fqn2)
		else:
			return self._checkSimilarityForNonMethodNodes(fqn1, fqn2)

	def _checkMethodSimilarity(self, fqn1, fqn2):
		# Check if fqns are from different variants, folder paths and method names.
		# Method names could have different parameters, but they are still similar.
		groups1 = self.METHOD_FQN_REGEX.match(fqn1).groups()
		groups2 = self.METHOD_FQN_REGEX.match(fqn2).groups()

		# Same FQN and method names, but different variant names
		differentVariants = groups1[0] != groups2[0]
		sameFqnRelativeToVariant = all([groups1[i] == groups2[i] for i in range(1, len(groups1))])
		return differentVariants and sameFqnRelativeToVariant

	def _checkSimilarityForNonMethodNodes(self, fqn1, fqn2):
		SIMILARITY_REGEX = re.compile('L/hexcom/(.*?)/(.*)')
		match1 = SIMILARITY_REGEX.match(fqn1)
		match2 = SIMILARITY_REGEX.match(fqn2)
		if match1 is not None and match2 is not None:
			groups1 = match1.groups()
			groups2 = match2.groups()
			return groups1[0] != groups2[0] and groups1[1] == groups2[1]
		return False

	def hasLanguageExtension(self, filePath):
		isJs = AbstractLanguageHelper.hasLanguageExtension(self, filePath)
		if isJs and ".min.js" not in filePath:
			return True
		return False

	def getPatchTypeForFile(self, filePath):
		CHANGELOG_FILE_REGEX = re.compile(r'(.*changes\.txt)')
		OUTPUT_FILE_REGEX = re.compile(r'(.*\.output)')
		if '[B]' not in filePath and '[P]' not in filePath:
			if self.hasLanguageExtension(filePath):
				return PatchType.METHOD
			elif CHANGELOG_FILE_REGEX.match(filePath) != None:
				return PatchType.CHANGELOG
			elif OUTPUT_FILE_REGEX.match(filePath) != None:
				return PatchType.OUTPUT
		return None

	def getPathRelativeToVariant(self, fqn):
		return self.PATCH_HIERARCHY_REGEX.match(fqn).groups()[1]

	def getVariantName(self, fqn):
		return self.PATCH_HIERARCHY_REGEX.match(fqn).groups()[0]

	def getVariantFqn(self, fqn):
		return self.VARIANT_FQN_REGEX.match(fqn).groups()[0]

	def isNavigablePatch(self, node):
		if self.isLibMethodWithoutSource(node):
			return False
		elif self.isMethodFqn(node) or self.isChangelogFqn(node) or self.isOutputFqn(node):
			return True
		return False

	def package(self, s):
		variantName = self.getVariantName(s)
		packageName = AbstractLanguageHelper.package(self, s)
		if packageName == '':
			return None
		elif packageName.endswith(variantName):
			return None
		return 'L'+ packageName

	def getPatchHierarchy(self, fqn):
		#Returns top-most to leaf node.
		if self.isMethodFqn(fqn):
			items = [self.getVariantFqn(fqn)]
			if self.package(fqn) is not None:
				items.append(self.package(fqn))
			items.append(self.fileFqn(fqn))
			items.append(fqn)
			return items
		else:
			startString = 'L/hexcom/'
			fqnFromVariant = fqn[fqn.index(startString) + len(startString):] + "/"
			separatorIndexes = [i for i, x in enumerate(fqnFromVariant) if x == '/']
			segments = [fqnFromVariant[:i] for i in separatorIndexes]
			hierarchy = [startString+s for s in segments]
			return hierarchy

	def fileFqn(self, fqn):
		return self.getOuterClass(fqn) + ";"

	def isFileFqn(self, fileFqn):
		return self.FILE_FQN_REGEX.match(fileFqn) is not None
