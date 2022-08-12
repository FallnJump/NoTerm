import sys as _sys
_sys.path.append(".")
from .htsv import RunServer
from .srvrun import run
__version__ = "0.0.7"

if __name__=="__main__":
	if len(_sys.argv)<=1:
		_portnum=6666
	else:
		_portnum=int(_sys.argv[1])
	
	RunServer(_portnum)
