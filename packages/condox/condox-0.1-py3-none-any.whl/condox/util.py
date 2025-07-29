import os, magic
from cantools.util import sym, cmd, log
from cantools.util.data import hex2rgb
from condox import config

class ColorMap(object):
	def __init__(self):
		self.count = 0
		self.map = {}

	def __call__(self, rgbstr):
		if not rgbstr.startswith("rgb"):
			rgbstr = hex2rgb(rgbstr)
		if rgbstr not in self.map:
			self.log("registering", rgbstr)
			self.map[rgbstr] = "col%s"%(self.count,)
			self.count += 1
		return self.map[rgbstr]

	def log(self, *msg):
		log("ColorMap: %s"%(" ".join(msg),))

	def rule(self, rgbstr):
		return "\\definecolor{%s}{RGB}{%s}"%(self.map[rgbstr], rgbstr[4:-1])

	def definitions(self):
		return "\n".join([self.rule(rs) for rs in self.map.keys()])

colormap = ColorMap()

def symage(path):
	ext = magic.from_file(path).split(" ").pop(0).lower()
	if ext not in ["png", "jpeg"]:
		log("converting %s to png!"%(ext,))
		cmd("convert -append -alpha off %s %s.png"%(path, path))
		cmd("mv %s.png %s"%(path, path))
		ext = "png"
	sname = "%s.%s"%(path.replace("blob", "build"), ext)
	if not os.path.exists(sname):
		sym("../%s"%(path,), sname)
	return sname

def getstart(h, sflag):
	i = h.find(sflag)
	while h.find(sflag, i + 1) != -1:
		i = h.find(sflag, i + 1)
	return i

panflags = {}
def panflag(src, dest, flag=None, val=None):
	if src not in panflags:
		panflags[src] = {}
	if dest not in panflags[src]:
		panflags[src][dest] = {}
	pfz = panflags[src][dest]
	if not flag:
		return pfz
	if not val:
		return pfz.get(flag)
	pfz[flag] = val

def pan(fp, ex=None, srcex="html", opath=None):
	opath = opath or "%s.%s"%(fp, ex)
	cline = 'pandoc "%s.%s" -o "%s"'%(fp, srcex, opath)
	if config.builder.verbose:
		cline = "%s --verbose"%(cline,)
	pfz = panflag(srcex, ex)
	for k, v in pfz.items():
		cline = "%s -%s %s"%(cline, k, v)
	cmd(cline)
	return opath

def h2l(h, depth=0):
	from condox import trans
	if config.legacyh2l:
		return trans.legacy.h2l(h, depth)
	return trans.html2latex.H2L(h, depth).translate()

def h2x(h):
	from condox import trans
	return trans.html2docx.H2X(h).translate()