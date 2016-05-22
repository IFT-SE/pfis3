from defaultPatchStrategy import DefaultPatchStrategy

class VariantPatchStrategy(DefaultPatchStrategy):

	def __init__(self, variantsDb):
		print "Variant Strategy created!!!"
		self.variantsDb = variantsDb


