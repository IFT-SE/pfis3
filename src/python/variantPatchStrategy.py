import sqlite3
import re
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
		print variantsDb
		self.variantsDb = variantsDb
		self.idToPatchMap={}


	def addFilePatch(self, files, fileName):
		files[fileName] = []

	def addMethodPatchIfNotPresent(self, methodFqn, files, normalizedClass):
		#TODO:
		# if self.getMethodInMethodList(methodFqn, files, normalizedClass) is None:

		methodPatch = self.getMethodPatchByFqn(methodFqn, files)

		if methodPatch is None:
			methodPatch = self.__getNewlyVisitedMethodPatch(methodFqn)

		if methodPatch not in files[normalizedClass]:
			files[normalizedClass].append(methodPatch)

	def __getNewlyVisitedMethodPatch(self, methodFqn):
		if self.langHelper.isPfigHeaderFqn(methodFqn):
			return MethodPatch(methodFqn)

		else:
			return self.__fetchMethodPatchFromDb(methodFqn)

	def getMethodPatchByFqn(self, fqn, files):
		# Query the known patches by a method's FQN. Returns the MethodData
		# object if it was found, or None if it wasn't. The MethodData object
		# can then be updated as necessary.
		norm = self.langHelper.normalize(fqn)

		# Get the outer class because the data structure is by file name
		norm = self.langHelper.getOuterClass(norm)

		if norm in files:
			# Return the method data object in the list that matches the desired FQN
			for method in files[norm]:
				if method.fqn == fqn:
					return method
			return None

		else:
			return None

	def _getMethodPatchByFqn_(self, fqn, files):
		patchRow = self.__getPatchRow(fqn)
		uuid = patchRow[4]
		if uuid in self.idToPatchMap:
			return self.idToPatchMap[uuid]
		else:
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
		methodPatch.variantInfo = VariantInfo(patchRow[0], patchRow[1], patchRow[2])

		self.idToPatchMap[methodPatch.uuid] = methodPatch

		return methodPatch

	def __getPatchRow(self, fqn):

		pathRelativeToVariant = self.__getPathRelativeToVariantFolder(fqn)
		variantName = self.__getVariantName(fqn)

		conn = sqlite3.connect(self.variantsDb)

		if conn is None:
			raise Exception("Db not found: ", self.variantsDb)

		c = conn.cursor()

		c.execute(GET_VARIANT_POSITION_QUERY, [variantName])
		variantNum = c.fetchone()[0]

		c.execute(FETCH_PATCH_FOR_FQN_QUERY, [pathRelativeToVariant, variantNum, variantNum])
		patchRow = c.fetchone()

		conn.close()

		return patchRow
