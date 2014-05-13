#
from google.appengine.ext import webapp #@UnresolvedImport
from google.appengine.ext.webapp import util #@UnresolvedImport
from google.appengine.ext.webapp import template #@UnresolvedImport
from django.utils import simplejson

import cgi
import StringIO
import itertools
import random
import logging

class Global:
    pass

class MainHandler(webapp.RequestHandler):
    def __init__(self, **args):
        self.rounds = """1 2 8\n3 3 3"""
        webapp.RequestHandler.__init__(self, **args)
    def get(self):
        #lst = self.game()
        self.response.out.write(template.render('game.html', {'lst':'', 'rounds':self.rounds, 're':str(self.request.headers), 'ra':'RARARA'}))
    
    def post(self):
        
        data2type = {'nrounds':int, 'nplayers':int, 'nslots':int, 'multiplier':float}
        args = dict((k, type(cgi.escape(self.request.get(k)))) for k, type in data2type.iteritems())
        Global.args = args
        if cgi.escape(self.request.get('server')) != "":
            self.redirect('/server')
            return
        
        self.rounds = str(cgi.escape(self.request.get('rounds')))
        rounds = self.rounds.strip().split('\n')
        rounds = [[int(o) for o in i.split(' ')] for i in rounds]

        random_mode = cgi.escape(self.request.get('random')) != ""
        
        lst = self.game(
#                   multiplier=float(cgi.escape(self.request.get('multiplier'))),
#                   rounds=rounds,
#                   nrounds=int(cgi.escape(self.request.get('nrounds'))),
#                   nplayers=int(cgi.escape(self.request.get('nplayers'))),
#                   nslots=int(cgi.escape(self.request.get('nslots'))),
                    rounds=rounds,
                    random_mode=random_mode,
                    **args
                   )
        self.response.out.write(template.render('game.html', {'lst':'\n'.join(lst), 'rounds':self.rounds}))        
    
    def game_run(self, rounds=20, nslots=10, random_mode=False):
        
        #for msg in self.game(rounds, nrounds, nplayers, multiplier, nslots, random_mode):
        
        pass
    
    def randomRounds(self, nrounds, nplayers, nslots):
        for _ in range(nrounds):
            yield [random.randint(0,nslots-1) for _ in range(nplayers)]
    def presetRounds(self, rounds):
        for choices in rounds:
            yield choices
            
    def game(self, nrounds=None, nplayers=None, multiplier=2.0, nslots=10, generator=None):
#        lst=[]
        
        if generator == None:
            generator = self.randomRounds(nrounds, nplayers, nslots)
            
#        def write(s):
#            lst.append(s)
        def divide(choice):
            nequal = 0
            div = {}
            for n, v in enumerate(choice):
                div.setdefault(v, []).append(n)
            return div
        
        score = [0] * nplayers
        b = StringIO.StringIO()
        
        def distance(a, b):
            rawdist = (b - a) % nslots
            fix = lambda x: nslots-1 if x == -1 else x
            return (fix((b - a)%nslots - 1), fix((a-b)%nslots - 1))
        
        for round, choice in enumerate(generator()):
            add = [0 for _ in choice]            
            divisions = divide(choice) 
            #write('ROUND %d: choice:%s - divisions are %s '% (round, choice, divisions))
            sorted_div = sorted(list(divisions.iteritems()), key=lambda x: x[0])
                                    
            pair = []
            for i in range(len(sorted_div)-1):
                pair.append((sorted_div[i], sorted_div[i+1]))
            pair.append((sorted_div[-1], sorted_div[0]))

            pair = sorted_div
            for (x, (_, divisiona)) in enumerate(sorted_div):
                clock, _ = distance(pair[x-1][0], pair[x][0])
                clock2, _ = distance(pair[x][0], pair[(x+1)%len(pair)][0])
                for c in divisiona:
                    add[c] = (clock+clock2) / len(divisiona)
            
            #write('raw round score: %s' % add)
            even = [x for x, i in enumerate(choice) if i % 2 == 0]
            odd  = [x for x, i in enumerate(choice) if i % 2 == 1]
            greater = even if len(even) > len(odd) else odd        
            for x in greater:
                add[x]*=multiplier
            #write('round score: %s' % add)
            score = [a+b for a, b in zip(score, add)]
            #write('total score: %s' % score)
            #write('---')
            yield {'roundscore':add, 'score':score, 'round':round, 'choices':choice, 'divisions':divisions, 'done':False}
        yield {'done':True}

class Client(webapp.RequestHandler):
    """ Will handle the RPC requests."""
    def get(self):
        pass
    def post(self):
        pass

class Server(webapp.RequestHandler):
    'modes '
    modes = ['modeInit', 'modeRound', 'modeDone']
    allowedFunctions = ['getGameData', 'getName', 'postValue', 'getResults']
    alphabet = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz'
    def __init__(self, **args):
        self.mode = 'modeInit'
        self.playern = 0
        self.roundData = {}
        webapp.RequestHandler.__init__(self, *args)
    
    def send(self, d={}):
        self.response.out.write(simplejson.dumps(d))
    
    def getName(self):
        self.playern += 1
        self.response.out.write('%s'%(self.playern-1,))
    
    def getGameData(self):
        if self.playern == Global.args['nplayers']:
            d = {'done':True}
            d.update(Global.args)
            self.send(d)
        else:
            self.send({'done':False, 'playern':0, 'nplayers':Global.args['nplayers']})
            
    def getResults(self):
        if len(self.rounddata) != Global.args['nplayers']:
            d = {'done':False}
            self.send({'roundDone':False, 'done':True, 'nplayers':len(self.rounddata)})
        else:
            # Check that it is not done...            
            self.send({'done':False, 'roundDone':True})            
        
    def postValue(self):
        self.rounddata[self.request.get('player')] = self.request.get('value')
        self.send({'done':False})
        # tell the client to wait until results
    def handleFunction(self):
        function = self.request.get('function')
        if function in Server.allowedFunctions:
            getattr(self, function)()
        else:
            self.response.out.write('%s is an invalid function' % function)        
    def get(self):
        if  'X-Requested-With' in self.request.headers:
            self.handleFunction()
        else:
            self.response.out.write(template.render('server.html', {}))
    def post(self):
        self.handleFunction()    

def main():
    application = webapp.WSGIApplication([('/', MainHandler), ('/client', Client), ('/server', Server)],
                                         debug=True)
    util.run_wsgi_app(application)

if __name__ == '__main__':
    main()
