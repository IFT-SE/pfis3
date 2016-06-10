from patches import MethodPatch
class DefaultPatchStrategy(object):
	def __init__(self, langHelper):
		self.langHelper = langHelper

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

	def addMethodPatchIfNotPresent(self, methodFqn, files, normalizedClass):
		if self.getMethodPatchByFqn(methodFqn, files) is None:
			files[normalizedClass].append(MethodPatch(methodFqn))
