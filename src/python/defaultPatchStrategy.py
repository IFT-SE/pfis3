from patches import MethodPatch
from patches import ChangelogPatch

class DefaultPatchStrategy(object):
	def __init__(self, langHelper):
		self.langHelper = langHelper

	def getPatchByFqn(self, fqn, files):
		# Query the known patches by a method's FQN. Returns the MethodData
		# object if it was found, or None if it wasn't. The MethodData object
		# can then be updated as necessary.
		norm = self.langHelper.normalize(fqn)

		# Get the outer class because the data structure is by file name
		norm = self.langHelper.getOuterClass(norm)

		if norm in files:
			# Return the method data object in the list that matches the desired FQN
			for patch in files[norm]:
				if patch.fqn == fqn:
					return patch
			return None

	def addPatchIfNotPresent(self, patchFqn, files, normalizedClass):
		if self.getPatchByFqn(patchFqn, files) is not None:
			return

		if self.langHelper.isMethodFqn(patchFqn):
			newPatch = MethodPatch(patchFqn)
		elif self.langHelper.isChangelogFqn(patchFqn):
			newPatch = ChangelogPatch(patchFqn)
		else:
			raise Exception("Not a patch fqn:", patchFqn)

		files[normalizedClass].append(newPatch)


