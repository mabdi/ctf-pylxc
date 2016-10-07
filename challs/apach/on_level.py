

import lxc
from os.path import join, isfile, exists

LXC_NAME = "waf"
MAIN_FOLDER = ""
WEBROOT = "/var/www/html/"

def make_instance(folder):
   dest = join(WEBROOT,folder)
   if exists(dest):
       return {'stat': 0, 'msg':"Already Exists", 'data':None}
   # copy folder
   dir_util.copy_tree(MAIN_FOLDER, dest )
   # run mysql query
   p = subprocess.Popen(["mysql","compile"], cwd="/home/usr/files", stdout=subprocess.PIPE)
   if p.wait() != 0:
      return {'stat': 0, 'msg':"mysql failed", 'data':None} #"mysql failed"
   return {'stat': 1, 'msg':"done", 'data':None}

def on_level(pid,folders):
   return {'stat': 1, 'msg':"every thing is awsome", 'data':None}
   # access lxc
   base = lxc.Container(LXC_NAME)
   if not base.defined:
      return {'stat': 0, 'msg':"container not defiend", 'data':None}
   if not base.running:
      return {'stat': 0, 'msg':"container not running", 'data':{'extra':"child cannot start. make sure you have `su - user` inside tmux and started the webservice"}}
   # run a function inside it
   ress = []
   for folder in folders:
       ress.append(base.attach_wait(make_instance,[folder]))
   # return response
   return {'stat': 1, 'msg':"done", 'data':ress}
