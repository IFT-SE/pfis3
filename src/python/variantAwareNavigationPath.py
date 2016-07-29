from navpath import NavigationPath

class VariantAwareNavigationPath(NavigationPath):

	def __init__(self, dbFilePath, langHelper, projectFolderPath, verbose = False):
		self.__variantAwareNavigations = []
		NavigationPath.__init__(self, dbFilePath, langHelper, projectFolderPath, verbose)
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
				prevNavToVariantPatch = self.__getNavToVariant(i)

				if prevNavToVariantPatch is not None:
					navTimeStamp = actualNav.toFileNav.timestamp
					nav.toFileNav = prevNavToVariantPatch.clone()
					# Cloning replaces entire nav, but we need to preserve timestamp for scent computation, etc.
					nav.toFileNav.timestamp = navTimeStamp

			self.__variantAwareNavigations.append(nav)

	def __getNavToVariant(self, navNumber):
		#If last nav is unknown, no way of knowing the actual location navigated to, so return None
		if navNumber == len(self._navigations)-1:
			return None

		#Actual location navigated to is fromNav of next Nav number
		actualLocNavigatedTo = self._navigations[navNumber+1].fromFileNav

		#See if any prior fromNav has a nav to a variant of the actual patch navigated to

		for i in range(navNumber-1, -1, -1):
			priorNav = self._navigations[i].fromFileNav
			if priorNav != None:
				if self.langHelper.isVariantOf(priorNav.methodFqn, actualLocNavigatedTo.methodFqn):
					return priorNav

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