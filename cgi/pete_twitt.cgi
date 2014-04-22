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
# Define function to generate login HTML form.
def login_form():
  html="""
<HTML>
   <HEAD>
      <TITLE>Info Form</TITLE>
   </HEAD>
   <BODY BGCOLOR = white>
      <center>
         <H2>PictureShare User Administration</H2>
      </center>
      <H3>Type User and Password:</H3>
      <FORM METHOD=post ACTION="pete_twitt.cgi">
        <TABLE BORDER = 0>
            <TR>
               <TH>Username:</TH>
               <TD><INPUT TYPE=text NAME="username"></TD>
            <TR>
            <TR>
               <TH>Password:</TH>
               <TD><INPUT TYPE=password NAME="password"></TD>
            </TR>
        </TABLE>
        <INPUT TYPE=hidden NAME="action" VALUE="login">
        <INPUT TYPE="submit" VALUE="Log In">
      </FORM>
      
      <INPUT TYPE="submit" VALUE="Sign Up" 
        onclick="window.location='pete_twitt.cgi?action=signup';"/>
      
      
   </BODY>
</HTML>
"""
  print_html_content_type()
  print(html)
    

##############################################################
# Define function to generate signup HTML form.
def signup_form():
  html="""
<HTML>
   <HEAD>
      <TITLE>Sign Up Form</TITLE>
   </HEAD>
   <BODY BGCOLOR = white>
      <center>
         <H2>Sign Up</H2>
      </center>
      <H3>Type User Name and Password:</H3>
      <FORM METHOD=post ACTION="pete_twitt.cgi">
        <TABLE BORDER = 0>
            <TR>
               <TH>Username:</TH>
               <TD><INPUT TYPE=text NAME="username"></TD>
            <TR>
            <TR>
               <TH>First Name:</TH>
               <TD><INPUT TYPE=text NAME="firstname"></TD>
            <TR>
            <TR>
               <TH>Last Name:</TH>
               <TD><INPUT TYPE=text NAME="lastname"></TD>
            <TR>
            <TR>
               <TH>Email:</TH>
               <TD><INPUT TYPE=text NAME="email"></TD>
            <TR>
            <TR>
               <TH>Password:</TH>
               <TD><INPUT TYPE=password NAME="password"></TD>
            </TR>
        </TABLE>
        <INPUT TYPE=hidden NAME="action" VALUE="signup">
        <INPUT TYPE="submit" VALUE="Sign Up">
      </FORM>
      
      
   </BODY>
</HTML>
"""
  print_html_content_type()
  print(html)



###################################################################
# Define function to test the password.
def check_password(user, passwd):

  conn = sqlite3.connect(DATABASE)
  c = conn.cursor()

  t = (user,)
  c.execute('SELECT password FROM users WHERE handle=?', t)

  row = stored_password=c.fetchone()
  conn.close()

  if row != None: 
    stored_password=row[0]
    if (stored_password==passwd):
      return "passed"

  return "failed"

#################################################################
def get_tweets(user, session):
  html=""
  conn = sqlite3.connect(DATABASE)
  c = conn.cursor()

  c.execute('SELECT * FROM tweets ORDER BY tweetid DESC')
  rows =c.fetchall()
  
  for row in rows:
    if not is_on_feed(row[2], user):
      continue
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
        {6}
        by <a href="personal_page.cgi?user={4}&session={5}&target={0}">@{0}</a>
      </h3>
    """.format(row[2], row[5], row[6], row[1], user, session, time)
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
  return html

##############################################################
def handle_reply(form):
  replyto = form["tweetid"].value
  user = form["user"].value
  session = form["session"].value
  word = form["reply"].value

  conn = sqlite3.connect(DATABASE)
  c = conn.cursor()
  
  c.execute('SELECT COUNT(*) FROM tweets')
  row = c.fetchone()
  tweetid=row[0]

  timestamp = int(time.time())
  color=""
  font=""
  
  t = (tweetid, word, user, timestamp, replyto, color, font)
  if ("file" in form or word):
    c.execute('INSERT INTO tweets VALUES (?,?,?,?,?,?,?)', t)
    c.execute('SELECT owner, word FROM tweets WHERE tweetid={0}'.format(replyto))
    row = c.fetchone()
    owner = row[0]
    main_word = row[1]
    inbox_msg = "@{0} replied '{1}' to your tweet '{2}'".format(user, word, main_word)
    t = (owner, inbox_msg, 1)
    c.execute('INSERT INTO inbox VALUES (?,?,?)', t)
  conn.commit()
  conn.close()
  
  redirect_homepage(user, session)
    
##########################################################
def handle_retweet(form):
  tweetid = form["tweetid"].value
  user = form["user"].value
  session = form["session"].value
  
  conn = sqlite3.connect(DATABASE)
  c = conn.cursor()
  c.execute('SELECT COUNT(*) FROM tweets')
  row = c.fetchone()
  retweet_tweetid=row[0]
  
  c.execute("SELECT owner, word, color, font FROM tweets WHERE tweetid='{0}'".format(tweetid))
  row = c.fetchone()

  timestamp = int(time.time())
  replyto = -1
  
  retweet_word = "RT @" + row[0] + " " + row[1] 
  t = (retweet_tweetid, retweet_word, user, timestamp, replyto, row[2], row[3])
  c.execute('INSERT INTO tweets VALUES (?,?,?,?,?,?,?)', t)
  conn.commit()
  conn.close()
  
  redirect_homepage(user, session)
    
##########################################################
def is_on_feed(followee, follower):
  if followee == follower:
    return True
    
  conn = sqlite3.connect(DATABASE)
  c = conn.cursor()

  c.execute("SELECT * FROM relations WHERE followee='{0}' AND follower='{1}'".format(followee, follower))
  row = c.fetchone()
  conn.commit()
  conn.close()
  
  if row == None:
    return False
  else:
    return True

##########################################################
# Diplay the options of admin
def display_homepage(user, session):
  inbox_cnt = 0
  conn = sqlite3.connect(DATABASE)
  c = conn.cursor()
  c.execute("SELECT COUNT(*) FROM inbox WHERE owner='{0}';".format(user))
  row = c.fetchone()
  inbox_cnt = row[0]

  html="""
    <head>
    <title>Home
    </title>
    <meta http-equiv="refresh" content="15">
    </head>
    <form name="input" action="pete_twitt.cgi" method="post" enctype="multipart/form-data">
    Your tweet: <input type="text" name="tweets">
    Color: <input type="color" name="color">
    Font: <select name="font">
            <option value="Times New Roman">Times New Roman</option>
            <option value="courier">courier</option>
            <option value="arial">arial</option>
          </select>
    <br>
    <I>Browse Picture:</I> <INPUT TYPE="FILE" NAME="file">
    <input type="submit" value="Tweet It!">
    <INPUT TYPE=hidden NAME="action" VALUE="tweet">
    <INPUT TYPE=hidden NAME="user" VALUE="{0}">
    <INPUT TYPE=hidden NAME="session" VALUE="{1}">
    </form>
    <INPUT TYPE="submit" VALUE="Search" 
      onclick="window.location='search.cgi?user={0}&session={1}';"/>
    <a href='pete_twitt.cgi?action=inbox&user={0}&session={1}'>inbox({2})</a>
    """.format(user, session, inbox_cnt)
      #Also set a session number in a hidden field so the
      #cgi can check that the user has been authenticated
  html += get_tweets(user, session)
  html +="""
    <a href='pete_twitt.cgi?action=chpwd&username={user}&session={session}'>change password</a>
  """.format(user=user, session=session)
  
  print_html_content_type()
  print(html)
#################################################################

def chpwd(user, session): 
  html="""
    <HTML>
       <HEAD>
          <TITLE>Change Password</TITLE>
       </HEAD>
       <BODY BGCOLOR = white>
          <center>
             <H2>Change password</H2>
          </center>
          <H3>Type New Password:</H3>
          <FORM METHOD=post ACTION="pete_twitt.cgi?action=updatepwd&user={user}&session={session}">
            <TABLE BORDER = 0>
                <TR>
                   <TH>New Password:</TH>
                   <TD><INPUT TYPE=password NAME="password"></TD>
                <TR>
            </TABLE>
            <INPUT TYPE="submit" VALUE="Change">
          </FORM>
          
          
       </BODY>
    </HTML>
  """.format(user=user, session=session)
  
  print_html_content_type()
  print(html)
  
#################################################################

def updatepwd(form):
  if (session.check_session(form) != "passed"):
    login_form()
    return
  
  conn = sqlite3.connect(DATABASE)
  c = conn.cursor()
  
  username=form["user"].value
  password=form["password"].value
  sys.stderr.write("asdfasdfasd ======= " + password)
  c.execute("UPDATE users SET password='{0}' WHERE handle='{1}';".format(password, username))
 
  conn.commit()
  conn.close()
 
  html="""
  <!DOCTYPE HTML>
  <html lang="en-US">
      <head>
          <meta charset="UTF-8">
          <meta http-equiv="refresh" content="1; url=pete_twitt.cgi">
          <title>Page Redirection</title>
      </head>
  </html>
  """
  
  print_html_content_type()
  print(html)
  
  
#################################################################
def redirect_homepage(user, session):
  html="""
  <!DOCTYPE HTML>
  <html lang="en-US">
      <head>
          <meta charset="UTF-8">
          <meta http-equiv="refresh" content="1;
                url=pete_twitt.cgi?action=home&username={user}&session={session}">
          <script type="text/javascript">
              window.location.href = "pete_twitt.cgi?action=home&username={user}&session={session}"
          </script>
          <title>Page Redirection</title>
      </head>
      <body>
          <!-- Note: don't tell people to `click` the link, just tell them that it is a link. -->
          If you are not redirected automatically, follow the 
            <a href='pete_twitt.cgi?action=home&username={user}&session={session}'>home</a>
      </body>
  </html>
  """.format(user=user, session=session)
  
  print_html_content_type()
  print(html)
  

#################################################################
def create_new_session(user):
  return session.create_session(user)

##############################################################
def show_inbox(form):
  if "user" in form and "session" in form:
    user=form["user"].value
    session=form["session"].value
  else:
    login_form()
    return
  
  conn = sqlite3.connect(DATABASE)
  c = conn.cursor()
  c.execute("SELECT message FROM inbox WHERE owner='{0}'".format(user))
  rows = c.fetchall()
  html = """
      <html>
         <head>
             <title>Inbox</title>
         </head>
         <body bgcolor="white">
           <h3 style=\"text-align: center\">Inbox<h3>
           <div align="center">
               <a href="pete_twitt.cgi?username={user}&session={session}&action=home">
                 <img align="middle" src="http://i.imgur.com/HZfbZHs.jpg" alt=""  width="700" height="210">
               </a>
           </div>
  """.format(user=user, session=session)
  for row in rows:
    html += "<h3 style=\"text-align: center\">{0}<h3>".format(row[0])
  
  html +="""
    <h5 style=\"text-align: center\">
      <a href='pete_twitt.cgi?action=clrinbox&username={user}&session={session}'>
        Clear Inbox
      </a>
    <h5>
  """.format(user=user, session=session)
  
  html += "</body> </html>"
  print_html_content_type()
  print(html)
  
  conn.commit()
  conn.close()
  
##############################################################
def clrinbox(user, session):
  conn = sqlite3.connect(DATABASE)
  c = conn.cursor()
  c.execute("DELETE FROM inbox WHERE owner='{0}'".format(user))
  
  conn.commit()
  conn.close()
  redirect_homepage(user, session)
  
##############################################################
def add_tweets(form):
  conn = sqlite3.connect(DATABASE)
  c = conn.cursor()
  
  c.execute('SELECT COUNT(*) FROM tweets')
  row = c.fetchone()
  tweetid=row[0]
  
  timestamp = int(time.time())

  if "tweets" in form:
    word=form["tweets"].value
  else:
    word=""
  username=form["user"].value
  
  replyto=-1
  color=form["color"].value
  font=form["font"].value
  
  t = (tweetid, word, username, timestamp, replyto, color, font)
  if ("file" in form or word):
    c.execute('INSERT INTO tweets VALUES (?,?,?,?,?,?,?)', t)

  conn.commit()
  conn.close()
  if "file" in form:
    upload_pic_data(form, tweetid)

##############################################################
def new_tweet(form):
  #Check session
  if session.check_session(form) != "passed":
    return

  if "tweets" in form:
    word=form["tweets"].value
  else:
    word=""
    
  username=form["user"].value
  session_value=form["session"].value
  if word or ("file" in form and form['file'].filename):
    add_tweets(form)

  redirect_homepage(username, session_value)

##############################################################
def show_image(path):
  sys.stderr.write(path)
    
  # Read image
  with open(IMAGEPATH + path, 'rb') as content_file:
    content = content_file.read()

  # Send header and image content
  hdr = "Content-Type: image/jpeg\nContent-Length: %d\n\n" % len(content)
  print hdr+content

###############################################################################

def upload(form):
  if session.check_session(form) != "passed":
    login_form()
    return

  html="""
      <HTML>

      <FORM ACTION="pete_twitt.cgi" METHOD="POST" enctype="multipart/form-data">
          <input type="hidden" name="user" value="{user}">
          <input type="hidden" name="session" value="{session}">
          <input type="hidden" name="action" value="upload-pic-data">
          <BR><I>Browse Picture:</I> <INPUT TYPE="FILE" NAME="file">
          <br>
          <input type="submit" value="Press"> to upload the picture!
          </form>
      </HTML>
  """

  user=form["user"].value
  s=form["session"].value
  print_html_content_type()
  print(html.format(user=user,session=s))

#######################################################

def upload_pic_data(form, tweetid):
  #Check session is correct
  if (session.check_session(form) != "passed"):
    login_form()
    return

  fileInfo = form['file']
  user=form["user"].value
  s=form["session"].value

  # Check if the file was uploaded
  # sys.stderr.write(fileInfo.filename)
  
  if fileInfo.filename:
    sys.stderr.write("uploading pic.\n")
    # Remove directory path to extract name only
    fileName = os.path.basename(fileInfo.filename)
    
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute('SELECT COUNT(*) FROM pictures')
    row = c.fetchone()
    pic_cnt=row[0]
    
    path = str(pic_cnt) + '.jpg'
    
    t = (path, tweetid, user)
    c.execute('INSERT INTO pictures VALUES (?,?,?)', t)
    conn.commit()
    conn.close()
    
    open(IMAGEPATH + path, 'wb').write(fileInfo.file.read())
    
  else:
    sys.stderr.write("+++++++++++.\n")
    message = 'No file was uploaded'
    
    
##############################################################
def print_html_content_type():
  # Required header that tells the browser how to render the HTML.
  print("Content-Type: text/html\n\n")
  
##############################################################
def is_exist(username):
  conn = sqlite3.connect(DATABASE)
  c = conn.cursor()

  # Try to get old session
  t = (username,)
  c.execute('SELECT * FROM users WHERE email=?', t)
  row = c.fetchone()
  conn.commit()
  conn.close()
  if row == None:
    return False

  return True
  
##############################################################
def add_user(username, password, firstname, lastname, email):
  conn = sqlite3.connect(DATABASE)
  c = conn.cursor()

  # Try to get old session
  t = (username, email, firstname, lastname, password)
  c.execute('INSERT INTO users VALUES (?,?,?,?,?)', t)
  
  conn.commit()
  conn.close()

##############################################################
# Define main function.
def main():
  form = cgi.FieldStorage()
  if "action" in form:
    action=form["action"].value
    #print("action=",action)
    if action == "login":
      if "username" in form and "password" in form:
          #Test password
        username=form["username"].value
        password=form["password"].value
        if check_password(username, password)=="passed":
          session=create_new_session(username)
          redirect_homepage(username, session)
        else:
          login_form()
          print("<H3><font color=\"red\">Incorrect user/password</font></H3>")
      else:
        login_form()
    elif action == "tweet":
      sys.stderr.write("entering new tweet.\n")
      new_tweet(form)
    elif action == "reply":
      handle_reply(form)
    elif action == "retweet":
      handle_retweet(form)
    elif action == "show_image":
      path=form["path"].value
      show_image(path)
    elif action == "inbox":
      show_inbox(form)
    elif action == "home":
      if "username" in form and "session" in form:
        #Test password
        username=form["username"].value
        session=form["session"].value
        display_homepage(username, session)
      else:
        login_form()
    elif action == "signup":
      if "username" in form and "password" in form:
        username=form["username"].value
        password=form["password"].value
        firstname=""
        lastname=""
        email=""
        if "firstname" in form:
          firstname=form["firstname"].value
        if "lastname" in form:
          lastname=form["lastname"].value
        if "email" in form:
          email=form["email"].value
          
        if is_exist(username):
          signup_form()
          print("<H3><font color=\"red\">User name existed</font></H3>")
        else:
          add_user(username, password, firstname, lastname, email)
          login_form()
          print("<H3><font color=\"red\">please log in</font></H3>")
      else:
        signup_form()
    elif action == "clrinbox":
      if "username" in form and "session" in form:
        #Test password
        username=form["username"].value
        session=form["session"].value
        clrinbox(username, session)
      else:
        login_form()
    elif action == "chpwd":
      if "username" in form and "session" in form:
        #Test password
        username=form["username"].value
        session=form["session"].value
        chpwd(username, session)
      else:
        login_form()
    elif action == "updatepwd":
      updatepwd(form)
    else:
      login_form()
  else:
    login_form()

###############################################################
# Call main function.
main()
