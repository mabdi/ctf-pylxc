#!/usr/bin/python3
from flask import Flask, request, Response, url_for
import imp
import json   
import os
import os.path  
import subprocess   
import code

app = Flask(__name__)
app.debug = True

def mk_response(stat,msg,data=None):
    #print(json.dumps({'stat':stat,'msg':msg,'data':data}))
    return json.dumps({'stat':stat,'msg':msg,'data':data})
    
def load_py(path):
    try:
        return imp.load_source(path[:-3], path)
    except FileNotFoundError:
        print("Problem grader for {} is offline.".format(path))    
		
		
@app.route("/api/onlevel", methods=['POST'])
def on_level():
     access_token = request.form.get('access_token', '').strip
     folders = request.form.get('folders', '').strip()
     pid = request.form.get('pid', '').strip()
     if not access_token:
        return mk_response(stat =0, msg = "access_denied")
     if not folders:
        return mk_response(stat = 0,msg ="درخواست نامعتبر")    
     if not pid:
        return mk_response(stat = 0,msg ="درخواست نامعتبر")
     path = "./challs/{}/on_level.py".format(pid)
     if not os.path.isfile(path):
        return mk_response(stat = 0,msg ="شماره سوال نامعتبر")    
     try:
        result = load_py(path).on_level(pid,folders)
        mk_response(stat =result['stat'],msg =result['msg'], data =result['data'])
     except:
        print("global Error") 
    
@app.route("/api/onteam", methods=['POST'])
def on_team():
     access_token = request.form.get('access_token', '').strip
     folder = request.form.get('folder', '').strip()
     pid = request.form.get('pid', '').strip()
     if not access_token:
        return mk_response(stat =0, msg = "access_denied")
     if not folder:
        return mk_response(stat = 0,msg ="درخواست نامعتبر")    
     if not pid:
        return mk_response(stat = 0,msg ="درخواست نامعتبر")
     path = "./challs/{}/on_team.py".format(pid)
     if not os.path.isfile(path):
        return mk_response(stat = 0,msg ="شماره سوال نامعتبر")    
     try:
        result = load_py(path).on_team(pid,folder)
        mk_response(stat =result['stat'],msg =result['msg'], data =result['data'])
     except:
        print("global Error") 

        
@app.route("/api/grade", methods=['POST'])
def grade_flag():
     folder = request.form.get('folder', '').strip()
     pid = request.form.get('pid', '').strip()
     key = request.files.get('file',None)
     flg = request.form.get('flag', '').strip()
     srcfold = ""
     if not folder:
        return mk_response(stat = 0,msg ="درخواست نامعتبر")
     if not pid:
        return mk_response(stat = 0,msg ="درخواست نامعتبر")
     path = "./challs/{}/grader.py".format(pid)
     if not os.path.isfile(path):
        return mk_response(stat = 0,msg ="شماره سوال نامعتبر")
     try:
        code.interact(local=locals()) 
        if key is not None:
           srcfold = "submits/" + folder + "/" + time.time()
           os.makedirs(srcfold)
           file = srcfold + "/submit_src.tar"
           key.save(file)
           cmd = "cd "+srcfold+" && tar -zxf submit_src.tar"
           subprocess.call(cmd, shell=True)
        result = load_py(path).grade(folder,pid,key,srcfold,flg)
        mk_response(stat =result['stat'],msg =result['msg'], data =result['data'])
     except:
        print("global Error") 
     
if __name__ == "__main__":
    app.run()
