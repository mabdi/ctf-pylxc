import lxc
from os.path import join, isfile, exists
import hashlib
import json
from distutils import dir_util
import pwd
import grp
import os

LXC_NAME = "waf"
MAIN_FOLDER = "/var/www/ctf___0"
MAIN_FOLDER2 = "/var/www/apach"
WEBROOT = "/var/www/html/waf"
TEAMSALT = "6a204bd89f3c8348afd5c77c717a097a"

def w_make_instance(arrr):
   result = make_instance(arrr[0],arrr[1],arrr[2],arrr[3])
   return result

def make_instance(team,pid,folder,team_folder):
   dest = WEBROOT + folder
   if not exists(dest):
       dir_util.copy_tree(MAIN_FOLDER, dest )
	   

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
