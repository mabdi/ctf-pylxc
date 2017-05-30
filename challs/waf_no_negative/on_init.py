import lxc
from os.path import join, isfile, exists
import hashlib
import json
from distutils import dir_util
import pwd
import grp
import os
import subprocess   
LXC_NAME = "waf"
MAIN_FOLDER = "/var/www/ctf___0"
WEBROOT = "/var/www/html/waf"
SQL_FILE = "/var/www/mybank.sql"
TEAMSALT = "6a204bd89f3c8348af45a77c717a097a123"

def w_make_instance(arrr):
   result = make_instance(arrr[0],arrr[1],arrr[2],arrr[3])
   return result

def make_instance(team,pid,folder,team_folder):
   dest = WEBROOT + team_folder
   if exists(dest):
       return 10
   try:   
       dir_util.copy_tree(MAIN_FOLDER, dest )
       db_name = "waf"+team_folder
       with open(join(dest,"const.php")) as f:
         newText=f.read()
         newText=newText.replace("DBUSER_JA", "team_"+str(team) )
         newText=newText.replace("USER_PID_JA", pid )
         newText=newText.replace("USER_FOLDER_JA", team_folder )
       with open(join(dest,"const.php"), "w") as f:
         f.write( newText )
       subprocess.call("chown www-data:www-data "+dest+" -R", shell=True)
       print(dest,db_name)
       # run mysql query
       import pymysql
       db = pymysql.connect("localhost","root","3&?v]V6YaZQ6B$>b")
       cursor = db.cursor()
       cursor.execute("DROP  DATABASE  IF EXISTS "+db_name)
       cursor.execute("CREATE DATABASE IF NOT EXISTS `"+db_name+"` DEFAULT CHARACTER SET utf8 COLLATE utf8_general_ci;")
       cursor.execute("USE `"+db_name+"`;")
       cursor.execute("CREATE TABLE IF NOT EXISTS `accounts` ("\
              "`ID` varchar(100) NOT NULL,"\
              "`Name` varchar(100) NOT NULL,"\
              "`Address` varchar(100) NOT NULL,"\
              "`City` varchar(100) NOT NULL,"\
              "`Postal_code` varchar(100) NOT NULL,"\
              "`Phone` varchar(100) NOT NULL,"\
              "`mail` varchar(100) NOT NULL,"\
              "`Country` varchar(100) NOT NULL,"\
              "`password` varchar(100) NOT NULL,"\
              "`balance` varchar(100) NOT NULL ) ENGINE=InnoDB DEFAULT CHARSET=utf8;")
       #cursor.execute("CREATE USER 'team_"+team+"'@'localhost' IDENTIFIED BY '123456';")
       cursor.execute("GRANT ALL PRIVILEGES ON `"+db_name+"`.* To 'team_"+team+"'@'localhost' IDENTIFIED BY '123456';")   
       cursor.execute("FLUSH PRIVILEGES;")
       db.close()
   except:
      print("BOOM")
      import traceback
      print(traceback.format_exc())
      return 12
   
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
        10: {'stat': 1, 'msg':"already exists", 'data':{'redirect_to':"/waf" + team_folder}},
        11: {'stat': 1, 'msg':"done", 'data':{'redirect_to':"/waf" + team_folder}},
        12: {'stat': 0, 'msg':"err",'data':None}
   }[res]
