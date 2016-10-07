
import random
import lxc
import code
import string
from multiprocessing.pool import ThreadPool

LXC_BASE = "tmpl_apach"
MOUNTPOINT = "files"


def filter_submition(submition):
    pass

def run_test():
    print(3)
    return {"status":1,"message":"OK.",'data': None}

def thread_worker(child):
    child.start()
    print(1)
    child.wait("RUNNING", 15)
    if not child.running:
        return {"status":0,"message":"child cannot start.",'data': None}
    if not child.get_ips(timeout=15):
        return {"status":0,"message":"failed to get ip address of container",'data': None}
    print(2)
    res = child.attach_wait(run_test)
    print(4)
    return res

def grade(folder,pid,file,submition,txtflg):
    code.interact(local=locals())
    filter_submition(submition)
    base = lxc.Container(LXC_BASE)
    if not base.defined:
        print("Base is not defined.")
        return {"status":0,"message":"خطای سرور",'data': None}
    if base.running:
        print("Base container is running")
        return {"status":0,"message":"خطای سرور",'data': None}
    c_name = ''.join(random.SystemRandom().choice(string.ascii_uppercase + string.digits) for _ in range(16))
    child = lxc.Container(c_name)
    if not child.defined:
      try:
        child = base.clone(c_name, bdevtype="overlayfs",
              flags=lxc.LXC_CLONE_SNAPSHOT)
        child.append_config_item("lxc.mount.entry",
            submition +" "+ MOUNTPOINT + " none bind 0 0")
        child.save_config()
        pool = ThreadPool(processes=1)
        async_result = pool.apply_async(thread_worker, (child,))
        result = async_result.get(timeout=20)
        return result
      except Exception as inst:
        return {"status":0,"message":"failed due exception",'data': {'exp': inst}}
      finally:
        child.stop()
#        child.destroy()
    else:
        return {"status":0,"message":"duplicate Name " + c_name,'data': None}