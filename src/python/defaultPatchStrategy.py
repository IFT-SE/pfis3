from patches import MethodPatch
class DefaultPatchStrategy(object):

	def addFilePatch(self, files, fileName):
		files[fileName] = []

	def getMethodInMethodList(self, methodFqn, files, fileName):
		# Return the method data object in the list that matches the desired FQN
		for method in files[fileName]:
			if method.fqn == methodFqn:
				return method
		return None

	def addMethodPatchIfNotPresent(self, methodFqn, files, normalizedClass):
		if self.getMethodInMethodList(methodFqn, files, normalizedClass) is None:
			files[normalizedClass].append(MethodPatch(methodFqn))
