from navpath import NavigationPath

class PFIS_V_NavPath(NavigationPath):

	def __init__(self, dbFilePath, langHelper, projectFolderPath, overrides={}, verbose = False):
		NavigationPath.__init__(self, dbFilePath, langHelper, projectFolderPath, overrides, verbose)

		self._name = NavigationPath.PFIS_V
		self._variantAwareNavigations = []
		self._replaceNavsToUnknownToLastSeenVariant()
		self._printVariantAwareNavigations()

	# This method changes the way unknowns are handled for variant-aware algorithms
	# If programmer navigates to "Unknown", but he/she has seen a variant of this unknown location,
	# then the nav is not entirely unknown
	# Here, we replace the to nav of "unknown" to the "to nav" of last seen variant of the same patch
	def _replaceNavsToUnknownToLastSeenVariant(self):
		for i in range(0, len(self._navigations)):
			actualNav = self._navigations[i]
			variantAwareNav = actualNav.clone()

			if actualNav.isToUnknown():
				similarPatchSeen = self.__getSimilarKnownPatch(i)

				if similarPatchSeen is not None:
					#If similar patch seen, then the actual patch is "known". So, put it back in nav path.
					variantAwareNav.toFileNav.methodFqn = self._navigations[i + 1].fromFileNav.methodFqn

			self._variantAwareNavigations.append(variantAwareNav)

	def getPriorNavToSimilarPatchIfAny(self, unknownNavNumber):
		actualLocNavigatedTo = self._navigations[unknownNavNumber + 1].fromFileNav
		for i in range(unknownNavNumber, -1, -1):
			priorNav = self._navigations[i].fromFileNav
			if priorNav != None:
				if self.langHelper.isVariantOf(priorNav.methodFqn, actualLocNavigatedTo.methodFqn):
					return priorNav
		return None

	def __getSimilarKnownPatch(self, unknownNavNumber):
		#If last nav is unknown, no way of knowing the actual location navigated to, so return None
		if unknownNavNumber == len(self._navigations)-1:
			return None

		#Actual location navigated to is fromNav of next Nav number
		actualLocNavigatedTo = self._navigations[unknownNavNumber+1].fromFileNav

		#See if any prior fromNav has a nav to a variant of the actual patch navigated to
		for i in range(unknownNavNumber, -1, -1):
			priorNav = self._navigations[i].fromFileNav
			if priorNav != None:
				if self.langHelper.isVariantOf(priorNav.methodFqn, actualLocNavigatedTo.methodFqn):

					# If similar patch was visited earlier, do not return unknown.
					# Instead return the patch.
					return priorNav

		return None

	def getLength(self):
		return len(self._variantAwareNavigations)

	def getNavigation(self, i):
		return self._variantAwareNavigations[i]

	def _printVariantAwareNavigations(self):
		print "--------------------------------------------"
		for i in range(len(self._variantAwareNavigations)):
			navigation = self._variantAwareNavigations[i]
			print '\t' + str(i) + ':\t' + str(navigation)
		print "--------------------------------------------"