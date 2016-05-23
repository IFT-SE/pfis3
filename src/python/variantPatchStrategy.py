import sqlite3
from defaultPatchStrategy import DefaultPatchStrategy
from patches import MethodPatch

class VariantPatchStrategy(DefaultPatchStrategy):

	def __init__(self, langHelper, variantsDb):
		DefaultPatchStrategy.__init__(self, langHelper)
		self.c = sqlite3.connect(variantsDb)
		self.idToPatchMap={}


	def addFilePatch(self, files, fileName):
		files[fileName] = []

	def addMethodPatchIfNotPresent(self, methodFqn, files, normalizedClass):
		#TODO:
		# if self.getMethodInMethodList(methodFqn, files, normalizedClass) is None:
		methodPatch = self.getMethodPatchByFqn(methodFqn, files)

		files[normalizedClass].append(MethodPatch(methodFqn))




