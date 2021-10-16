from .htsv import RunServer
import sys as _sys
import argparse

def run():
	arg=argparse.ArgumentParser()
	arg.add_argument("--port",metavar="p",type=int,default=6666)
	cfg=arg.parse_args()
	RunServer(cfg.portnum)

exit()
if __name__=="__main__":
	if len(_sys.argv)<=1:
		portnum=6666
	else:
		portnum=int(_sys.argv[1])
	_sys.path.append(".")
	RunServer(portnum)
