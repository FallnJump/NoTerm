
    function setConsoleStr(ctl,ref,stln,cls=false){
        var tctl=0;
        var tbc=getConsoleStyleTable(ctl);
        if(tbc==null){
            tbc=setPreElem2Console(ctl);
            if(tbc==null){
                return;
            }
        }
        var pres=tbc.querySelectorAll("pre");
        var lnnumarr=pres[0].innerHTML.split("\n");
        var ctts=pres[1].innerHTML.split("\n");
        var curstln=lnnumarr[0].slice(0,-1)*1;
        var curedln=curstln+lnnumarr.length;
        var maxln=pres[1].getAttribute("data-lines");
        if(maxln==null){
            maxln=256;
        }
        
        var currdst=curstln*1;
        var reflna=ref.split("\n");
        stln=stln*1;
        var edln=reflna.length+stln;
        var res="";
        var newst;
        if(edln-stln>maxln){
            for(var i=0;i<maxln;i++){
                res+=reflna[i+edln-stln-maxln]+"\n";
            }
            res=res.slice(0,-1);
            if(stln>=0){
                stln=edln-maxln;
            }else{
                stln=0;
            }
            newst=stln;
        }else if(stln<curstln-maxln || edln>curedln+maxln || stln<0 || cls){
            res=ref;
            newst=Math.max(0,stln);
        }else{
            if(edln<curedln && stln+maxln<curedln){
                curedln=stln+maxln;
            }
            if(edln-maxln>curstln){
                currdst=edln-maxln;
            }
            var newed=Math.max(edln,curedln);
            newst=Math.min(stln,currdst);
            if(newed-newst>maxln){
                newst=newed-maxln;
            }
            res="";
            for(var n=newst;n<newed;n++){
                if(n>=stln && n<edln){
                    res+=reflna[n-stln];
                }else if(n>=curstln && n<=curedln){
                    res+=ctts[n-curstln];
                }
                if(n<newed-1){
                    res+="\n";
                }
            }
        }
        setPreElem2Console(tbc,newst,res);
    }
    function setConsoleStyle(ctl){
        
        ctl.style+="background-color:black;overflow:scroll;height:80px;";
        var tds=ctl.querySelectorAll("td");
        for(var i=0;i<2;i++){
            tds[0].style="align:left;vertical-align:top;";
        }
    }
    function getConsoleStyleTable(ctl){
        var tbc=ctl;
        while(tbc!=null){
            if(tbc.tagName=="TABLE") break;
            tbc=tbc.parentNode;
        }
        if(tbc.className!="ConsoleStyle") return null;
        return tbc;
    }
    function setPreElem2Console(prectl,defa=0,newstr=null)
    {
        var tbc=getConsoleStyleTable(prectl);
        if(tbc==null){
            if(prectl.tagName!="PRE"){
                return null;
            }
            swd=prectl.style.width;
            sht=prectl.style.height;
            prectl.style.width="";
            prectl.style.height="";
            
            var tbltempl=`<table class="ConsoleStyle" style="background-color:black;display:block;overflow:scroll;height:${sht};width:${swd};"><tr><td style="align:left;vertical-align:top;"><pre style="color:#007f7f;">0000:</pre></td><td style="color:#c0c0c0;align:left;vertical-align:top;" hidden></td><td style="color:#c0c0c0;align:left;vertical-align:top;"><pre></pre></td></tr></table>`;
            prectl.insertAdjacentHTML("afterend",tbltempl);
            var tbc=prectl.nextSibling;
            tbc.querySelectorAll("td")[1].appendChild(prectl);
            tbc=getConsoleStyleTable(prectl);
        }
        var pres=tbc.querySelectorAll("pre");
        if(newstr!=null){
            pres[1].innerHTML=newstr;
        }
        var lines=pres[1].innerHTML.split("\n").length;
        var lnstr="";
        for(var i=0;i<lines;i++){
            lnstr+=(Array(8).join("0")+(i*1+defa)).slice(-8)+":"+(i<lines-1?"\n":"");
        }
        pres[0].innerHTML=lnstr;
        
        pres[2].innerHTML=adopt_consolestyle(pres[1].innerHTML,[{},-1,-1]);
        return tbc;
    }
    function textstyle(){
        return [[],["font-weight","bold"],["font-weight","light"],["font-style","italic"],["text-decoration","underline"],["text-decoration","blink"],["text-decoration","blink"]];
    }
    function style2num(spanelem){
        var fgc=spanelem.style["color"];
        var bgc=spanelem.style["background-color"];
        var ts=textstyle();
        var dct={};
        for(var i=1;i<ts.length;i++){
            if(spanelem.style[ts[i][0]]==ts[i][0]){
                dct[i]=true;
            }
        }
        if(7 in dct){
            resn=[dct,bgc,fgc];
        }else{
            resn=[dct,fgc,bgc];
        }
        return resn;
    }
    function num2style(refn){
        var res0=textstyle();
        
        var res1=[[0,0,0],[3,0,0],[0,3,0],[3,3,0],[0,0,3],[3,0,3],[0,3,3],[3,3,3],[2,2,2],[4,0,0],[0,4,0],[4,4,0],[0,0,4]
            ,[4,0,4],[0,4,4],[4,4,4]]
        var sfc=[0,0x33,0x66,0x99,0xcc,0xff];
        var b=[(1 in refn[0]?2:1),2];
        
        var bgc=[0,0,0];
        var fgc=[0xc0,0xc0,0xc0];
        var cres=[fgc,bgc];
        for(var t=0;t<2;t++){
            var refc=refn[t+1];
            if((refc+"").slice(0,3)=="rgb"){
                rgbc=refc;
            }else{
                if(refc>=256 || refc<0){
                }else if(refc>=232){
                    var cc=refc-231;
                    var cw=cc*8;
                    cres[t]=[cw,cw,cw];
                }else if(refc>=16){
                    var cc=refc-16;
                    var cr=Math.floor(refc/36);
                    var cg=Math.floor(refc/6)%6;
                    var cb=refc%6;
                    cres[t]=[sfc[cr],sfc[cb],sfc[cg]];
                }else{
                    cres[t]=res1[refc];
                    for(var cc=0;cc<3;cc++){
                        cres[t][cc]*=64;
                    }
                }
                rgbc="rgb(";
                for(var cc=0;cc<3;cc++){
                    cres[t][cc]*=b[t];
                    if(cres[t][cc]>255) cres[t][cc]=255;
                    rgbc+=(cc>0?",":"")+cres[t][cc];
                }
                rgbc+=")";
            }
            cres[t]=rgbc;
        }
        
        var dct={};
        for(var i=1;i<7;i++){
            if(i in refn[0]){
                dct[res0[i][0]]=res0[i][1];
            }
        }
        var fgbg=["color","background-color"];
        if(7 in refn[0]){
            fgbg=[fgbg[1],fgbg[0]];
        }
        for(var i=0;i<2;i++){
            dct[fgbg[i]]=cres[i];
        }
        bal="";
        for(var k in dct){
            bal+=k+": "+dct[k]+";\n";
        };
        return bal;
    }
    function adopt_consolestyle(ref,refn){
        var re=/\x1b\[([\d\;]*)m/g;
        var refa=ref.replace(re,"\x1b\x1b$1\x1b\x1b").split("\x1b\x1b");
        var res=refa[0];
        var clssp="";
        for(var i=1;i<refa.length;i+=2){
            var spa=refa[i].split(";");
            var sps=clssp+"<span style=\"";
            var ssn=spa.length;

            for(var si=0;si<ssn;si++){
                var v=spa[si]*1;
                var q=Math.floor(v/10);
                if(v==0){
                    refn=[{},-1,-1];
                }else{
                    var t;
                    switch(q){
                        case 0:
                            t=0;
                            break;
                        case 3:
                            t=1
                            break;
                        case 4:
                            t=2;
                            break;
                        default:
                            t=-1;
                    }
                    if(t>=0){
                        var vv=v-q*10;
                        if(t>0 && vv==8 && si+2<ssn && spa[si+1]*1==5){
                            refn[t]=(spa[si+2]*1);
                        }else if(t>0 && vv<8){
                            refn[t]=vv;
                        }else if(t==0){
                            refn[t][vv]=true;
                        }else{
                            refn[t]=0;
                        }
                    }
                }
            }
            sps+=num2style(refn);
            res+=sps+"\">"+refa[i+1];
            clssp="</span>";
        }
        res+=clssp;
        return res;
    }

