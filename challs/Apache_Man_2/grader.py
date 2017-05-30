import time
import random
import lxc
import code
import string
from multiprocessing.pool import ThreadPool
import os
from os.path import join, isfile, exists
import json
 

LXC_BASE = "tmpl_apach"
MOUNTPOINT = "files"
LXC_IP = "10.10.13.7"

##### GRADER FUNCTIONS
import http.client
ip1 = '127.0.0.1'
ip2 = LXC_IP

    
def DisableSSLv3():
    import socket, ssl, pprint
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    # disable sslv3 and sslv2
    ssl_sock = ssl.wrap_socket(s, ssl_version=ssl.PROTOCOL_SSLv3, do_handshake_on_connect=False)
    try:
        ssl_sock.connect(('localhost', 443))
        ssl_sock.do_handshake()
        return False
    except:
        ssl_sock.close()
        # enable tlsv1
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        ssl_sock = ssl.wrap_socket(s, ssl_version=ssl.PROTOCOL_TLSv1, do_handshake_on_connect=False)
        try:
            ssl_sock.connect(('localhost', 443))
            ssl_sock.do_handshake()
            return True
        except:
            return False
            
            
def RestrictWeakSSLCiphers():
    import socket, ssl, pprint
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    # disable sslv3 and sslv2
    ciphers = "EXP:NULL:ADH:LOW:MD5:RC4"
    ssl_sock = ssl.wrap_socket(s, do_handshake_on_connect=False, ciphers=ciphers)
    try:
        ssl_sock.connect(('localhost', 443))
        ssl_sock.do_handshake()
        return False
    except:
        ssl_sock.close()
        # enable tlsv1
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        ssl_sock = ssl.wrap_socket(s, ssl_version=ssl.PROTOCOL_TLSv1, do_handshake_on_connect=False)
        try:
            ssl_sock.connect(('localhost', 443))
            ssl_sock.do_handshake()
            return True
        except:
            return False
            
            
            
def SetServerTokenToProd():
    try:
        ret = True
        conn = http.client.HTTPConnection("localhost")
        conn.request("GET","/")
        res = conn.getresponse()
        headers = res.getheaders()
        for header in headers:
            if(header[0].lower() == 'server' and (header[1].find('Ubuntu') != -1)):
                ret = False
    except:
        return False
    return ret
    
    
def SetServerSignatureToOff():
    try:
        ret = True
        conn = http.client.HTTPConnection("localhost")
        conn.request("GET","/")
        res = conn.getresponse()
        body = res.read()
        if(body.find('Apache') != -1):
                ret = False
    except:
        return False
    return ret

    
def DirectoryListing():
    try:
        ret = True
        conn = http.client.HTTPConnection("localhost")
        conn.request("GET","/DirectoryListing/")
        res = conn.getresponse()
        if(res.status == 200):
                return False

    except:
        return False
    return ret



##### END OF GRADER FUNCTIONS


def filter_submition(submition):
    for root, subdirs, files in os.walk(submition):
        for filename in files:
            if not (filename.endswith(".conf") or filename.endswith(".load") or  filename =="envvars" or  filename=="magic"):
                os.remove(join(root,filename))
                print("deleted",join(root,filename))

                
def run_test_body(): 
    # apache test syntax
    import subprocess
    cmd = "apachectl configtest"
    p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    res =str(p.stdout.read())
    retval = p.wait()
    if retval != 0:
       return {"stat":10,"msg":"`apachectl configtest` failed.",'data': {'stdio':res,'retval':retval}}  # stat: 10 cmd error
    print("ctl passed")
    # apache restart
    cmd = "service apache2 restart"
    p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    res =str(p.stdout.read())
    retval = p.wait()
    if retval != 0:
       return {"stat":10,"msg":"`service apache2 restart` failed.",'data': {'stdio':res,'retval':retval}}
    print("restart passed")
    # evals
    funcs = [
             ('DisableSSLv3', 20), \
             ('RestrictWeakSSLCiphers', 20), \
             ('SetServerTokenToProd', 20), \
             ('SetServerSignatureToOff', 20), \
             ('DirectoryListing', 20)]
    score = 0
    result = []
    max = 0
    for func in funcs:
        res = (func, False)
        max += func[1]
        if(globals()[func[0]]()):
            res = (func, True)
            score += func[1]
        result.append(res)
    if max == score:
        return {"stat":1,"msg":"VeryWell!",'data': {'stdio':'','retval':'','score':score,'result':result}}    # completely done
    else:
        return {"stat":2,"msg":"Try Harder.",'data': {'stdio':'','retval':'','score':score,'result':result}} # partially done
         

def run_test():
    #global ip2
    #ip2 = argz[0]
    res = run_test_body()
    with open("/files/result.txt","w") as f:
    #with open("/root/result.txt","w") as f:
          f.write(json.dumps(res))
    return 10
    
def thread_worker(child):
    child.start()
    child.wait("RUNNING", 15)
    if not child.running:
        return {"stat":0,"msg":"child cannot start.",'data': None}
    #child.attach_wait(lxc.attach_run_command, ["service", "networking", "restart"])
    #if not child.get_ips(timeout=15):
    #    return {"stat":0,"msg":"failed to get ip address of container",'data': None}
    #ip2 = child.get_ips()[0]
    
    child.attach_wait(lxc.attach_run_command, ["rm","-rf","/etc/apache2/conf-available*"])
    child.attach_wait(lxc.attach_run_command, ["rm","-rf","/etc/apache2/conf-enabled/*"])
    child.attach_wait(lxc.attach_run_command, ["rm","-rf","/etc/apache2/mods-available/*"])
    child.attach_wait(lxc.attach_run_command, ["rm","-rf","/etc/apache2/mods-enabled/*"])
    child.attach_wait(lxc.attach_run_command, ["rm","-rf","/etc/apache2/sites-available/*"])
    child.attach_wait(lxc.attach_run_command, ["rm","-rf","/etc/apache2/sites-enabled/*"])
    child.attach_wait(lxc.attach_run_command, ["cp","-r","/files/etc","/"])
    time.sleep(0.3)
    res = child.attach_wait(run_test)
    if(res >= 256):
       res = res / 256
    if(res == 10):
       child_root_fs = child.get_config_item('lxc.rootfs').split(':')[-1]
       return {"stat":200,"msg":"extract info file",'data': {'file':join(child_root_fs,"root","result.txt")}}
    else:
       return {"stat":0,"msg":"Illegal state",'data': None}
    
def grade(folder,pid,file,submition):
  try: 
    filter_submition(submition)
    base = lxc.Container(LXC_BASE)
    if not base.defined:
        print("Base is not defined.")
        return {"stat":0,"msg":"خطای سرور",'data': None}
    if base.running:
        print("Base container is running")
        return {"stat":0,"msg":"خطای سرور",'data': None}
    c_name = ''.join(random.SystemRandom().choice(string.ascii_uppercase + string.digits) for _ in range(16))
    child = lxc.Container(c_name)
    if not child.defined:
      try:
        child = base.clone(c_name, bdevtype="overlayfs",
              flags=lxc.LXC_CLONE_SNAPSHOT)
        child.append_config_item("lxc.mount.entry", submition +" "+ MOUNTPOINT + " none bind 0 0")
        #child.append_config_item("lxc.mount.entry", submition +"/etc/apache2 etc/apache2 none bind 0 0")
        child.save_config()
        pool = ThreadPool(processes=1)
        async_result = pool.apply_async(thread_worker, (child,))
        result = async_result.get(timeout=60)
        child.stop()
        if(result["stat"]==200):
           with open(join(submition,"result.txt")) as f:
           #with open(result["data"]["file"]) as f:
           
               jsonstr =f.read()
               jsonstr = json.loads(jsonstr)   
               result = jsonstr
               if result["stat"] == 1:                              
                    import hashlib
                    #team_folder = hashlib.md5(("6a204bd89f3c8348afd5c77c717a097a"+team).encode('utf-8')).hexdigest()
                    #flag = "infosec-" + hashlib.md5((folder + "infosec-3f51f45f424a61516b5cc8b6663d919c").encode('utf-8')).hexdigest()
                    flag = "infosec-3f51f45f424a61516b5cc8b6663d919c"
                    result["data"]["flag"] = flag
        #child.destroy()
        return result
      except Exception as inst:
        import traceback
        e = traceback.format_exc()
        return {"stat":0,"msg":"failed due exception",'data': {'exp': inst,'stack':e}}
      finally:
        #print(c_name)
        if child.running:#pass
           child.stop()
        child.destroy()
    else:
        return {"stat":0,"msg":"duplicate Name " + c_name,'data': None}
  except Exception as inst:
        return {"stat":0,"msg":"failed due exception",'data': {'exp': inst,'stack':e}}
