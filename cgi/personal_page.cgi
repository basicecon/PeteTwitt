#!/usr/bin/python

# Import the CGI, string, sys modules
import cgi, string, sys, os, re, random
import cgitb; cgitb.enable()  # for troubleshooting
import sqlite3
import session
import time
import datetime

#Get Databasedir
MYLOGIN="wang1247"
DATABASE="/homes/"+MYLOGIN+"/PeteTwitt/pete_twitt.db"
IMAGEPATH="/homes/"+MYLOGIN+"/PeteTwitt/images/"

##############################################################
def personal_homepage(user, target_user, session):
  html=""
  conn = sqlite3.connect(DATABASE)
  c = conn.cursor()

  c.execute("SELECT * FROM tweets WHERE owner='{0}' ORDER BY tweetid DESC".format(target_user))
  rows =c.fetchall()
  
  c.execute("SELECT firstname, lastname FROM users WHERE handle='{0}'".format(target_user))
  row = c.fetchone()
  
  html += """
    <h2>{2}'s Personal Homepage</h2>
    <h3>{0} {1} @{2}</h3>
  """.format(row[0], row[1], target_user)
  
  for row in rows:
    if row[4] != -1:
      continue
    c.execute('SELECT path FROM pictures WHERE tweetid = {0}'.format(row[0]))
    pic_row = c.fetchone()
    if pic_row:
      path = pic_row[0]
      image_url="pete_twitt.cgi?action=show_image&path={path}".format(path=path)
      html += '<image src="'+image_url+'" height="250" >'
      
    time = datetime.datetime.fromtimestamp(row[3]).strftime('%Y-%m-%d %H:%M:%S')
    messages="""
      <h3>
      <div style="color:{1}; font-family:'{2}'">{3}</div> 
      {4} by @{0}
      </h3>
    """.format(row[2], row[5], row[6], row[1], time)
    html += messages
    
    c.execute('SELECT word, owner FROM tweets WHERE replyto = {0} ORDER BY tweetid'.format(row[0]))
    replys = c.fetchall()
    for rrow in replys:
      rhtml = """
        <h4 style="text-indent: 20px;">
          @{0}  {1}
        </h4>
        """.format(rrow[1], rrow[0])
      html += rhtml
      
    reply_form = """
      <form action="pete_twitt.cgi" method=POST>
        <input type=hidden name="user" value={user}>
        <input type=hidden name="session" value={session}>
        <INPUT TYPE=hidden NAME="action" VALUE="reply">
        <input type=hidden name="tweetid" value={tid}>
        <input type=text size=50 name=reply>
        <input type=submit value="reply">
      </form>
      
    """.format(user=user, session=session, tid=row[0])
      
    retweet_button = """
      <INPUT TYPE="submit" VALUE="Retweet" 
      onclick="window.location='pete_twitt.cgi?user={0}&session={1}&action={2}&tweetid={3}';"/>
      <br>========================================<br>
      """.format(user, session, "retweet", row[0])
    
    html += reply_form
    html += retweet_button
    
  conn.close()
  print_html_content_type()
  print(html)  

##############################################################
def print_html_content_type():
  print("Content-Type: text/html\n\n")

  
############################################################## 
form = cgi.FieldStorage()
user=form["user"].value
session=form["session"].value
target_user=form["target"].value
personal_homepage(user, target_user, session)