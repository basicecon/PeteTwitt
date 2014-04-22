#!/usr/bin/python

# Import the CGI, string, sys modules
import cgi, string, sys, os, re, random
import cgitb; cgitb.enable()  # for troubleshooting
import sqlite3

#Get Databasedir
MYLOGIN="wang1247"
DATABASE="/homes/"+MYLOGIN+"/PeteTwitt/pete_twitt.db"

def create_session(user):
    # Store random string as session number
    # Number of characters in session string
    n=20
    char_set = string.ascii_uppercase + string.digits
    session = ''.join(random.sample(char_set,n)) 

    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()

    # Try to get old session
    t = (user,)
    c.execute('SELECT * FROM sessions WHERE user=?', t)
    row = c.fetchone()
    if row == None:
      # No session for this user. Create one
      s=(user,session)      
      c.execute('INSERT INTO sessions VALUES (?,?)', s)
    else:
      # Update current session
      s=(session,user)
      c.execute('UPDATE sessions SET session=? WHERE user=?',s)

    conn.commit()
    conn.close()

    return session

def check_session(form):
    if "user" in form and "session" in form:
        username=form["user"].value
        session=form["session"].value
        session_stored=read_session_string(username)
        if session_stored==session:
           return "passed"

    return "failed"

def read_session_string(user):
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()

    # Try to get old session
    t = (user,)
    c.execute('SELECT * FROM sessions WHERE user=?', t)
    row = c.fetchone()
    conn.close()

    if row == None:
      return 'no session'

    return row[1]

