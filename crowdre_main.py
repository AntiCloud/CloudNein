from twisted.web import server, resource
from twisted.internet import reactor

import json
import sys

import crowdre_sql as cs
import pprint

log = open("log.txt", "w")

class Root(resource.Resource):
    def getChild(self, child, request):
        if child == "":
            return Version()
        print "WARNING -UNIMPL: %s" % child
        return Bad()

class JSONApiEndpoint(resource.Resource):
    isLeaf = True
    def render_GET(self, request):
        return self.render_POST(request)

    def render_POST(self, request):
        request.responseHeaders.setRawHeaders("Content-type",
        ["application/json; charset=utf-8"])

        request.content.seek(0)
        content = request.content.read()

        v = None
        if content:
            v = json.loads(content)

        if log:
            log.write("%s\n" % request.path)
            if (v):
                log.write("IN:  %s\n" % pprint.pformat(v))

        out = self.handle(v)

        log.write("OUT: %s\n" % pprint.pformat(out))
        log.write("\n")
        log.flush()

        return json.dumps(out)

class Bad(JSONApiEndpoint):
    def handle(self, s):
        return ""

def BadAuth():
    return {'valid': None,'errors':[{'message':'invalid token'}],'stage':'auth'}

def dMap(mapping, inobj):
    return dict( (k, o(inobj) if callable(o) else getattr(inobj, o)) for (k, o) in mapping)

from copy import copy
# /version
class Version(JSONApiEndpoint):
    leafName = 'version'

    def handle(self, in_data):
        return {'valid': True, 'version': True}

################################################
class LastRevs(JSONApiEndpoint):
    leafName = 'lastrevs'

    def handle(self, in_data):

        revs = []
        ret = {'valid': True, 'revisions': revs}

        # Validation
        if not in_data:
            return {'valid': False, 'why': "No input data"}
        if not all(_ in in_data for _ in ['functions',
                                         'binary']):
            return {'valid': False, 'why': "Invalid parameters"}

        authtoken = in_data["auth"]["token"]
        if cs.Token.checkToken(self.db, authtoken) == -1:
            print "Auth failed - Token: %s" % authtoken
            return BadAuth()    
            
        # Check if we're doing exact or fuzzy matching
        matchmode = "fuzzy"
        if "method" in in_data:
        	if in_data["method"] == "exact":
        		matchmode = "exact"
       
        # iterate through data
        for i in in_data["functions"]:
        	
            if matchmode == "exact":
                vp = cs.Vpoint.getForExactBinaryFunction(self.db, in_data["binary"], i["fhash"],
                   last=True)
            else:
            	vp = cs.Vpoint.getForFuzzyBinaryFunction(self.db, i["simhash"], last=True)

            # If no match found
            if not vp:
                continue

            assert len(vp) == 1

            vp = vp[0]

            t = [("vpoint", "id"),
                 ("prototype", "prototype"),
                 ("name", "name"),
                 ("author", lambda x: x.commit.author.munged()),
                 ("fhash", "fhash"),
                 ("simhash", "simhash"),
                 ("message", lambda x: x.commit.message )]

            d = dMap(t, vp)
            revs.append(d)

        return ret

class Revisions(JSONApiEndpoint):
    leafName = 'revisions'

    def handle(self, in_data):
        if not in_data:
            return {'valid': False, 'why': "No input data"}
        if not all(_ in in_data for _ in ['auth', 'fhash', 'offset',
                                         'binary', 'processor']):
            return {'valid': False, 'why': "Invalid parameters"}

        binary = in_data["binary"]
        authtoken = in_data["auth"]["token"]
        fhash = in_data["fhash"]
        offset = in_data["offset"]
        processor = in_data["processor"]
        
        if cs.Token.checkToken(self.db, authtoken) == -1:
            print "Auth failed - Token: %s" % authtoken
            return BadAuth() 

        resp = cs.Vpoint.getForExactBinaryFunction(self.db, binary, fhash)

        ns = []
        for i in resp:
            t = [
                    ("vpoint", "id"),
                    ("name", "name"),
                    ("prototype", "prototype"),
                    ("message", lambda x: x.commit.message),
                    ("author", lambda x: x.commit.author.munged()),
                    ("timestamp", lambda x: int(x.commit.timestamp)),
                    ("simhash", "simhash")
                    ]

            ns.append(dMap(t, i))

        rev_resp = {'valid':True,
                   u'revisions': ns }

        return rev_resp

import time
class Commit(JSONApiEndpoint):
    leafName = 'commit'

    def handle(self, in_data):
        if not in_data:
            return {'valid': False, 'why': "No input data"}
        if not all(_ in in_data for _ in ['acl', 'auth', 'vpoints',
                                         'binary', 'processor']):
            return {'valid': False, 'why': "Invalid parameters"}
        
        message = ""    
        if "message" in in_data:
            message = in_data["message"]
            
        authtoken = in_data["auth"]["token"]    

        authorid = cs.Token.checkToken(self.db, authtoken)
        if authorid == -1:
            print "Auth failed - Token: %s" % authtoken
            return BadAuth()     
            
        cid = cs.Commit.new(self.db, in_data["acl"], message,
                time.time(), authorid)

        print "Allocated new commit id=%d" %cid

        for i in in_data['vpoints']:
            cs.Vpoint.new(self.db,
                    i["function"],
                    in_data["binary"],
                    i["simhash"],
                    cid,
                    i["name"],
                    i["comments"],
                    i["prototype"],
                    i["refdtypes"],
                    i["regvars"],
                    i["stackvars"])

        return {'valid': True}


class Checkout(JSONApiEndpoint):
    leafName = 'checkout'

    def handle(self, in_data):
        authtoken = in_data["auth"]["token"]    

        authorid = cs.Token.checkToken(self.db, authtoken)
        if authorid == -1:
            print "Auth failed - Token: %s" % authtoken
            return BadAuth()
    
        ret = {'valid':True}
        fns = []
        ret['functions'] = fns
        ret['types'] = []

        for i in in_data["functions"]:
            fhash = i['fhash']
            vpoint = int(i['vpoint'])

            vp = cs.Vpoint.getFor(self.db, vpoint_id=vpoint, fhash=fhash)
            if not vp:
                continue

            assert len(vp) == 1
            vp = vp[0]

            t = [("vpoint", "id"),
                 ("name", "name"),
                 ("prototype", "prototype"),
                 ("refdtypes", "refdtypes_b"),
                 ("comments", "comments_b"),
                 ("regvars", "regvars_b"),
                 ("stackvars", "stackvars_b") ]

            fns.append(dMap(t, vp))
        return ret


def main():
    if len(sys.argv) != 2:
    	print "Usage: <database filename (will be created if none exists)>"
    	return

    root = Root()

    name = sys.argv[1]
    db = cs.connect(name)
    cs.setup(db)

    def putEndpoint(cname):
        r = cname()
        r.db = db
        root.putChild(cname.leafName, r)

    putEndpoint(Version)
    putEndpoint(Commit)
    putEndpoint(Revisions)
    putEndpoint(Checkout)
    putEndpoint(LastRevs)


    site = server.Site(root)
    reactor.listenTCP(8080, site)
    reactor.run()

if __name__ == '__main__':
    main()
