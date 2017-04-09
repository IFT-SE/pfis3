import sqlite3
import re
import os
from defaultPatchStrategy import DefaultPatchStrategy
from patches import *

GET_VARIANT_POSITION_QUERY = 'select * from VARIANTS where NAME= ?'
FETCH_PATCH_FOR_FQN_QUERY = 'select vf.method, v1.name, v2.name, vf.body, vf.uuid from variants_to_functions as vf ' \
                            'join variants as v1 on vf.start = v1.num ' \
                            'join variants as v2 on vf.end=v2.num ' \
                            'where vf.method = ? and start <= ? and end >=?'

class VariantPatchStrategy(DefaultPatchStrategy):
	FILE_TARGET_REGEX = re.compile(r'L/hexcom/(.*?)/(.*)')

	def __init__(self, langHelper, variantsDb):
		DefaultPatchStrategy.__init__(self, langHelper)
		self.variantsDb = variantsDb
		self.idToPatchMap = {}
		self.fqnToIdMap = {}

	def addMethodPatchIfNotPresent(self, methodFqn, files, normalizedClass):
		#See patch for same FQN exists
		methodPatch = self.getMethodPatchByFqn(methodFqn, files)
		#Is patch for FQN does not exist, do the following
		if methodPatch is None:
			#Get a method patch, with appropriate ID
			methodPatch = self.__getNewlyVisitedPatch(methodFqn)

			self.__addPatchIfNotPresent(methodPatch, methodFqn, files, normalizedClass)

	def addChangelogPatchIfNotPresent(self, changelogFqn, files, normalizedClass):
		# See patch for same FQN exists
		changelogPatch = self.getMethodPatchByFqn(changelogFqn, files)

		if changelogPatch is None:
			changelogPatch = self.__getNewlyVisitedPatch(changelogFqn)

			self.__addPatchIfNotPresent(changelogPatch, changelogFqn, files, normalizedClass)

	def __addPatchIfNotPresent(self, patch, filePathOrFqn, files, normalizedClass):
		# If ID not exists earlier, ID -> Patch map
		if patch.uuid not in self.idToPatchMap.keys():
			self.idToPatchMap[patch.uuid] = patch

		# Add entry for FQN -> UUID
		self.fqnToIdMap[filePathOrFqn] = patch.uuid

		# Add to known patches for file
		if patch not in files[normalizedClass]:
			files[normalizedClass].append(patch)

	def __getNewlyVisitedPatch(self, methodFqn):
		if self.langHelper.isChangelogFqn(methodFqn):
			return ChangelogPatch(methodFqn)

		# If FQN is a file header, create a new header if it is not already available
		# Otherwise, get the right patch from varinat information db

		if self.langHelper.isPfigHeaderFqn(methodFqn):
			return MethodPatch(methodFqn)
		else:
			return self.__fetchMethodPatchFromDb(methodFqn)

	def getMethodPatchByFqn(self, fqn, files):
		if fqn in self.fqnToIdMap.keys():
			uuid = self.fqnToIdMap[fqn]
			return self.idToPatchMap[uuid]
		return None

	def __getPathRelativeToVariantFolder(self, fqn):
		if self.langHelper.isMethodFqn(fqn):
			return VariantPatchStrategy.FILE_TARGET_REGEX.match(fqn).groups()[1]

	def __getVariantName(self, fqn):
		if self.langHelper.isMethodFqn(fqn):
			return VariantPatchStrategy.FILE_TARGET_REGEX.match(fqn).groups()[0]

	def __fetchMethodPatchFromDb(self, fqn):
		patchRow = self.__getPatchRow(fqn)
		methodPatch = MethodPatch(fqn)
		methodPatch.uuid = patchRow[4]
		return methodPatch

	def __getPatchRow(self, fqn):

		pathRelativeToVariant = self.__getPathRelativeToVariantFolder(fqn)
		variantName = self.__getVariantName(fqn)

		if not os.path.exists(self.variantsDb):
			raise Exception("Db not found: ", self.variantsDb)

		conn = sqlite3.connect(self.variantsDb)

		if conn is None:
			raise Exception("Connection Error: ", self.variantsDb)

		c = conn.cursor()

		c.execute(GET_VARIANT_POSITION_QUERY, [variantName])
		variantNum = c.fetchone()[0]

		c.execute(FETCH_PATCH_FOR_FQN_QUERY, [pathRelativeToVariant, variantNum, variantNum])
		patchRow = c.fetchone()

		conn.close()

		return patchRow
