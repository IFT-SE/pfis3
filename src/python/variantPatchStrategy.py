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

	def addPatchIfNotPresent(self, patchFqn, files, normalizedClass):
		# See patch for same FQN exists, else add
		if self.getPatchByFqn(patchFqn, files) is not None:
			return

		newPatch = self.__getNewlyVisitedPatch(patchFqn)
		files[normalizedClass].append(newPatch)

		#Update the patch details in fqn-id-node maps
		if newPatch.uuid not in self.idToPatchMap.keys():
			self.idToPatchMap[newPatch.uuid] = newPatch
		self.fqnToIdMap[patchFqn] = newPatch.uuid

	def __getNewlyVisitedPatch(self, patchFqn):
		if self.langHelper.isMethodFqn(patchFqn):
			newPatch = MethodPatch(patchFqn)

			# If it is an actual method patch (not PFIGHeader),
			# get the right patch UUID from the equivalence DB

			if not self.langHelper.isPfigHeaderFqn(patchFqn):
				self.__updatePatchUUIDFromEquivalenceDb(newPatch)

		elif self.langHelper.isChangelogFqn(patchFqn):
			newPatch = ChangelogPatch(patchFqn)

		else:
			raise Exception("Not a patch fqn:", patchFqn)
		return newPatch

	def getPatchByFqn(self, fqn, files):
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

	def __updatePatchUUIDFromEquivalenceDb(self, newPatch):
		patchRow = self.__getPatchRow(newPatch.fqn)
		newPatch.uuid = patchRow[4]


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
