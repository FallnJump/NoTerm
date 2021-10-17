import os
from glob2 import glob
import subprocess as spr
import threading as thrd
import datetime
import time

ProcList=dict()
ProcID=0
TraceOut=[]
BakLog=[]

class Piper():
	def __init__(self,isBinary=False):
		r,w=os.pipe()
		self.r_no=r
		self.w_no=w
		b="b" if isBinary else ""
		self.rs=os.fdopen(r,"r"+b)
		self.ws=os.fdopen(w,"w"+b)
	
	def put(self,data,withflush=True):
		self.ws.write(data)
		if withflush:
			self.ws.flush()
	
	def read(self,cnt=None):
		return self.rs.read(cnt)
	
	def close(self):
		if self.r_no is not None:
			os.close(self.r_no)
			os.close(self.w_no)
			self.r_no=None
			self.w_no=None

def force_make_rootpath(path):
	p=os.path.dirname(path)
	lst=[]
	while(True):
		if p==os.path.sep or p=="":
			break
		if os.path.exists(p):
			if not os.path.isdir(p):
				return False
			break
		p,q=os.path.split(p)
		lst.append(q)
	lst=lst[::-1]
	pp=p
	for t in lst:
		pp=os.path.join(pp,t)
		try:
			os.mkdir(pp)
		except OSError:
			return False
	return True

class MakeTree:
	def __init__(self,srcpath,destpath):
		self.srcpath=srcpath
		self.destpath=destpath
		
	def makemovelist_core(self,srcrp,destrp):
		itm=[srcrp,destrp]
		srcpath=os.path.join(self.srcpath,srcrp)
		if os.path.split(destrp)[1]=="":
			destrp+=os.path.basename(srcrp)
		destpath=os.path.join(self.destpath,destrp)
		if not os.path.exists(destpath):
			return [itm],[]
		if os.path.isdir(srcpath) and os.path.isdir(destpath):
			flist=[]
			flist+=glob(os.path.join(srcpath,"*"))
			reslist=[]
			exlist=[]
			for fl in flist:
				f=os.path.split(fl)[1]
				r,e=self.makemovelist_core(os.path.join(srcrp,f),os.path.join(destrp,""))
				reslist+=r
				exlist+=e
			reslist+=[(srcrp,"<rmdir>")]
		else:
			if os.path.isdir(srcpath):
				n=1
				while(True):
					destpathn=destpath+"."+str(n)
					if not os.path.exists(destpathn):
						itm=[srcpath,destpathn]
						return [itm],[]						
					n+=1
			else:
				reslist=[itm]
				exlist=[itm]
		return reslist,exlist

def makemovelist(srcpath,destpath, makeroot=False):
	
	if makeroot:
		d=force_make_rootpath(destpath)
		if not d:
			return False, "Failed to make root-directory: "+destpath+"\n"

	# fixing argument paths....
	srcpath=os.path.normpath(srcpath)
	if os.path.split(destpath)[1]=="":
		destpath+=os.path.basename(srcpath)
	destpath=os.path.normpath(destpath)
	srcpath=os.path.abspath(srcpath)
	destpath=os.path.abspath(destpath)
	cmn=os.path.commonpath((srcpath,destpath))

	#path check.
	drtp=os.path.dirname(destpath)
	if cmn==srcpath:
		# not allow reccurently moving
		return False, "reccurently moving occured\n"
	if (not os.path.exists(srcpath)) or (not os.path.exists(drtp)):
		return False, "root path is not founded!\n"
	srcdir,srcf=os.path.split(srcpath)
	destdir,destf=os.path.split(destpath)
	mk=MakeTree(srcdir,destdir)
	r=mk.makemovelist_core(srcf,destf)
	return True,(srcdir,destdir,r)

def makeshellscript(lst, iscopy=False):
	cmd=""
	srcrt,destrt=lst[0],lst[1]
	for li in lst[2][0]:
		if li[1]!="<rmdir>":
			if not iscopy:
				cope="mv"
			else:
				cope="cp -r"
			cmd+=cope+" "+os.path.join(srcrt,li[0])+" " + os.path.join(destrt,li[1]) + "\n"
		else:
			if not iscopy:
				cmd+="rmdir "+os.path.join(srcrt,li[0])
	return cmd

class Wrkpath:
	def __init__(self):
		self.wrk="."
	
	def getabspath(self,path):
		if path[0:4]=="..."+os.path.sep:
			respath=os.path.join(self.wrk,path[4:])
		else:
			respath=path
		respath=os.path.normpath(respath)
		respath=os.path.abspath(respath)
		self.wrk=os.path.dirname(respath)
		return respath

import atexit

def makecmd(cmd):
	return "echo \"<in>\"`pwd`$ \""+cmd+"\"\n"+cmd+"\necho\necho ***next***\n"


def getoutputlog(log_stline,log,n=-1):
	res=""
	if n<0:
		n+=len(log)+1
	n=max(0,len(log)-n)
	res=str(log_stline+n)+":"+str(log_stline+len(log))+"\n"
	for m in range(n,len(log)):
		res+=log[m]+"\n"
	return res

def getoutputlog_absline(log_stline,log,an):
	n=max(0,an-log_stline)
	return getoutputlog(log_stline,log,-1-n)

def GetProcLine(prockey,procitem):
	res=""
	for itm in procitem:
		sitm=str(itm)
		if isinstance(itm,datetime.datetime):
			sitm=sitm.split(".")[0]
		res+="|||"+sitm
	res+="|||(ended)|||ended."
	return res

class SubProcWrap:
	def __init__(self,tg,key,args):
		global ProcID,ProcList
		self.out=""
		self.status=""
		self._key="["+str(ProcID)+"]"+key
		self._stopflag=False
		self._proc=None
		self.stdresp=""
		self._sess=None
		ProcID+=1
		self._outputlog_stlines=0
		self.outputlog=[]
		self._outputlogcount=256
		self.lastque=""
		self.pp=None

		def tgwrap():
			global TraceOut,BakLog
			tg()
			self.close()
			self.status="ended."
			trc=self._key+GetProcLine(self._key,ProcList[self._key][:-1])+"\n-------- log start --------\n"+self.out+"<detail>\n"+self.getoutputlog(5)+"-------- log end --------\n"
			TraceOut=[trc]+TraceOut
			if len(TraceOut)>9:
				TraceOut=TraceOut[:-1]
			BakLog=BakLog[-10:]+[[self._key,self._outputlog_stlines,self.outputlog]]
			ProcList.pop(self._key)
		argforpl=args.split("\n")[0][:64]+"..." if type(args)==str else args
		ProcList[self._key]=(argforpl,datetime.datetime.now(),self)
		self._thr=thrd.Thread(target=tgwrap)
		self._thr.setDaemon(True)
		self._thr.start()
		atexit.register(self.stop)
		
	def changeoutputlogcount(self,newnum):
		self._outputlogcount=newnum

	def putoutputlog(self,line):
		self.outputlog.append(line)
		m=len(self.outputlog)-self._outputlogcount
		if m>0:
			self.outputlog=self.outputlog[m:]
			self._outputlog_stlines+=m
		
	def getoutputlog(self,n=-1):
		return getoutputlog(self._outputlog_stlines,self.outputlog,n)
		
	def getoutputlog_absline(self,an):
		return getoutputlog_absline(self._outputlog_stlines,self.outputlog,an)
	
	def trimlog(self):
		n=len(self.outputlog)-1
		while(n>=0):
			if self.outputlog[n]!="":
				break
		self.outputlog=self.outputlog[:n+1]

	def stop(self):
		self._stopflag=True
		if self._proc is not None and self._proc.poll() is None:
			self._proc.kill()
			self.pp.close()

	def is_alive(self):
		return self._thr.is_alive()
		
	def open(self,cmd="sh"):
		if self._proc is None:
			self.pp=Piper()
			self._proc=spr.Popen(cmd,shell=True,text=True,stdin=spr.PIPE,stdout=self.pp.ws,stderr=spr.DEVNULL)
	
	def quecmd(self,cmd):
			if self._proc is None or self._proc.poll() is not None:
				print("err> already finished.")
				return
			self.lastque=cmd
			if cmd[-1]!="\n":
				cmd+="\n"
			self._proc.stdin.write(cmd)
			self._proc.stdin.flush()

	def runcmd(self,cmd):
		self.status="processing <"+cmd+">"
		self.open()
		excmd=makecmd(cmd)
		self.quecmd(excmd)
		while(True):
			try:
				res=self.pp.rs.readline()
			except OSError:
				break
			if res=="***next***\n" or res=="":
				break
			self.putoutputlog(res[:-1])
		#self.trimlog()
		return not self._stopflag

	def close(self):
		if self._proc is not None:
			self._proc.terminate()
			self.pp.close()
			self._proc=None

def getProcList():
	res="Thread Name|||Args|||Start Time|||Running Time|||Status"
	nt=datetime.datetime.now()
	for k in ProcList:
		c=ProcList[k]
		res +="\n"+k+"|||"+str(c[0])+"|||"+str(c[1]).split(".")[0]+"|||"+str(nt-c[1]).split(".")[0]+"|||"+c[2].status
	return res

def getTraceLog():
	res=""
	for t in TraceOut:
		res+=t
	return res

def getStatusLog():
	res=str(len(ProcList))+"\n"
	res+=getProcList()
	res+="\n/////////////////////////////////\n"
	res+=getTraceLog()
	return res

class MoveFile(SubProcWrap):
	def __init__(self,arg,withchk,iscopy=False):
		self.arg=arg
		self.withchk=withchk
		self.iscopy=iscopy
		super().__init__(self.run_thread,"MoveFile",(self.arg,self.withchk))

	def run_thread(self):
		if 1:
			tokens=self.arg.split(";")
			srcwrk=Wrkpath()
			destwrk=Wrkpath()
			src=""
			errout=""
			self.status="estimate for moving files...."
			for token in tokens:
				errTemp="***Error from request "+token+">\n"
				tarr=token.split(":")
				if len(tarr)==1:
					errout+=errTemp+"Invalid Token.\n"
					continue
				srcp=srcwrk.getabspath(tarr[0])
				tg=tarr[1]
				if tg[-1]=="/":
					tg+=os.path.split(srcp)[1]
				destp=destwrk.getabspath(tg)
				res, lst=makemovelist(srcp,destp,not self.withchk)
				if not res:
					errout+=errTemp+lst
				elif self.withchk and len(lst[2][1])>0:
					errout+=errTemp
					for ls in lst[2][1]:
						errout+=ls[0]+"  -->  "+ls[1]+": dest path already exists.\n"
				#prs+=lst[2][0]
				if errout=="":
					src+=makeshellscript(lst,self.iscopy)
			if errout=="":
				lstarr=src.split("\n")
				for s in lstarr:
					if s =="":
						continue
					if not self.runcmd(""+s):
						break
				self.out=": Command is>\n"+src
				self.out=("STOP" if self._stopflag else "OK") + self.out
			else:
				self.out=errout
				errout_a=errout.split("\n")
				for ln in errout_a:
					self.putoutputlog(ln)

class ConvertMovie(SubProcWrap):
	def __init__(self,args):
		self.args=args
		super().__init__(self.run,"ConvMovie",args)
	
	def run(self):
		tokens=self.args.split(";")
		for t in tokens:
			a=t.split(":")
			if len(a)==1:
				src=a[0]
				dest=os.path.splitext(src)[0]+"_cvt.mp4"
			else:
				src,dest=a[:2]
			cmd="ffmpeg -i "+src+" -vcodec h264 -acodec mp3 "+dest
			if not self.runcmd(""+cmd):
				break
			self.out=str(self.stdresp)+"\n"

class DoCommand(SubProcWrap):
	def __init__(self,args,rawmode=False):
		self.args=args
		self._rawmode=rawmode
		super().__init__(self.run,"Cmd",args)
	
	def run(self):
		if not self._rawmode:
			arg=self.args.replace("%20"," ").replace("%9999%","\n")
		else:
			arg=self.args
		argtk=arg.split("\n")
		for t in argtk:
			if not self.runcmd(t):
				print(66555555555)
				break
			print(77766666666666666)
			self.out=str(self.stdresp)+"\n"

class InterCom(SubProcWrap):
	def __init__(self,taskName="Term"):
		self.args=""
		self.evt=thrd.Event()
		self.started=False
		super().__init__(self.run,taskName,"")
	
	def quecmd(self,cmd):
		lq=cmd
		m=0
		for m in range(0,len(lq)):
			if lq[-m-1]!="\n":
				break
		if m>0:
			lq=lq[:-m]
		if lq=="":
			lq="\n"
		super().quecmd(lq)
		lq=lq.split("\n")
		if len(lq)>1:
			lns="("+str(len(lq))+" lines)"
		else:
			lns=""
		self.status="last que=<"+lq[-1]+" "+lns+">"

	def run(self):
		self.putoutputlog("")
		self.open("script -q /dev/null")
		ends=False
		laststat=datetime.datetime.now()
		def para():
			while(True):
				laststat=datetime.datetime.now()
				try:
					rd=self.pp.read(1)
				except OSError:
					print("process finished. --loop aborted.")
					break
				if rd=="":
					break
				if rd=="\n":
					nn=min(len(self.outputlog),2)
					for n in range(nn):
						if self.outputlog[-n-1]!="\n":
							break
					if n < nn:
						self.putoutputlog("")
				else:
					if rd=="\x07":
						self.outputlog[-1]=""
					else:
						self.outputlog[-1]+=rd
			ends=True
		self.started=True
		th=thrd.Thread(target=para)
		th.setDaemon(True)
		th.start()
		while(True):
			dtime=datetime.datetime.now()-laststat
			if ends or self._stopflag or (self._proc.poll() is not None and int(dtime.seconds)>=0.5):
				break
			time.sleep(1.0)
		self.close()


def StopProc(key):
	if key in ProcList:
		ProcList[key][2].stop()

def GetLogOf(key,stline):
	if key in ProcList:
		return ProcList[key][2].getoutputlog_absline(stline)
	for bklg in BakLog:
		if bklg[0]==key:
			return getoutputlog_absline(bklg[1],bklg[2],stline)
	return "err>\nTask name: ["+key+"] is not running."


def SetCmd(key,arg):
	tne="err>\nTask name: ["+key+"] is "
	if key in ProcList:
		obj=ProcList[key][2]
		if isinstance(obj,InterCom):
			obj.quecmd(arg)
			return "ok"
		return tne+"not a interactive process."
	return tne +"not running."
