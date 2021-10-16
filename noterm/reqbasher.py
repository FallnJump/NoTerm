import subprocess
from subprocess import PIPE
import sys
from io import TextIOWrapper, StringIO,BytesIO

class ReqBasher:
	def encode(self, refstr):
		return refstr.encode(self.enc, self.esc)
	
	def decode(self, refbin):
		return refbin.decode(self.enc, self.esc)
	
	def __init__(self):
		self.enc=sys.getfilesystemencoding()
		self.esc="surrogateescape"
		self.p = subprocess.Popen("sh",stdin=PIPE,stdout=PIPE,stderr=subprocess.STDOUT)
		self.tokenend="[next token]\n"
	
	def req(self,cmd):
		self.p.stdin.write(self.encode(cmd+"\n"))
		self.p.stdin.write(self.encode("echo "+self.tokenend))
		self.p.stdin.flush()
		resp=b""
		for b in self.p.stdout:
			if self.decode(b)==self.tokenend:
				break
			resp+=b
		return self.decode(resp)

if __name__=="__main__":
	rq=ReqBasher()
	print(rq.req("cat 34444.txt"))
	print(rq.req("ls"))
