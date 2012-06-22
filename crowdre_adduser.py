# Run with args: <database filename> <name> <email> <authtoken>

import json
#import sqlite3
import sys

import crowdre_sql as cs
import pprint


def main():
    if len(sys.argv) != 5:
    	print "Usage: <database filename> <name> <email> <authtoken>"
    	return
    	
    name = sys.argv[1]
    username = sys.argv[2]
    email = sys.argv[3]
    authtoken = sys.argv[4]
    db = cs.connect(name)
    cs.setup(db)

    r = db.execute("""select count(*) from author""")
    idcount = r.fetchone()[0]
    idcount = idcount + 1
    
    r = db.execute("""insert into author values (%d, '%s', '%s')""" % (idcount, username, email))
    r = db.execute("""insert into token values ('%s', %d)""" % (authtoken, idcount))
    db.commit()
    
    print "User inserted successfully!"
    return

if __name__ == '__main__':
    main()
