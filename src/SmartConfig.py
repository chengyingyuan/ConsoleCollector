import sys
import re
from collections import OrderedDict

class SmartConfig(object):
    def __init__(self, fpath, encoding=None):
        self._fpath = fpath
        self._encoding = encoding
        self._reset()
        self._parse()
    
    def __len__(self):
        if self._freevarslen is None:
            self._freevarslen = len(self._freevars)
            self._sectionslen = len(self._sections)
        return self._freevarslen+self._sectionslen
    
    def __getattr__(self, name):
        return self.get(name)
    
    def __getitem__(self, name):
        if type(name) == int: # Access by index
            if self._keys is None:
                self._keys = self._freevars.keys() + self._sections.keys()
            if name < 0 or name > self.__len__():
                raise IndexError()
            if name < self._freevarslen:
                return self._freevars[self._keys[name]]
            else:
                return self._sections[self._keys[name]]
        else:
            return self.get(name)
    
    def _reset(self):
        self._errstring = ''
        self._errline = -1
        self._freevars = OrderedDict()
        self._sections = OrderedDict()
        self._freevarslen = None
        self._sectionslen = None
        self._keys = None
    
    def keys(self):
        if self._keys is None:
            self._keys = self._freevars.keys() + self._sections.keys()
        return self._keys[:]
    
    @property
    def valid(self):
        return (not self._errstring)

    @property
    def errstring(self):
        return self._errstring
    
    @property
    def errline(self):
        return self._errline
    
    @property
    def sectionNames(self):
        return self._sections.keys()
    
    def getSection(self, secName):
        if secName in self._sections:
            return self._sections[secName]
        return None
    
    def get(self, key, secName=None, limit=False):
        if secName is None:
            if key in self._freevars:
                return self._freevars[key]
            if key in self._sections:
                return self._sections[key]
            return None
        if secName in self._sections:
            if key in self._sections[secName]:
                return self._sections[secName][key]
            if (not limit) and (key in self._freevars):
                return self._freevars[key]
        return None
    
    def getInt(self, key, secName=None, limit=False):
        v = self.get(key, secName, limit)
        if v is not None:
            v = int(v)
        return v

    def getFloat(self, key, secName=None, limit=False):
        v = self.get(key, secName, limit)
        if v is not None:
            v = float(v)
        return v

    def getBool(self, key, secName=None, limit=False):
        v = self.get(key, secName, limit)
        if v is not None:
            v = v.lower()
            if v == "true":
                return True
            return False
        return v
    
    def getDict(self, key, secName=None):
        cands = self.get(key, secName)
        if type(cands) != str:
            return None
        ckeys = [key.strip() for key in cands.split(',')]
        result = {}
        for ckey in ckeys:
            value = self.get(ckey)
            if value is not None:
                result[ckey] = value
        return result
    
    def dump(self):
        print("Free variables:")
        for k, v in self._freevars.items():
            print("\t{} => {}".format(k, v))
        print("Sections:")
        for secName, secVars in self._sections.items():
            print("\t{}".format(secName))
            for secVarName, secVarVals in secVars.items():
                print("\t\t{} => {}".format(secVarName, secVarVals))

    def _resolve_deps(self, target, referer):
        # Phase I: Build dependencies
        deps = {}
        for k, v in target.items():
            depvars = re.findall('\\${(.*?)}', v)
            for dv in depvars:
                if (dv in target) or (dv in referer):
                    if k not in deps:
                        deps[k] = {}
                    deps[k][dv] = None
                else:
                    self._errstring = "Dependency variable {} not defined".format(dv)
                    return False
        # Phase III: Resolve dependencies
        vpath = []
        depvals = {}
        for key in deps.keys():
            result = self._resolve_key(key, deps, target, referer, vpath)
            if result is None:
                return False
            depvals[key] = result
        # Phase IV: Update target
        for key in deps.keys():
            target[key] = depvals[key]
        return True

    def _resolve_key(self, key, deps, target, referer, vpath):
        vpath = vpath[:]
        vpath.append(key)
        for kk in deps[key].keys():
            if deps[key][kk] is not None:
                continue
            if kk not in deps:
                if kk in target:
                    deps[key][kk] = target[kk]
                elif kk in referer:
                    deps[key][kk] = referer[kk]
                else:
                    assert False
                continue
            if kk in vpath:
                self._errstring = 'Dependency loop found, {}->{}({})'.format(key, kk, vpath)
                return None
            vvpath = vpath[:]
            vvpath.append(kk)
            result = self._resolve_key(kk, deps, target, referer, vvpath)
            if result is None: # Loop found
                return None
            deps[key][kk] = result
        value = target[key]
        for kk in deps[key].keys():
            value = value.replace('${%s}' % kk, deps[key][kk])
        return value
    
    def _parse(self):
        freevars = OrderedDict()
        sections = OrderedDict()
        # Phase I: Scan lines in order
        with open(self._fpath, 'r', encoding=self._encoding) as fp:
            lineno = 0
            secName = None
            secVars = None
            while True:
                line = fp.readline()
                if not line: # end of file
                    break
                lineno += 1
                line = line.strip()
                if (not line) or line.startswith('#'):
                    continue
                # Is it a section beginning
                m = re.match('^\\[([^\\]]+)\\]$', line)
                if m:
                    secName = m.group(1)
                    secVars = OrderedDict()
                    sections[secName] = secVars
                    continue
                # Is it a variable
                elems = [elem.strip() for elem in line.split('=', 1)]
                if len(elems) != 2:
                    self._errline = lineno
                    self._errstring = "No assignment operation"
                    return False
                key, value = elems
                if secName is not None:
                    secVars[key] = value
                else:
                    freevars[key] = value
        # Phase II: Resolve dependencies
        if not self._resolve_deps(freevars, {}):
            return False
        for key in sections.keys():
            if not self._resolve_deps(sections[key], freevars):
                return False
        self._freevars = freevars
        self._sections = sections
        return True

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("USAGE: SmartConfig.py <config-file>", file=sys.stderr)
        sys.exit(-1)
    c = SmartConfig(sys.argv[1], encoding='UTF-8')
    if c.valid:
        print("OK Valid config")
    c.dump()
