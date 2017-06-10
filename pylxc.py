#!/usr/bin/python3
from flask import Flask, request, Response, url_for
import imp
import json   
import os
import os.path  
import subprocess   
import code
import time

app = Flask(__name__)
app.debug = True

ACCESS_TOKEN = open("access_token.txt").read().strip()

CHALLS = {
    "c9c3e050517cecff6c7bbc818d84ced7":"apach-test",
    "c06890c6a5cf80024298730171b29506":"waf",
	
	
	"4b6d4ba6317d03c0202b0286fe5e94aa":"Apache_Man_1",
	"3d6797f3aa1096b64f2f54609ce2f329":"Apache_Man_2",
	"7089fee1bb82b14ef441de2a6a73497f":"Apache_Man_3",
	"2f62165f107b5ea071016cc35e9990b2":"waf_no_negative",
}

def mk_response(stat,msg,data=None):
    return json.dumps({'stat':stat,'msg':msg,'data':data})
    
def load_py(path):
    try:
        return imp.load_source(path[:-3], path)
    except FileNotFoundError:
        print("Problem grader for {} is offline.".format(path))    

@app.route("/api/init", methods=['POST'])
def on_init():
     print('on_init')
     access_token = request.form.get('access_token', '').strip()
     folder = request.form.get('folder', '').strip()
     team = request.form.get('team', '').strip()
     pid = request.form.get('pid', '').strip()
     if not access_token or access_token != ACCESS_TOKEN:
        return mk_response(stat =0, msg = "access_denied")
     if not folder:
        return mk_response(stat = 0,msg ="درخواست نامعتبر")    
     if not team:
        return mk_response(stat = 0,msg ="درخواست نامعتبر")        
     if not pid:
        return mk_response(stat = 0,msg ="درخواست نامعتبر")
     pid = CHALLS[pid]
     path = "./challs/{}/on_init.py".format(pid)
     if not os.path.isfile(path):
        return mk_response(stat = 0,msg ="شماره سوال نامعتبر")    
     try:
        print(team,pid,folder)
        result = load_py(path).init(team,pid,folder)
        return mk_response(stat =result['stat'],msg =result['msg'], data =result['data'])
     except:
        print ("global Error") 
        import traceback
        print(traceback.format_exc())
        
        
@app.route("/api/grade", methods=['POST'])
def grade_flag(): 
     import time
     print('tic',time.time())
     folder = request.form.get('folder', '').strip()
     pid = request.form.get('pid', '').strip()
     key = request.files.get('file',None)
     srcfold = ""
     if not folder:
        return mk_response(stat = 0,msg ="درخواست نامعتبر")
     if not pid:
        return mk_response(stat = 0,msg ="درخواست نامعتبر")
     path = "./challs/{}/grader.py".format(pid)
     if not os.path.isfile(path):
        return mk_response(stat = 0,msg ="شماره سوال نامعتبر")
     try: 
        if key is not None:
           srcfold = "submits/{}/{}".format(folder,int(time.time()))
           os.makedirs(srcfold)
           file = srcfold + "/submit_src.tar"
           key.save(file)
           cmd = "cd "+srcfold+" && tar -zxf submit_src.tar"
           subprocess.call(cmd, shell=True)
           subprocess.call("cd "+srcfold+" && chmod o+w . -R", shell=True)
        result = load_py(path).grade(folder,pid,key,os.path.abspath(srcfold))
        print('toc',time.time(),result)
        return mk_response(stat =result['stat'],msg =result['msg'], data =result['data'])
     except:
        print ("global Error") 
        import traceback
        print(traceback.format_exc())
     
if __name__ == "__main__":
    app.run()
