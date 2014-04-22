#!/usr/bin/python

import sqlite3
conn = sqlite3.connect('pete_twitt.db')

c = conn.cursor()

# Turn on foreign key support
c.execute("PRAGMA foreign_keys = ON")

# Create users table
c.execute('''CREATE TABLE users
	     (handle TEXT NOT NULL,
	      email TEXT,
	      firstname TEXT,
	      lastname TEXT,
	      password TEXT NOT NULL,
	      PRIMARY KEY(handle))''')

# Create tweets table
# Visibility is 'public' or 'private'
c.execute('''CREATE TABLE tweets
	     (tweetid INTEGEER NOT NULL,
	      word TEXT NOT NULL,
	      owner TEXT NOT NULL,
	      time INTEGER NOT NULL,
	      replyto INTEGER,
	      color TEXT,
	      font TEXT,
	      FOREIGN KEY (owner) REFERENCES users(handle),
	      PRIMARY KEY(tweetid))''')
	      
# Create relation table
c.execute('''CREATE TABLE relations
       (followee TEXT NOT NULL,
        follower TEXT NOT NULL,
        PRIMARY KEY(followee, follower))''')
        
# Create inbox table
c.execute('''CREATE TABLE inbox
       (owner TEXT NOT NULL,
        message TEXT NOT NULL,
        isread INTEGER NOT NULL)''')

# Create pictures table
c.execute('''CREATE TABLE pictures
	     (path TEXT NOT NULL,
	      tweetid INTEGER NOT NULL,
	      owner TEXT NOT NULL,
	      FOREIGN KEY(tweetid) REFERENCES tweets(tweetid),
	      FOREIGN KEY(owner) REFERENCES users(handle),
	      PRIMARY KEY(path))''')

# Create sessions table
c.execute('''CREATE TABLE sessions
	     (user TEXT NOT NULL,
	      session TEXT NOT NULL,
	      FOREIGN KEY(user) REFERENCES users(handle),
	      PRIMARY KEY(session))''')


# Save the changes
conn.commit()

# Close the connection
conn.close()
