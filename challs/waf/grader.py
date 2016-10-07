
import random
import lxc

LXC_BASE = "foo"
MOUNTPOINT = "home/usr/files"


def filter_submition(submition):
    pass

def run_test():
    pass

def thread_worker(child):
    child.start()
    child.wait("RUNNING", 15)
    if not child.running:
	    return {"status":0,"message":"child cannot start.",'data': None}
    if not child.get_ips(timeout=15):
	    return {"status":0,"message":"failed to get ip address of container",'data': None}
    res = child.attach_wait(run_test)
    return res

def grade(folder,pid,file,submition,txtflg):
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
        child = base.clone(c_name, bdevtype="overlayfs",
              flags=lxc.LXC_CLONE_SNAPSHOT)
        child.append_config_item("lxc.mount.entry",
            submition +" "+ MOUNTPOINT + " none bind 0 0")
        child.save_config()
        pool = ThreadPool(processes=1)
        async_result = pool.apply_async(thread_worker, (child))
        result = async_result.get(timeout=20)
        child.stop()
        child.destroy()
		return result
	else:
	    print("duplicate Name " + c_name);