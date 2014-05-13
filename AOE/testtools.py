'''
Created on Mar 5, 2011

@author: aoeu
'''
from random import randint
import traceback
import socket

def randomlist(amt=None, lo=-1000, hi=1000):
    if amt == None:
        amt = randint(5,9)
    return [randint(lo, hi) for _ in range(amt)]


class SecurityError:
    pass

class ExecError:
    pass

def assertEqual(v1, v2):
    try:
        assert eval(v1) == eval(v2)
    except AssertionError:
        raise AssertionError("%s(%s) != %s(%s) " % (v1, eval(v1),v2, eval(v2)))

glob = globals()
moduleAllow = {'math':['acos', 'asin', 'atan', 'atan2', 'ceil', 'cos', 'cosh', 
                        'degrees', 'e', 'exp', 'fabs', 'floor', 'fmod', 'frexp', 'hypot', 'ldexp', 'log', 
                        'log10', 'modf', 'pi', 'pow', 'radians', 'sin', 'sinh', 'sqrt', 'tan', 'tanh']}
for k in moduleAllow:
    exec ('import %s' % k) in globals(), locals()    
defaultFunc = dict((i, getattr(glob[k], i)) for (k, lst) in moduleAllow.iteritems() for i in lst)
defaultFunc['__builtins__'] = None

def safeExec(code, safe=[], dic=defaultFunc):
    global defaultFunc, glob
    d = dic.copy()
    for i in safe:
        d[i] = glob[i]
    print 'the dict is ', d
    if 'import' in code or 'exec' in code:
        return (False, 'Import and Exec are not allowed')
    local = {}
    try:
        exec code in d, local
    except:
        return (False, traceback.format_exc(), local)
    return (True, '', local)