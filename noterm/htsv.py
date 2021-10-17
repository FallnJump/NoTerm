import http.server as srv
from .reqbasher import ReqBasher
import mimetypes
import os
import time
from io import BytesIO
import cv2
import numpy as np
import shutil
import sys
import re
from glob2 import glob
from .movefiler import MoveFile,ConvertMovie,getStatusLog,spr,DoCommand,StopProc,InterCom,SetCmd,GetLogOf

grqls=None
grq=None

class MyHdler(srv.BaseHTTPRequestHandler):
	DLM_NORM=0
	DLM_FORCE=1
	DLM_PARTIAL=2
	def __init__(self,a,b,c):
		global grq,grqls
		self.reqls = grqls
		self.req = grq
		self.enc=sys.getfilesystemencoding()
		self.esc="surrogateescape"
		self.chunksz=512*1024
		self.chunkspan=0.1
		self.maxlist=200
		self.thumb_size=(320,240)
		self.thumb_compress=75
		self.thumb_lsize=(1920,1280)
		self.thumb_lcompress=40
		self.reqrng=None
		super().__init__(a,b,c)
	
	def encode(self, refstr):
		return refstr.encode(self.enc, self.esc)

	def decode(self, refbin):
		return refbin.decode(self.enc, self.esc)
		
	def text2resp(self,restext):
		resbin=self.encode(restext)
		return BytesIO(resbin),len(resbin)

	def header_for_forcedl(self):
		self.send_header("Content-type", "application/octet-stream; chatset="+self.enc)
		self.send_header("Content-Diposition", "attachment")
	
	def header_for_text(self):
		self.send_header("Content-type", "text/html; chatset="+self.enc)

	def header_for_mime(self, p):
		self.send_header("Content-type", mimetypes.guess_type(p)[0])

	def send_content(self, fp, contlen):
		sended=0
		while(1):
			if sended>contlen:
				break
			bin=fp.read(self.chunksz)
			if sended+self.chunksz>contlen:
				bin=bin[:contlen-sended]
				sended=contlen
			else:
				sended+=self.chunksz
			if bin==b"":
				break
			try:
				self.wfile.write(bin)
			except BrokenPipeError:
				print("connection aborted")
				return
			self.wfile.flush()
			time.sleep(self.chunkspan)
		fp.close()

	def resp_reqfail(self):
		self.send_response(srv.HTTPStatus.BAD_REQUEST)
		self.end_headers()
	
	def resp_notfound(self):
		self.send_response(srv.HTTPStatus.NOT_FOUND)
		self.end_headers()

	def resp_ok(self):
		self.send_response(srv.HTTPStatus.OK)

	def get_ls_core(self, arg, exinfo):
		args=arg.split("?")
		if len(args)>1:
			sted=args[1].split("-")
			sted[0]=int(sted[0])
			sted[1]=int(sted[1])
		else:
			sted=None
		arg=args[0]
		res="ls>"
		rpwd=self.reqls.req("pwd")
		if not os.path.isdir(arg):
			dpt=os.path.split(arg)[0]
		else:
			dpt=arg
		dpt=os.path.join(dpt,"")
		cmd="ls -a --full-time " if exinfo else "ls -a "
		stofs=1 if exinfo else 0
		fcnt=self.reqls.req("ls -a -U1 "+arg+"|wc -l")[:-1]
		fcnt=int(fcnt)
		if sted is not None:
			tcmd="|head -n "+str(sted[1]+1+stofs)+"|tail -n "+str(sted[1]-sted[0]+1)
		else:
			tcmd=""
			sted=[0,fcnt]
		if sted[0]>fcnt-1:
			sted[0]=fcnt
		if sted[1]>=fcnt:
			sted[1]=fcnt-1
		rln=self.reqls.req(cmd+arg+tcmd)[:-1]
		errstr="ls:"
		if rln[:len(errstr)]==errstr:
			res="err>\n" + res
		rlns=rln.split("\n")
		res+=str(fcnt)+("/%d-%d" % (sted[0],sted[1]))+"\n"+dpt+"\n"
		#if sted is not None:
		#	rlns=rlns[sted[0]:sted[1]]
		for r in rlns:
			bw=False
			if exinfo:
				rtks=r.replace("\ ","\s").split(" ")
				rts=[]
				for rtk in rtks:
					if rtk !="":
						rts.append(rtk.replace("\s", "\ "))
				if len(rts)>=9:
					rts=[rts[8],rts[4],rts[5]+"_"+rts[6]]
					bw=True
			else:
				bw=True
				rts=[r]
			if bw:
				if os.path.isdir(dpt+rts[0]):
					rts[0]=os.path.join(rts[0],"")
				tg=""
				for rtt in rts:
					tg+=rtt+"|"
				tg=tg[:-1]
				res += tg + "\n"
		self.resp_ok()
		self.header_for_text()
		return res
	
	def get_ls(self, arg):
		res=self.get_ls_core(arg, False)
		return self.text2resp(res)
	
	def get_lsl(self,arg):
		res=self.get_ls_core(arg,True)
		return self.text2resp(res)
	
	def get_cmd(self, arg):
		res="cmd>\n"
		self.resp_ok()
		rpt=arg.replace("%20"," ")
		res+=self.req.req(rpt)
		self.header_for_text()
		resbin=self.encode(res)
		return BytesIO(resbin), len(resbin)
	
	def get_mv_core(self, arg, withchk, iscopy):
		res="move>\n"
		self.resp_ok()
		MoveFile(arg,withchk,iscopy)
		self.header_for_text()
		res+="OK"
		resbin=self.encode(res)
		return BytesIO(resbin), len(resbin)
	
	def get_status(self,arg):
		res=getStatusLog()
		self.resp_ok()
		self.header_for_text()
		resbin=self.encode(res)
		return BytesIO(resbin), len(resbin)
	
	def get_file(self, arg, dlmode=DLM_NORM):
		arg=arg.split("?")[0]
		if os.path.exists(arg) and os.path.isfile(arg):
			self.send_response(srv.HTTPStatus.OK if self.reqrng is None else srv.HTTPStatus.PARTIAL_CONTENT)
			if dlmode!=MyHdler.DLM_FORCE:
				self.header_for_mime(arg)
			else:
				self.header_for_forcedl()
			fp = open(arg, "rb")
			leng=os.path.getsize(arg)
			if self.reqrng is not None:
				lengl=min(leng-self.reqrng[0],self.chunksz)
				if self.reqrng[1]<0:
					self.reqrng[1]+=self.reqrng[0]+lengl
				self.reqrng.append(leng)
				fp.seek(self.reqrng[0])
				leng=self.reqrng[1]-self.reqrng[0]+1
			return fp, leng
		else:
			self.resp_notfound()
			return None,0
		
	def get_dl(self,arg):
		return self.get_file(arg, MyHdler.DLM_FORCE)

	def get_mime(self, arg):
		org=self.getorgbackfile(arg)
		if org[1]:
			arg=org[0]
		t=mimetypes.guess_type(arg)[0]
		if t is None:
			t="None/None"
		t+="//:"
		if not os.path.exists(arg):
			t+="-1"
		else:
			t+=str(os.path.getsize(arg))
		tbin=self.encode(t)
		self.send_response(srv.HTTPStatus.OK)
		return BytesIO(tbin),len(tbin)
		
	def getaspectedsize(self, im, sz):
		wh=im.shape[:2][::-1]
		aspx=sz[0]/wh[0]
		aspy=sz[1]/wh[1]
		asp=min(aspx,aspy)
		return round(wh[0]*asp), round(wh[1]*asp)
		
	def imread(self, arg, noenc=False):
		t=mimetypes.guess_type(arg)[0]
		raw_key="image/x-"
		if t[:len(raw_key)]==raw_key:
			#b=self.req.req("exiftool -jpgfromraw -b "+arg)
			p=spr.run("exiftool -jpgfromraw -b "+arg,shell=True,stdout=spr.PIPE)
			#b=p.stdout.read()
			#p.stdout.close()
			b=p.stdout
			if noenc:
				return b
			imbin=np.frombuffer(b,np.uint8)
			return cv2.imdecode(imbin, cv2.IMREAD_UNCHANGED)
		return cv2.imread(arg)
	
	def get_move(self, arg):
		return self.get_mv_core(arg,True, False)
	
	def get_forcemove(self, arg):
		return self.get_mv_core(arg,False, False)
	
	def get_copy(self, arg):
		return self.get_mv_core(arg,True, True)
	
	def get_forcecopy(self, arg):
		return self.get_mv_core(arg,False, True)
		
	
	def get_media_core(self,arg):
		arga=arg.split("|")
		ldtype=arga[1] if len(arga)>=2 else "r"
		arg=arga[0]
		if not os.path.exists(arg):
			return (None, 0), self.resp_notfound
		t=mimetypes.guess_type(arg)[0]
		t=[""] if t is None else t.split("/")
		if t[0]!="image" and t[0]!="video" and t[0]!="audio":
			return (None,0), self.resp_reqfail
		if ldtype=="r":
			return self.get_file(arg), None

		if ldtype=="c":
			if t[0]=="image":
				if t[1][:2]!="x-":
					return self.get_file(arg), None
				b=self.imread(arg, True)
				return (b, None), self.resp_ok
			elif t[0]=="video":
				if t[1]=="mp4" or t[1]=="quicktime" or t[1]=="ogg":
					return self.get_file(arg), None
				# convert to image.
		# thumbnail making.
		if t[0]=="audio":
			if ldtype=="c" and t[1]=="mpeg":
				return self.get_file(arg), None
			# not supported.
			return (None,0), self.resp_reqfail
		elif t[0]=="image":
			if ldtype=="c":
				if t[1][:2]!="x-":
					return self.get_file(arg), None
				b=self.imread(arg, True)
				return (b, None), self.resp_ok
			# load image.
			im=self.imread(arg, False)
		elif t[0]=="video":
			if ldtype=="c":
				if t[1]=="mp4" or t[1]=="quicktime" or t[1]=="ogg":
					return self.get_file(arg), None
				ldtype="b"
			# to image.
			vd=cv2.VideoCapture(arg)
			im=None
			if vd.isOpened():
				ct=vd.get(cv2.CAP_PROP_FRAME_COUNT)
				vd.set(cv2.CAP_PROP_POS_FRAMES, ct//10)
				rss,imtmp=vd.read()
				if rss:
					im=imtmp
				vd.release()
		else:
			return (None,0),self.resp_reqfail

		if ldtype=="b":
			sz,cmp=self.thumb_lsize,self.thumb_lcompress
		else:
			sz,cmp=self.thumb_size,self.thumb_compress
		sz=self.getaspectedsize(im,sz)
		im=cv2.resize(im, sz)
		opt=(cv2.IMWRITE_JPEG_QUALITY, cmp)
		_, b=cv2.imencode(".jpg", im, opt)
		return (b,None),self.resp_ok
	
	def get_media(self, arg):
		ct,respf=self.get_media_core(arg)
		if respf is not None:
			respf()
		if ct[1] is None:
			#print(ct[0])
			return BytesIO(ct[0]),len(ct[0])
		else:
			return ct
		
	def get_conv(self,arg):
		args=arg.split(";")
		flted=""
		for a in args:
			mmt=mimetypes.guess_type(a)[0]
			if mmt is not None and mmt.split("/")[0]=="video":
				flted+=a+";"
		if flted!="":
			flted=flted[:-1]
		if flted!="":
			ConvertMovie(flted)
		return self.get_status(arg)
	
	def make_thumbs(self, arg):
		def add_arg(destlist, srcrng, flag):
			for u in srcrng:
				if len(destlist) >= self.maxlist:
					return False
				destlist.append((flag, u))
			return True
			
		args=arg.split("?")
		arg=args[0]
		rln=self.reqls.req("ls "+arg)
		arg=os.path.join(arg,"")
		errstr="ls:"
		res="thumb>\n"
		res+=arg+"\n"
		if rln[:len(errstr)]==errstr:
			res="err>\n"
			self.resp_notfound()
			return None, 0
		rlns=rln.split("\n")[:-1]
		rln=[]
		for r in rlns:
			mmt=mimetypes.guess_type(arg+r)
			if mmt[0] is None:
				continue
			t=mmt[0].split("/")[0]
			if t == "image":
				rln.append((r,0))
			if t == "video":
				rln.append((r,1))
		rlns=rln
		bcnt=0
		flist=[]
		for o in args[1:]:
			if len(rlns)==0:
				continue
			kw=o[:1].lower()
			if kw=="b":
				t=int(o[1:])
				t=range(t,t+1)
				f=True
			elif kw=="l":
				t=int(o[1:])
				t=range(len(rlns)-t,len(rlns))
				f=False
			elif kw=="=" or kw=="$":
				t=o[1:]
				c=t.split("|")
				t=c[0]
				if len(c)==1:
					c=[0,0]
				else:
					c=c[1].split("-")
					if len(c)==1:
						c=[c[0],c[0]]
					for ci in range(2):
						if c[ci]=="":
							c[ci]=0
						else:
							c[ci]=int(c[ci])
				tt=None
				for ir in range(len(rln)):
					if t==rln[ir][0]:
						tt=ir
				if tt is None:
					continue
				st=max(0,min(len(rln),tt-c[0]))
				ed=max(0,min(len(rln),tt+c[1]+1))
				t=range(st,ed)
				f=(kw=="$")
			else:
				tse=o.split("-")
				if tse[1]=="":
					ed=len(rlns)
				else:
					ed=int(tse[1])+1
				if tse[0]=="":
					st=0
				else:
					st=int(tse[0])
				ed=max(0,min(len(rlns),ed))
				st=max(0,min(len(rlns),st))
				t=range(st, ed)
				f=False
			if not add_arg(flist, t, f):
				break
				
		thpath="thumbs"
		if os.path.exists(thpath):
			shutil.rmtree(thpath)
		os.mkdir(thpath)
		thpath=os.path.join(thpath, "")
		for n,t in enumerate(flist):
			fnm,tp=rlns[t[1]]
			if t[1]>=len(rlns):
				im = None
			else:
				if tp==0:
					im=self.imread(arg+fnm)
				elif tp==1:
					vd=cv2.VideoCapture(arg+fnm)
					im=None
					if vd.isOpened():
						ct=vd.get(cv2.CAP_PROP_FRAME_COUNT)
						vd.set(cv2.CAP_PROP_POS_FRAMES, ct//10)
						rss,imtmp=vd.read()
						if rss:
							im=imtmp
						vd.release()
				else:
					im=None
			if not im is None:
				if t[0]:
					# bigger thumb
					outfix="_prev"
					sz,cmp=self.thumb_lsize,self.thumb_lcompress
				else:
					outfix="_thumb"
					sz,cmp=self.thumb_size,self.thumb_compress
					# smaller thumb
				cmp=(cv2.IMWRITE_JPEG_QUALITY, cmp)
				sz=self.getaspectedsize(im,sz)
				imrs=cv2.resize(im, sz)
				outpath=thpath+str(n)+outfix+".jpg"
				cv2.imwrite(outpath, imrs, cmp)
				res += "#0|"+fnm+"|%d,%d|%d,%d|"%(im.shape[1],im.shape[0],sz[0],sz[1])+outpath+"\n"
		
		self.resp_ok()
		self.header_for_text()
		resbin=self.encode(res)
		return BytesIO(resbin), len(resbin)

	def dbg_headers(self):
		#print(hds.values(),hds.keys())
		hvals=self.headers.values()
		for n,key in enumerate(self.headers):
			print("|"+key+"|"+hvals[n]+"|")
		
	def makepath(self,arg):
		self.resp_ok()
		self.header_for_text()
		mkd=(arg[-1]=="/")
		if mkd:
			arg=arg[:-1]
		if os.path.exists(arg):
			res="err>\npath already exists."
		elif not os.path.exists(os.path.split(arg)[0]):
			res="err>\nrootdir does not exist."
		else:
			res="ok"
			if mkd:
				os.mkdir(arg)
			else:
				fp=open(arg,"w")
				fp.close()
		resbin=self.encode(res)
		return BytesIO(resbin), len(resbin)
	
	def do_comm(self,arg,rawmode=False):
		DoCommand(arg,rawmode)
		return self.get_status(arg)
	
	def simple_ok(self,arg=None):
		self.resp_ok()
		self.header_for_text()
		if arg is None:
			arg="ok"
		resbin=self.encode(arg)
		return BytesIO(resbin),len(resbin)
	
	def do_icomm(self,arg):
		InterCom()
		return self.simple_ok()
	
	def do_ique(self,arg):
		a=arg.index("|||")
		if a<0:
			return None
		key,ctt=arg[0:a],arg[a+3:]
		resp=SetCmd(key,ctt)
		return self.simple_ok(resp)
	
	def do_icmd_core(self,arg):
		a=arg.index("|||")
		if a<0:
			return None
		key,ctt=arg[0:a],arg[a+3:]
		tsk=InterCom(key)
		while(not tsk.started):
			time.sleep(0.5)
		tsk.quecmd(ctt)
		return self.simple_ok()
	
	def do_icmd(self,arg):
		return self.do_icmd_core(arg+"\nexit\n")
	
	def do_qcmd(self,arg):
		return self.do_icmd_core(arg)

	def do_ilog(self,arg):
		a=arg.index("|||")
		if a<0:
			return None
		key,ctt=arg[0:a],arg[a+3:]
		res=GetLogOf(key,int(ctt))
		self.resp_ok()
		self.header_for_text()
		resbin=self.encode(res)
		return BytesIO(resbin),len(resbin)
	
	def checkswap(self,topath):
		if os.path.exists(topath):
			i=0
			while(True):
				pt=topath+(".backup.%04d" % (i,))
				if not os.path.exists(pt):
					break
				i+=1
			return pt,"ok\nexisting file backuped."
		elif not os.path.exists(os.path.split(topath)[0]):
			return "<err>","err>\ndirectory does not exist."
		return "","ok"
	
	def getorgbackfile(self,arg):
		m=re.search(r"\.backup\.\d{4,}$",arg)
		if m is None:
			return arg,False
		return arg[:m.start()],True
		
	def do_swapbk(self,arg):
		orgfile=self.getorgbackfile(arg)
		if not orgfile[1]:
			# not backup file.
			return None
		res=self.checkswap(orgfile[0])
		if res[0]=="<err>":
			return None
		if res[0]!="":
			# since orgfile already exists,
			os.rename(orgfile[0],res[0])
		os.rename(arg,orgfile[0])
		return self.simple_ok()

	def killproc(self,arg):
		args=arg.split(";;;")
		for t in args:
			StopProc(t)
		return self.get_status(arg)
	
	def do_rename(self,arg):
		args=arg.split(":")
		if os.path.exists(args[1]):
			res="err>\ndest path: "+ args[1]+" already exists."
		elif not os.path.exists(args[0]):
			res="err>\ntarget path: "+ args[0] +" does not exist."
		else:
			res="ok"
			os.rename(args[0],args[1])
		return self.simple_ok(res)
	
	def get_Main(self,arg):
		#refpath=self.headers.get("referer")
		wrk=os.path.split(__file__)[0]
		host=self.headers.get("host")
		if arg=="" or arg[0]!="/":
			arg="/"+arg
		if os.path.exists(wrk+arg) and not os.path.isdir(wrk+arg):
				return self.get_file(wrk+arg)
		if arg!="/":
			return None
		htmlpath=wrk+"/tabletemplate.html"
		fp=open(htmlpath,"r")
		fltxt=fp.readlines()
		fp.close()
		#print(self.headers)
		if len(arg)==0 or arg[-1]!="/":
			arg+="/"

		keydom="var dom="
		resp=""
		b=True
		for i in range(len(fltxt)):
			if b and keydom in fltxt[i]:
				fltxt[i]=keydom+"\"http://"+host+"/\";\n"
				fltxt[i+1]="var initpath=\""+arg+"\";\n"
				b=False
				print(fltxt[i:i+2])
			resp+=fltxt[i]
		self.resp_ok()
		self.header_for_mime(htmlpath)
		resbin=self.encode(resp)
		return BytesIO(resbin),len(resbin)

	def do_GET(self):
		title = "HTTP Stub"
		rng=None
		hvals=self.headers.values()
		#print(self.dbg_headers())
		for n,key in enumerate(self.headers):
			if key=="Range":
				rng=hvals[n]
				rng=rng.split("bytes=")[1]
				rng=[rng.split("/")[0].split("-"),hvals[n]]
				break
		self.reqrng=[int(rng[0][0]),int(rng[0][1]) if rng[0][1]!="" else -1] if rng is not None else None
		pt=self.path
		pt=pt.split("????")[0]
		dlsla="/dl/"
		if pt[:len(dlsla)]==dlsla:
			pt="/dl?"+pt[len(dlsla):]
		if not "?" in pt:
			pt="/main?"+pt[1:]
		cmd_and_func= \
			[("ls", self.get_ls), ("cmd", self.do_comm),
			("file", self.get_file), ("dl", self.get_dl),
			("thumb", self.make_thumbs),
			("mime", self.get_mime),
			("move",self.get_move),
			("movef",self.get_forcemove),
			("lsl",self.get_lsl),
			("status",self.get_status),
			("media",self.get_media),
			("movcv",self.get_conv),
			("mkpath",self.makepath),
			("stop",self.killproc),
			("icmd_st",self.do_icomm),
			("icmd_que",self.do_ique),
			("icmd_log",self.do_ilog),
			("icmd",self.do_icmd),
			("swapbk",self.do_swapbk),
			("main",self.get_Main),
			("rename",self.do_rename)
			]
		strm=None
		for pair in cmd_and_func:
			op, arg=pt[:len(pair[0])+2], pt[len(pair[0])+2:]
			if op == "/" +pair[0]+"?":
				strm=pair[1](arg)
				break
		if strm is None:
			self.resp_reqfail()
			return
		if strm[0] is None:
			strm = None

		if strm is not None:
			self.send_header("Content-Length", str(strm[1]))
			if self.reqrng is not None:
				reshdbuf="bytes "+str(self.reqrng[0])+"-"+str(self.reqrng[1])+"/"+str(self.reqrng[2])
				self.send_header("Content-Range",
				reshdbuf)
			self.send_header("Access-Control-Allow-Origin","*")
		self.end_headers()
		if strm is None:
			return
		self.send_content(strm[0],strm[1])
		strm[0].close()

	def do_POST(self):
		lg=int(self.headers.get('content-length'))
		rpd=self.rfile.read(lg)
		opt="wb"
		tgopt,topath=self.path.split("????")[0].split("?")[:2]
		tgopt=tgopt[1:]
		flsave=True
		if tgopt=="move" or tgopt=="movef" or tgopt=="copy" or tgopt=="copyf":
			flsave=False
			rps=self.decode(rpd)
		elif tgopt=="cmd" or tgopt=="icmd" or tgopt=="qcmd":
			flsave=False
			rps=topath+"|||"+self.decode(rpd)
		elif "s" in tgopt:
			rps=self.decode(rpd)
			opt="w"
		elif "b" in tgopt:
			rps=rpd
		else:
			self.resp_reqfail()
			return
		if flsave:
			self.resp_ok()
			self.header_for_text()
			b=False
			frc=("f" in tgopt)
			if not frc:
				org=self.getorgbackfile(topath)
				if org[1]:
					# Evacuate the original file.
					swp=self.checkswap(org[0])
					if swp[0]!="<err>" and swp[0]!="":
						os.rename(org[0],swp[0])
						# save as original file.
						topath=org[0]
			res=self.checkswap(topath)
			if res[0]!="<err>":
				if res[0]!="" and not frc:
					os.rename(topath,res[0])
				fp=open(topath,opt)
				fp.write(rps)
				fp.close()
				if frc:
					res=[res[0],"ok"]
			resp=res[1]
			resp=self.encode(resp)
			strm=BytesIO(resp),len(resp)
		else:
			strm=None
			if tgopt=="cmd":
				strm=self.do_ique(rps)
			elif tgopt=="icmd":
				strm=self.do_icmd(rps)
			elif tgopt=="qcmd":
				strm=self.do_qcmd(rps)
			elif tgopt=="move":
				strm=self.get_move(rps)
			elif tgopt=="movef":
				strm=self.get_forcemove(rps)
			elif tgopt=="copy":
				strm=self.get_copy(rps)
			elif tgopt=="copyf":
				strm=self.get_forcecopy(rps)
		if strm is None:
			self.resp_reqfail()
			return
		self.send_header("Content-Length", str(strm[1]))
		self.send_header("Access-Control-Allow-Origin","*")
		self.end_headers()
		self.send_content(strm[0],strm[1])
		strm[0].close()

def RunServer(port, waitforever=True):
	global grq, grqls
	hd=srv.SimpleHTTPRequestHandler
	grq=ReqBasher()
	grqls=ReqBasher()
	hd=MyHdler
	sv=srv.HTTPServer(("",port),hd)
	if waitforever:
		sv.serve_forever()
	return sv

def clireq(url, req, data=None):
	if data is None:
		r=req.Request(url)
	else:
		r=req.Request(url,data=data,method="POST")
	with req.urlopen(r) as u:
		bres=b""
		while(1):
			b=u.read()
			if b==b"":
				break
			bres+=b
	return bres
