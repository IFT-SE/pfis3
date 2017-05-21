from patches import *

class KnownPatches(object):
	# This class keeps track of the classes that the programmers "knows about."
	# It is used primarily to map from Text selection offset events to actual
	# methods.

	def __init__(self, languageHelper):
		self.langHelper = languageHelper
		self.files = {}

	def getPatchByFqn(self, fqn):
		# Query the known patches by a method's FQN. Returns the MethodData
		# object if it was found, or None if it wasn't. The MethodData object
		# can then be updated as necessary.
		norm = self.langHelper.normalize(fqn)

		# Get the outer class because the data structure is by file name
		norm = self.langHelper.getOuterClass(norm)

		if norm in self.files:
			# Return the method data object in the list that matches the desired FQN
			for patch in self.files[norm]:
				if patch.fqn == fqn:
					return patch
			return None

	def addFilePatch(self, filePathOrFqn):
		# Add a file to the known files. Each file is stored according to its
		# normalized path so that later when we query by FQN, we can quickly
		# retrieve a file's contents. This is because a normalized FQN should
		# match a normalized path if both are representing the same class.
		normalizedFqn = self.langHelper.normalize(filePathOrFqn)
		if normalizedFqn != '':
			# Get the outer class because the data structure is by file name
			normalizedFqn = self.langHelper.getOuterClass(normalizedFqn)

			# Set up the initial empty list if this is the first instance of the
			# file
			#TODO: Not inlined to handle edge case : files or classes with no methods
			if normalizedFqn not in self.files:
				self.files[normalizedFqn] = []

			# Add the patch if it doesn't already exist in the file
			self.addPatchIfNotPresent(filePathOrFqn, normalizedFqn)

	def addPatchIfNotPresent(self, patchFqn, normalizedClass):
		if self.getPatchByFqn(patchFqn) is not None:
			#Patch already exists!
			return

		if self.langHelper.isMethodFqn(patchFqn):
			newPatch = MethodPatch(patchFqn)
		elif self.langHelper.isChangelogFqn(patchFqn):
			newPatch = ChangelogPatch(patchFqn)
		elif self.langHelper.isOutputFqn(patchFqn):
			newPatch = OutputPatch(patchFqn)
		else:
			raise Exception("Not a patch fqn:", patchFqn)
		self.files[normalizedClass].append(newPatch)


	def findMethodByFqn(self, fqn):
		return self.getPatchByFqn(fqn)

	def findPatchByOffset(self, filePath, offset):
		# Query the known patches by an offset. If a method corresponds to this
		# offset in the given file, then its corresponding MethodData object is
		# returned, otherwise, None is returned.

		norm = self.langHelper.normalize(filePath)
		if norm == '' or norm not in self.files:
			return None
		patches = self.files[norm]

		if self.langHelper.getPatchType(norm) in (PatchType.CHANGELOG, PatchType.OUTPUT):
			# There is only one patch in these files, so just return it.
			# Don't do index computations
			return patches[0]

		elif self.langHelper.getPatchType(norm) == PatchType.SOURCE:
			surroundingMethods = [method for method in patches if method.isOffsetInMethod(offset)]

			if surroundingMethods is not None and len(surroundingMethods) > 0:
				sortedSurroundingMethods = sorted(surroundingMethods, key=lambda method:method.startOffset, reverse=True)
				return sortedSurroundingMethods[0]

		return None

	def getAdajecentMethods(self):
		# Returns a list of method lists where each inner list is the set of
		# methods in a file ordered by offset.
		adjacentMethodLists = []

		for norm in self.files:
			sortedMethods = sorted(self.files[norm], key=lambda method: method.startOffset)
			adjacentMethodLists.append(sortedMethods)

		return adjacentMethodLists

	def __str__(self):
		s = ''
		for norm in self.files:
			s += norm + '\n'
			for methodPatch in self.files[norm]:
				s += str(methodPatch) + '\n'

		return s
