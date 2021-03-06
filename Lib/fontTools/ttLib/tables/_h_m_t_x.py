import sys
import DefaultTable
import array
from fontTools import ttLib
from fontTools.misc.textTools import safeEval
import warnings


class table__h_m_t_x(DefaultTable.DefaultTable):
	
	headerTag = 'hhea'
	advanceName = 'width'
	sideBearingName = 'lsb'
	numberOfMetricsName = 'numberOfHMetrics'
	
	def decompile(self, data, ttFont):
		numGlyphs = ttFont['maxp'].numGlyphs
		numberOfMetrics = int(getattr(ttFont[self.headerTag], self.numberOfMetricsName))
		if numberOfMetrics > numGlyphs:
			numberOfMetrics = numGlyphs # We warn later.
		# Note: advanceWidth is unsigned, but we read/write as signed.
		metrics = array.array("h", data[:4 * numberOfMetrics])
		if sys.byteorder <> "big":
			metrics.byteswap()
		data = data[4 * numberOfMetrics:]
		numberOfSideBearings = numGlyphs - numberOfMetrics
		sideBearings = array.array("h", data[:2 * numberOfSideBearings])
		data = data[2 * numberOfSideBearings:]

		if sys.byteorder <> "big":
			sideBearings.byteswap()
		if data:
			sys.stderr.write("too much data for hmtx/vmtx table\n")
		self.metrics = {}
		for i in range(numberOfMetrics):
			glyphName = ttFont.getGlyphName(i)
			self.metrics[glyphName] = list(metrics[i*2:i*2+2])
		lastAdvance = metrics[-2]
		for i in range(numberOfSideBearings):
			glyphName = ttFont.getGlyphName(i + numberOfMetrics)
			self.metrics[glyphName] = [lastAdvance, sideBearings[i]]
	
	def compile(self, ttFont):
		metrics = []
		for glyphName in ttFont.getGlyphOrder():
			metrics.append(self.metrics[glyphName])
		lastAdvance = metrics[-1][0]
		lastIndex = len(metrics)
		while metrics[lastIndex-2][0] == lastAdvance:
			lastIndex -= 1
			if lastIndex <= 1:
				# all advances are equal
				lastIndex = 1
				break
		additionalMetrics = metrics[lastIndex:]
		additionalMetrics = [sb for advance, sb in additionalMetrics]
		metrics = metrics[:lastIndex]
		setattr(ttFont[self.headerTag], self.numberOfMetricsName, len(metrics))
		
		metrics = sum(metrics,[])
		metrics = array.array("h", metrics)
		if sys.byteorder <> "big":
			metrics.byteswap()
		data = metrics.tostring()
		
		additionalMetrics = array.array("h", additionalMetrics)
		if sys.byteorder <> "big":
			additionalMetrics.byteswap()
		data = data + additionalMetrics.tostring()
		return data
	
	def toXML(self, writer, ttFont):
		names = self.metrics.keys()
		names.sort()
		for glyphName in names:
			advance, sb = self.metrics[glyphName]
			writer.simpletag("mtx", [
					("name", glyphName), 
					(self.advanceName, advance), 
					(self.sideBearingName, sb),
					])
			writer.newline()
	
	def fromXML(self, (name, attrs, content), ttFont):
		if not hasattr(self, "metrics"):
			self.metrics = {}
		if name == "mtx":
			self.metrics[attrs["name"]] = [safeEval(attrs[self.advanceName]), 
					safeEval(attrs[self.sideBearingName])]
	
	def __getitem__(self, glyphName):
		return self.metrics[glyphName]
	
	def __setitem__(self, glyphName, (advance, sb)):
		self.metrics[glyphName] = advance, sb

