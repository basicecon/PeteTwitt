#!/usr/bin/python

# Import the CGI, string, sys modules
import cgi, string, sys, os, re, random
import cgitb; cgitb.enable()  # for troubleshooting
import sqlite3
import session
import time

#Get Databasedir
MYLOGIN="wang1247"
DATABASE="/homes/"+MYLOGIN+"/PeteTwitt/pete_twitt.db"
IMAGEPATH="/homes/"+MYLOGIN+"/PeteTwitt/images/"


##############################################################
def print_html_content_type():
  # Required header that tells the browser how to render the HTML.
  print("Content-Type: text/html\n\n")
  
##############################################################
def search_page(form):
  sys.stderr.write("entering search page.\n")
  if session.check_session(form) != "passed":
    sys.stderr.write("didnt pass\n")
    return

  html="""
      <html>
      <head>
          <title>Twitt Search</title>
      </head>
      <body bgcolor="white">
          <h3 style="text-align: center">Search</h3>
          <div align="center">
              <a href="pete_twitt.cgi?username={user}&session={session}&action=home">
                <img align="middle" src="http://i.imgur.com/HZfbZHs.jpg" alt=""  width="700" height="210">
              </a>
          </div>
          <form style="text-align: center" action="search.cgi" method=GET>
            <input type=hidden name="user" value={user}>
            <input type=hidden name="session" value={session}>
            <input type=text size=50 name=query>
            <select name="type">
              <option value="name">user name</option>
              <option value="tweet">tweet</option>
            </select>
            <input type=submit value="search">
          </form>
      
  """
  
  if "query" in form:
    searchQuery=form["query"].value
    if searchQuery:
      searchType=form["type"].value
      if searchType == "name":
        html += find_names(form)
      else:
        html += find_tweets(searchQuery)
  
  html += "</body>"
  html += "</html>"
  user=form["user"].value
  s=form["session"].value
  print_html_content_type()
  print(html.format(user=user,session=s))

##############################################################
def find_names(form):
  html = ""
  conn = sqlite3.connect(DATABASE)
  c = conn.cursor()

  user=form["user"].value
  session=form["session"].value
  query=form["query"].value
  searchType=form["type"].value
  
  # Try to get old session
  c.execute('''SELECT firstname, lastname, handle FROM users WHERE handle LIKE '{query}' OR firstname LIKE '{query}'
               OR lastname LIKE '{query}' OR email LIKE '{query}'
            '''.format(query=query))
  rows = c.fetchall()
  for row in rows:
    if row[2] == user:
      button = ""
    elif is_following(row[2], user):
      button="""
        <INPUT TYPE="submit" VALUE="Unfollow" 
        onclick="window.location='search.cgi?user={0}&session={1}&query={2}&type={3}&action={4}&followee={5}';"/>
      """.format(user, session, query, searchType, "unfollow", row[2])
    else:
      button="""
        <INPUT TYPE="submit" VALUE="Follow" 
        onclick="window.location='search.cgi?user={0}&session={1}&query={2}&type={3}&action={4}&followee={5}';"/>
      """.format(user, session, query, searchType, "follow", row[2])
      
    messages="""
      <h3>{3} {0} {1} @{2}</h3>
    """.format(row[0], row[1], row[2], button)
    html += messages
    
  
  conn.close()
  return html
  
##############################################################
def is_following(followee, follower):
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

##############################################################
def find_tweets(query):
  html = ""
  conn = sqlite3.connect(DATABASE)
  c = conn.cursor()

  c.execute("""SELECT * FROM tweets WHERE word LIKE '% {query} %' 
               OR word LIKE '%{query} %' OR word LIKE '% {query}%' 
               OR word='{query}'
               ORDER BY tweetid DESC""".format(query=query)
           )
  rows = c.fetchall()
  
  for row in rows:
    c.execute('SELECT path FROM pictures WHERE tweetid = {0}'.format(row[0]))
    pic_row = c.fetchone()
    
    messages="""
      <h3>@{0}: 
        <div style="color:{1}; font-family:'{2}'">{3}</div>
      </h3>
    """.format(row[2], row[5], row[6], row[1])
    html += messages
    
    if pic_row:
      path = pic_row[0]
      image_url="pete_twitt.cgi?action=show_image&path={path}".format(path=path)
      html += '<image src="'+image_url+'" height="250" >'
    
    
  
  conn.close()
  return html
  
##############################################################
def redirect_search_page(form):
  user=form["user"].value
  session=form["session"].value
  query=form["query"].value
  searchType=form["type"].value
  
  html="""
  <!DOCTYPE HTML>
  <html lang="en-US">
      <head>
          <meta charset="UTF-8">
          <meta http-equiv="refresh" content="1;
                url=search.cgi?user={user}&session={session}&query={query}&type={type}">
          <script type="text/javascript">
              window.location.href = "search.cgi?user={user}&session={session}&query={query}&type={type}"
          </script>
          <title>Search Page Redirection</title>
      </head>
      <body>
          <!-- Note: don't tell people to `click` the link, just tell them that it is a link. -->
          If you are not redirected automatically, follow the 
            <a href='search.cgi?user={user}&session={session}&query={query}&type={type}'>home</a>
      </body>
  </html>
  """.format(user=user, session=session, query=query, type=searchType)
  
  print_html_content_type()
  print(html)
  
  
##############################################################
def follow(form):
  follower=form["user"].value
  followee=form["followee"].value
  
  conn = sqlite3.connect(DATABASE)
  c = conn.cursor()
  
  if not is_following(followee, follower):
    t = (followee, follower)
    c.execute('INSERT INTO relations VALUES (?,?)', t)
    msg = "@{0} just followed you.".format(follower)
    t = (followee, msg, 1)
    c.execute('INSERT INTO inbox VALUES (?,?,?)', t)

  conn.commit()
  conn.close()
  
  redirect_search_page(form)

##############################################################

def unfollow(form):
  follower=form["user"].value
  followee=form["followee"].value

  conn = sqlite3.connect(DATABASE)
  c = conn.cursor()

  if is_following(followee, follower):
    c.execute("DELETE FROM relations WHERE followee='{0}' AND follower='{1}'".format(followee, follower))

  conn.commit()
  conn.close()
  redirect_search_page(form)
  
##############################################################
# Define main function.
def main():
  form = cgi.FieldStorage()
  if "action" in form:
    action=form["action"].value
    #print("action=",action)
    if action == "follow":
      follow(form)
    elif action == "unfollow":
      unfollow(form)
  else:
    search_page(form)
###############################################################
# Call main function.
main()
