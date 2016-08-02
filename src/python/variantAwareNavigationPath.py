from navpath import NavigationPath

class VariantAwareNavigationPath(NavigationPath):

	def __init__(self, dbFilePath, langHelper, projectFolderPath, collapse = False, verbose = False):
		NavigationPath.__init__(self, dbFilePath, langHelper, projectFolderPath, verbose)
		self.collapse = collapse
		if self.collapse:
			self._name = NavigationPath.VARIANT_AWARE_COLLAPSED
		else:
			self._name = NavigationPath.VARIANT_AWARE

		self.__variantAwareNavigations = []
		self.__replaceNavsToUnknownToLastSeenVariant()
		self._printVariantAwareNavigations()

	# This method changes the way unknowns are handled for variant-aware algorithms
	# If programmer navigates to "Unknown", but he/she has seen a variant of this unknown location, then the nav is not entirely unknown
	# Here, we replace the to nav of "unknown" to the "to nav" of last seen variant of the same patch
	def __replaceNavsToUnknownToLastSeenVariant(self):
		for i in range(0, len(self._navigations)):
			actualNav = self._navigations[i]
			nav = actualNav.clone()

			if actualNav.isToUnknown():
				prevNavToVariantPatch = self.__getNavToPredictForUnseenButKnownNav(i)

				if prevNavToVariantPatch is not None:
					navTimeStamp = actualNav.toFileNav.timestamp
					nav.toFileNav = prevNavToVariantPatch.clone()
					# Cloning replaces entire nav, but we need to preserve timestamp for scent computation, etc.
					nav.toFileNav.timestamp = navTimeStamp

			self.__variantAwareNavigations.append(nav)

	def getPriorNavToSimilarPatchIfAny(self, unknownNavNumber):
		actualLocNavigatedTo = self._navigations[unknownNavNumber + 1].fromFileNav
		for i in range(unknownNavNumber - 1, -1, -1):
			priorNav = self._navigations[i].fromFileNav

			print "i", priorNav
			if priorNav != None:
				if self.langHelper.isVariantOf(priorNav.methodFqn, actualLocNavigatedTo.methodFqn):
					return priorNav
		return None

	def __getNavToPredictForUnseenButKnownNav(self, unknownNavNumber):
		#If last nav is unknown, no way of knowing the actual location navigated to, so return None
		if unknownNavNumber == len(self._navigations)-1:
			return None

		#Actual location navigated to is fromNav of next Nav number
		actualLocNavigatedTo = self._navigations[unknownNavNumber+1].fromFileNav

		#See if any prior fromNav has a nav to a variant of the actual patch navigated to
		for i in range(unknownNavNumber-1, -1, -1):
			priorNav = self._navigations[i].fromFileNav
			if priorNav != None:
				if self.langHelper.isVariantOf(priorNav.methodFqn, actualLocNavigatedTo.methodFqn):

					# If similar patch visited earlier, return the last visited one if collapsed.
					# This is because they will both be a single node.
					# If it is an uncollapsed model, the prior visited and actual location are two different nodes, even if they are exactly the same.
					# So return the actual location the programmer navigated to.

					if self.collapse == True:
						return priorNav
					else:
						return actualLocNavigatedTo

		return None

	def getLength(self):
		return len(self.__variantAwareNavigations)

	def getNavigation(self, i):
		return self.__variantAwareNavigations[i]

	def _printVariantAwareNavigations(self):
		print "--------------------------------------------"
		for i in range(len(self.__variantAwareNavigations)):
			navigation = self.__variantAwareNavigations[i]
			print '\t' + str(i) + ':\t' + str(navigation)
		print "--------------------------------------------"