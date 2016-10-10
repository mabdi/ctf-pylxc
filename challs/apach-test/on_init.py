import lxc
from os.path import join, isfile, exists
import hashlib
import json
from distutils import dir_util
import pwd
import grp
import os

LXC_NAME = "ide"
MAIN_FOLDER = "/var/www/ide000"
MAIN_FOLDER2 = "/var/www/apach"
WEBROOT = "/var/www/html/ide"
TEAMSALT = "6a204bd89f3c8348afd5c77c717a097a"

def w_make_instance(arrr):
   result = make_instance(arrr[0],arrr[1],arrr[2],arrr[3])
   return result

def make_instance(team,pid,folder,team_folder):
   dest = WEBROOT + team_folder
   if not exists(dest):
       # create a codiad
       dir_util.copy_tree(MAIN_FOLDER, dest )
       with open(join(dest,"config.php")) as f:
           newText=f.read()
           newText=newText.replace("BASE_PATH_JA", dest )
           newText=newText.replace("BASE_URL_JA", "ctf.behsazan.net/ide" + team_folder )
       with open(join(dest,"config.php"), "w") as f:
           f.write( newText )
   dest2 = join(dest,'workspace','apache')
   if exists(dest2):
      return 10
   # copy folder
   dir_util.copy_tree(MAIN_FOLDER2, dest2 )
   # update projects.php
   with open(join(dest,"data","projects.php")) as f:
       jsonstr =f.read()
       jsonstr = jsonstr[8:-5]
       jsonstr = json.loads(jsonstr)   
       jsonstr.append({'path':'apache','name':'apache'})
       jsonstr = json.dumps(jsonstr)
   with open(join(dest,"data","projects.php"), "w") as f:
       f.write( jsonstr )
   # update components/ctf/config.php   
   with open(join(dest,"components","ctf","config.php")) as f:
	   conf = f.read()
	   conf = conf.replace("PID_JA", pid )
	   conf = conf.replace("FOLDER_JA", folder )
   with open(join(dest,"components","ctf","config.php"), "w") as f:
       f.write( conf )
   uid = pwd.getpwnam("www-data").pw_uid
   gid = grp.getgrnam("www-data").gr_gid
   os.chown(dest, uid, gid)
   for root, dirs, files in os.walk(dest):  
     for momo in dirs:  
         os.chown(os.path.join(root, momo), uid, gid)
     for momo in files:
         os.chown(os.path.join(root, momo), uid, gid)

   return 11

def init(team,pid,folder):
   # access lxc
   base = lxc.Container(LXC_NAME)
   if not base.defined:
      return {'stat': 0, 'msg':"container not defiend", 'data':None}
   if not base.running:
      return {'stat': 0, 'msg':"container not running", 'data':{'extra':"child cannot start. make sure you have `su - user` inside tmux and started the webservice"}}
   # run a function inside it
   team_folder = hashlib.md5((TEAMSALT+team).encode('utf-8')).hexdigest()
   res = base.attach_wait(w_make_instance, [team, pid, folder, team_folder])
   # return response
   if res > 256:
       res = int(res / 256 )
   return {
        10: {'stat': 1, 'msg':"already exists", 'data':{'redirect_to':"/ide" + team_folder}},
        11: {'stat': 1, 'msg':"done", 'data':{'redirect_to':"/ide" + team_folder}},
   }[res]
