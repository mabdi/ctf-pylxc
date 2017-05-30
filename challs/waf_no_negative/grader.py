
import random
import lxc
import code
import string
from multiprocessing.pool import ThreadPool
import os
from os.path import join, isfile, exists
import json
 

LXC_BASE = "tmpl_waf"
MOUNTPOINT = "files"
LXC_IP = "10.10.13.7"

##### GRADER FUNCTIONS

##### END OF GRADER FUNCTIONS


def filter_submition(submition):
    for root, subdirs, files in os.walk(submition):
        for filename in files:
            if not (filename.endswith(".conf") or filename.endswith(".load") or  filename =="envvars" or  filename=="magic"):
                os.remove(join(root,filename))
                print("deleted",join(root,filename))

                
def run_test_body(): 
    return {"stat":1,"msg":"VeryWell!",'data': None}    # completely done


def run_test():
    #global ip2
    #ip2 = argz[0]
    # res = run_test_body()
    res = {"stat":0,"msg":"Not Implimented.",'data': None}
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