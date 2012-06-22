import sqlite3
import json

class DatabaseValidationException(Exception):
    pass
DBVErr = DatabaseValidationException


def cqt(args):
    if not args:
        return ""
    return  " WHERE " + " and ".join("%s = ?" % i for i in args.keys())

def cqte(conn, table, args, rowfn, one=True):
        r = conn.execute("SELECT * FROM %s %s" % (table, cqt(args)),
                args.values())
        if one:
            r = r.fetchone()
            if not r:
                return None
            return rowfn(r)

        return map(rowfn, r)


# Processor Object
class Processor(object):
    @staticmethod
    def dbSetup(c):
        c.execute("CREATE TABLE processor (id INTEGER PRIMARY KEY ASC, name)")

    @staticmethod
    def getById(c, id):
        c.execute("SELECT * FROM processor WHERE id == ?", (id, ))
        r = c.fetchone()

        a = Processor()
        a.__id = r["id"]
        a.__name = r["name"]
        return a

    @property
    def name(self):
        return self.__name

    @property
    def id(self):
        return self.__id


class Binary(object):
    @staticmethod
    def dbSetup(c):
        c.execute("CREATE TABLE binary (binhash, proc_id, filename)")

class Function_In_Binary(object):
    @staticmethod
    def dbSetup(c):
        c.execute("CREATE TABLE func_in_bin (fhash, binhash, offset)")

class Function(object):
    @staticmethod
    def dbSetup(c):
        c.execute("CREATE TABLE function (fhash, simhash, proc_id)")

class Token(object):
    @staticmethod
    def dbSetup(c):
        c.execute("CREATE TABLE token (token, author_id)")
    
    @staticmethod
    def checkToken(c, tok):
        r = c.execute("SELECT * FROM token WHERE token = ?", (tok,)).fetchone()
        if not r:
            return -1
        return r["author_id"]

class Author(object):
    @staticmethod
    def dbSetup(c):
        c.execute("CREATE TABLE author (author_id INTEGER PRIMARY KEY ASC, name, email)")

    @staticmethod
    def createFromRow(r):
        s = Author()
        s.id = r["author_id"]
        s.name = r["name"]
        s.email = r["email"]
        return s

    @staticmethod
    def getByAuthorID(c, aid):
        r = c.execute("SELECT * FROM author WHERE author_id = ?",
                (aid,)).fetchone()
        if not r:
            return None
        return Author.createFromRow(r)

    def munged(self):
        return "%s <%s>" % (self.name, self.email)


class Commit(object):
    @staticmethod
    def dbSetup(c):
        c.execute("CREATE TABLE commit_ (commit_id  INTEGER PRIMARY KEY ASC, author, acl, message, timestamp)")

    @staticmethod
    def createFromRow(c, r):
        s = Commit()
        s.id = r["commit_id"]
        s.author = Author.getByAuthorID(c, r["author"])
        if not s.author:
            raise DBVErr("No author for commit with author_id=%d" % r["author"])
        s.acl = r["acl"]
        s.message = r["message"]
        s.timestamp = r["timestamp"]
        return s

    @staticmethod
    def getByCommitId(c, cid):
        r = c.execute("SELECT * FROM commit_ WHERE commit_id == ?", (cid,))
        r = r.fetchone()
        if not r:
            return None
        return Commit.createFromRow(c, r)

    @staticmethod
    def new(conn, acl, message, timestamp, authorid):
        curs = conn.cursor()
        curs.execute("""INSERT INTO commit_
            (author, acl, message, timestamp)
            VALUES (?, ?, ?, ?)""", (authorid, acl, message, timestamp)) ########################

        conn.commit()
        r = curs.lastrowid
        return r

class Vpoint(object):
    @staticmethod
    def dbSetup(c):
        c.execute("""CREATE TABLE vpoint (
            vpoint_id INTEGER PRIMARY KEY ASC,
            fhash,
            binhash,
            simhash,
            commitID,
            name,
            comments_b,
            prototype,
            refdtypes_b,
            regvars_b,
            stackvars_b)""")

    @staticmethod
    def createFromRow(c, r):
        s = Vpoint()
        s.id = r["vpoint_id"]
        s.fhash = r["fhash"]
        s.binhash = r["binhash"]
        s.simhash = r["simhash"]
        s.commit = Commit.getByCommitId(c, r["commitID"])

        if not s.commit:
            raise DBVErr("No commit for vpoint with commit_id=%d" %
                    r["commitID"])
        s.name = r["name"]
        s.prototype = r["prototype"]
        

        # 4 opaque blob types - currently JSON
        s.comments_b = json.loads(r["comments_b"])
        s.refdtypes_b = json.loads(r["refdtypes_b"])
        s.regvars_b = json.loads(r["regvars_b"])
        s.stackvars_b = json.loads(r["stackvars_b"])

        return s

    @staticmethod
    def getFor(c, last=False, **kwargs):
        lc = ""
        if last:
            lc = "ORDER BY vpoint_id DESC LIMIT 1"


        rows = c.execute("SELECT * FROM vpoint" + cqt(kwargs) + lc,
                kwargs.values())


        return [Vpoint.createFromRow(c,r) for r in rows]

    @staticmethod
    def getForExactBinaryFunction(c, binhash, fhash, last=False):
        return Vpoint.getFor(c, binhash=binhash, fhash=fhash, last=last)
    
    @staticmethod    
    def getForFuzzyBinaryFunction(c, simhash, last=False):
        return Vpoint.getFor(c, simhash=simhash, last=last)

    @staticmethod
    def new(conn, fhash,
            binhash,
            simhash,
            commitID,
            name,
            comments_b,
            prototype,
            refdtypes_b,
            regvars_b,
            stackvars_b):

        curs = conn.cursor()
        curs.execute("""INSERT INTO vpoint
            (fhash,
            binhash,
            simhash,
            commitID,
            name,
            comments_b,
            prototype,
            refdtypes_b,
            regvars_b,
            stackvars_b)
            VALUES (?, ?, ?, ?, ?,?,?,?,?,?)""", (fhash,
            binhash,
            simhash,
            commitID,
            name,
            json.dumps(comments_b),
            prototype,
            json.dumps(refdtypes_b),
            json.dumps(regvars_b),
            json.dumps(stackvars_b)
            ))

        conn.commit()
        r = curs.lastrowid
        return r

def connect(name):
    conn = sqlite3.connect(name)
    conn.row_factory = sqlite3.Row
    return conn

def setup(c):
    r = c.execute("""SELECT name FROM sqlite_master WHERE type='table' and
    name='processor'""")

    if r.fetchone():
        return

    for i in [Processor, Binary, Function_In_Binary, Function, Token, Author,
            Commit, Vpoint]:
        i.dbSetup(c)
