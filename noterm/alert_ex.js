        var _alertoncef=0;
        var _altln="";
        var _altlnc=0;
        var _altsetting=[7,5];

        function alert0(inc,...args){
            if(_alertoncef<=_altsetting[0]){
                _altln+="\n";
                if(_altlnc%_altsetting[1]==0){
                    _altln="";
                }
                _altlnc+=inc;
                _altln+=`[${_altlnc}]:`;
                
                for(var i=0;i<args.length;i++){
                    _altln+=args[i]+" ";
                }
                if(_altlnc%_altsetting[1]==0){
                    alert(_altln);
                    _alertoncef++;
                }
            }
        }
        function alert1(...args){
            alert0(1,...args);
        }
        function alert2(...args){
            var inc =_altsetting[1]-(_altlnc % _altsetting[1]);
            alert0(inc,...args);
        }
        function alert1reset(alarmnum=7,alarmln=5){
            _altlnc=0;
            _altln="";
            _alertoncef=0;
            _altsetting=[alarmnum,alarmln];
        }
