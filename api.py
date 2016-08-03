from flask import Flask, request, Response, url_for
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, InvalidName
import string
import random
import http.client
import re
import urllib
import json
from werkzeug.datastructures import Headers
from werkzeug.exceptions import NotFound
import lxc
import shutil
import os
import crypt
import time
import subprocess
from multiprocessing.pool import ThreadPool
from distutils import dir_util
import sys
import code

app = Flask(__name__)
app.debug = True

__connection = None
__client = None

mongo_addr = "127.0.0.1"
mongo_port = 27017
mongo_db_name = "lxc"

HOST = "10.0.0.1:3444"
external_client = None
LXC_GRAND_PA = "000_grand_pa"
LXC_CODIAD_TMPLATE = "000_lxc_codiad"
LXC_JAVA_TMPLT = "000_lxc_java_tmpl"

CHALLS = {
   "pid1": {
        "src": "/challs/chal1",
        "ant": "/challs/chal1/ant"
   },
}
ips = {}

HTML_REGEX = re.compile(r'((?:src|action|href)=["\'])/')
JQUERY_REGEX = re.compile(r'(\$\.(?:get|post)\(["\'])/')
JS_LOCATION_REGEX = re.compile(r'((?:window|document)\.location.*=.*["\'])/')
CSS_REGEX = re.compile(r'(url\(["\']?)/')

REGEXES = [HTML_REGEX, JQUERY_REGEX, JS_LOCATION_REGEX, CSS_REGEX]

def get_conn():
    if external_client is not None:
        return external_client

    global __client, __connection
    if not __connection:
        try:
            __client = MongoClient(mongo_addr, mongo_port)
            __connection = __client[mongo_db_name]
        except ConnectionFailure:
            raise SevereInternalException("Could not connect to mongo database {} at {}:{}".format(mongo_db_name, mongo_addr, mongo_port))
        except InvalidName as error:
            raise SevereInternalException("Database {} is invalid! - {}".format(mongo_db_name, error))

    return __connection

def app_init():
   #print("checking template containers")
   if not lxc.Container( LXC_GRAND_PA ).defined:
     sys.exit("Root lxc is not defined.")
   if not lxc.Container( LXC_CODIAD_TMPLATE ).defined:
     print("Contaienr " + LXC_CODIAD_TMPLATE + " is not defined. ctreating ...")
     pa = lxc.Container(LXC_GRAND_PA)
     cod = pa.clone(LXC_CODIAD_TMPLATE, bdevtype="overlayfs",
                     flags=lxc.LXC_CLONE_SNAPSHOT)
     #cod.start()
     #cod.run "apt-get install apache2 php5 libapache2-mod-php5 php5-mcrypt git"
     #cod.run 
     # TODO

   if not lxc.Container( LXC_JAVA_TMPLT ).defined:
     print("Contaienr " + LXC_JAVA_TMPLT + " is not defined. ctreating ...")
     pa = lxc.Container(LXC_GRAND_PA)
     jav = pa.clone(LXC_JAVA_TMPLT, bdevtype="overlayfs",
                     flags=lxc.LXC_CLONE_SNAPSHOT)
     # TODO

   db = get_conn()
   print("loading ips")
   for entr in db.instances.find():
      lx = lxc.Container(entr["token"])
      if lx.defined:
         if lx.running:
           ips[entr["token"]] = lx.get_ips(family="inet",timeout=10)[0] #entr["ip"]
         else:
           lx.start()
           lx.wait("RUNNING", 10)
           if not lx.running:
              return (False,"child "+entr["token"]+" start. make sure you have `su - ctf` inside tmux and started the webservice")
           if not lx.get_ips(timeout=10):
              return (False, "failed to get ip address of container "+ entr["token"])
           ips[entr["token"]] = lx.get_ips(family="inet")[0]
         print("loaded: "+entr["token"]+"\tip:"+ips[entr["token"]])
      else:
         print("Container " + entr["token"] + " not found. removing from db.")
         db.instances.delete_one({"token":entr["token"]})



def create_lxc4pid(pid,token,passw):
  if pid not in CHALLS:
     return False,"problem is not added"
  prblm = CHALLS[pid]["src"]
  config_text = """<?php
	function getConfig() {
		return array(
			"zip-name" => $_SESSION['project']+"/submit_src.tar" ,
			"upload-webservice" => "https://%s/api/submit",
			"reset-webservice" => "https://%s/api/reset",
			"pid" => "%s",
			"token" => "%s",
		);
	}
?>""" % (HOST,HOST,pid,token)
  # make lxc
  base = lxc.Container(LXC_CODIAD_TMPLATE)
  if not base.defined:
    return (False,"Base Container \""+LXC_CODIAD_TMPLATE+"\" not exists")
  lxc2 = lxc.Container(token)
  if lxc2.defined:
     return (False,"Container \""+ token +"\" already exists")
  else:
   try:
     lxc2 = base.clone(token, bdevtype="overlayfs",
                     flags=lxc.LXC_CLONE_SNAPSHOT)
#     import code
#     code.interact(local=locals())
     # copy files to it
     srcfold = os.getcwd() + "/mnt/" + token + "/"
     if not os.path.exists(srcfold):
        os.makedirs(srcfold)
     f = open(srcfold + "cnf","w")
     f.write(config_text)
     f.close()
     dir_util.copy_tree(prblm, srcfold )
     lxc2.append_config_item("lxc.mount.entry", srcfold +" /home/ubuntu/src none bind 0 0")
     lxc2.save_config()
     lxc2.start()
     lxc2.wait("RUNNING", 10)
     if not lxc2.running:
       return (False,"child cannot start. make sure you have `su - ctf` inside tmux and started the webservice")
     if not lxc2.get_ips(timeout=10):
       return (False, "failed to get ip address of container")
     lxc_ips = lxc2.get_ips(family="inet")
     lxc2.attach_wait(lxc.attach_run_command, ["mv home/usr/src/cnf /var/www/html/plugins/ctf/config.php"])
     lxc2.attach_wait(lxc.attach_run_command, ["chown www-data:www-data -R /var/www/html/"])
     # change ubuntu password
     salt = ''.join(random.SystemRandom().choice(string.ascii_uppercase + string.digits) for _ in range(8))
     hashed = crypt.crypt(passw,"$6$"+salt)
     lxc2.attach_wait(lxc.attach_run_command, ["usermod", "-p", hashed, "ubuntu"])
     # grab ip
     ips[token] = lxc_ips[0]
     return (True,"Done.")
   except:
    print("Unexpected error:", sys.exc_info())
    container = lxc.Container(token)
    if container.defined:
      if container.running:
        if not container.shutdown(30):
          container.stop()
      lxc.Container(token).destroy()
    raise

@app.route("/w/backend/new", methods=['POST'])
def post_new():
    tid = request.form.get('tid', '')
    pid = request.form.get('pid', '')
    db = get_conn()
    inst = db.instances.find_one({"pid":pid,"tid":tid})
    if inst is None:
       token = ''.join(random.SystemRandom().choice(string.ascii_uppercase + string.digits) for _ in range(32))
       passw = ''.join(random.SystemRandom().choice(string.ascii_uppercase + string.digits) for _ in range(8))
       (stat,msg) = create_lxc4pid(pid,token,passw)
       if not stat:
          return "{\"status\":0,\"message\":\"" + msg	 + "\"}"
       ip = ips[token]
       inst = {
         'tid': tid,
         'pid': pid,
         'token': token,
#         'ip': ip,
         'password': passw
       }
       db.instances.insert(inst)
       return "{\"status\":1,\"token\":\"" + inst["token"] + "\", \"password\":\""+passw+"\"}"

# this function will run within the context of a container
def run_test():
    p = subprocess.Popen(["ant","compile"], cwd="/home/usr/files", stdout=subprocess.PIPE)
    if p.wait() != 0:
       return 40 #"compile failed"
    p = subprocess.Popen(["ant","test"], cwd="/home/usr/files", stdout=subprocess.PIPE)
    if p.wait() == 99:
       return 1
    return 0

def thread_worker(child):
    child.start()
    child.wait("RUNNING", 15)
    if not child.running:
        print("child cannot start. make sure you have `su - abdi` inside tmux and started the webservice")
    if not child.get_ips(timeout=15):
        print("failed to get ip address of container")
    res = child.attach_wait(run_test)
    if res > 256:
         res = res >>8
    return res

@app.route("/w/api/submit", methods=['POST'])
def post_submit():
  token = request.form.get('token', '')
  if(token in ips.keys()):
     pid = request.form.get('pid', '')
     key = request.files.get('file',None)
#     key_str = key.stream.read().decode("utf-8")
#     key.stream.seek(0)
#     hash = hashlib.md5(key_str.encode('utf-8')).hexdigest()
     global correct
     correct = False
     try:
        srcfold = "submits/" + token + "/" + time.time()
        os.makedirs(srcfold)
        file = srcfold + "/submit_src.tar"
        key.save(file)
        ant_file = CHALLS[pid]["ant"]
        shutil.copy(ant_file, srcfold )
        cmd = "cd "+srcfold+" && tar -zxf submit_src.tar"
        subprocess.call(cmd, shell=True)
        base = lxc.Container(LXC_JAVA_TMPLT)
        if not base.defined:
            print("Base is not defined.")
            return "{\"status\":0,\"message\":\"خطای سرور\"}"
        if base.running:
            print("Base container is running")
            return "{\"status\":0,\"message\":\"خطای سرور\"}"
        c_name = ''.join(random.SystemRandom().choice(string.ascii_uppercase + string.digits) for _ in range(16))
        child = lxc.Container(c_name)
        if not child.defined:
            child = base.clone(c_name, bdevtype="overlayfs",
                 flags=lxc.LXC_CLONE_SNAPSHOT)
            child.append_config_item("lxc.mount.entry",
                 srcfold +" home/usr/files none bind 0 0")
            child.save_config()
            pool = ThreadPool(processes=1)
            async_result = pool.apply_async(thread_worker, (child))
            child.stop()
            child.destroy()
        correct = async_result.get(timeout=20)
#        print(srcfold)
        if correct == 40:
            return "{\"status\":0,\"message\":\"کامپایل نشد\"}" # True, "درست است"
        elif correct == 1:
            return "{\"status\":1,\"message\":\"درست بود!\"}" #  False, "تلاش ناکافی!"
        else:
            return "{\"status\":0,\"message\":\"درست نبود\"}" #  False, "تلاش ناکافی!"
     except:
        print("global Error")
  else:
     return "{\"status\":0,\"message\":\"invalid token\"}"


@app.route("/w/api/reset", methods=['POST'])
def do_reset():
  token = request.form.get('token', '')
  if(token in ips.keys()):
    db = get_conn()
    inst = db.instances.find_one({"token":token})
    if inst is None:
      return "{\"status\":0,\"message\":\"invalid request\"}"
    tid = inst['tid']
    pid = inst['pid']
    (stat,msg) = create_lxc4pid(pid,token,inst['password'])
    ip = ips[name]
    #db.instances.update_one(
    #      { 'token': token },
    #      { "$set": { 'ip': ip }}
    #)
    if not stat:
       return "{\"status\":0,\"message\":\"" + msg + "\"}"
  else:
    return "{\"status\":0,\"message\":\"invalid token\"}"

def iterform(multidict):
    for key in multidict.keys():
        for value in multidict.getlist(key):
            yield (key.encode("utf8"), value.encode("utf8"))


# https://github.com/ziozzang/flask-as-http-proxy-server/blob/master/proxy.py
@app.route('/w/ide/<token>/', methods=["GET", "POST"])
@app.route('/w/ide/<token>/<path:file>', methods=["GET", "POST"])
def proxy_handler(token,file=""):
    if token not in ips:
      return "{\"status\":0,\"message\":\"Invalid token.\"}"
    ip = ips[token]
    request_headers = {}
    for h in ["Cookie", "Referer", "X-Csrf-Token","Content-Type"]:
        if h in request.headers:
            request_headers[h] = request.headers[h]
#    for h in request.headers:
    #for key, value in request.headers.to_list():
    #  request_headers[key] = value # request.headers[h]
    if request.query_string:
        path = "/%s?%s" % (file, request.query_string)
    else:
        path = "/" + file
    if request.method == "POST":
        form_data = list(iterform(request.form))
        form_data = urllib.parse.urlencode(form_data)
        request_headers["Content-Length"] = len(form_data)
    else:
        form_data = None
    conn = http.client.HTTPConnection(ip, 80)
#    code.interact(local=locals())
    conn.request(request.method, path, body=form_data, headers=request_headers)
    resp = conn.getresponse()
    # Clean up response headers for forwarding
    d = {}
    response_headers = Headers()
    for key, value in resp.getheaders():
        d[key.lower()] = value
        if key.lower() in ["content-length", "connection", "content-type"]:
            continue

        if key == "set-cookie":
            cookies = value.split(",")
            [response_headers.add(key, c) for c in cookies]
        else:
            response_headers.add(key, value)

    root = url_for(".proxy_handler", token=token,file=file)
    code.interact(local=locals())

    if "text/" in resp.getheader('content-type'):
        # Generic HTTP.  text/css text/javascript text/html
        contents = resp.read().decode("utf-8")
        for regex in REGEXES:
           contents = regex.sub(r'\1%s' % root, contents)
    else:
        contents = resp.read()

    response_headers.remove('Transfer-Encoding')
    response_headers.remove('Vary')
    #print(resp.status)
    flask_response = Response(response=contents,
                              status=resp.status,
                              headers= response_headers,
                              content_type=resp.getheader('content-type'))
    return flask_response

if __name__ == "__main__":
    app_init()
    app.run()
