"""collect: extensions to create frequently used collections of objects."""


def __requestItem__expt(self,tierMax=None,esid=None):
    """Return set of experiment item identifiers for experiments linked directly or indirectly to this requestItem:
          tierMax: maximum experiment tier: if set, only return experiments with tier <= tierMax;
          esid: set of esid values: if set, return experiments for specified set, rather than self.esid"""

    assert self._h.label == 'requestItem', 'collect.__requestItem__expt attached to wrong object: %s [%s]' % (self._h.title,self._h.label)

    if esid != None:
      es = self._inx.uid[esid]
    else:
      es = self._inx.uid[self.esid]
    s = set()

###
### checking tierMax and treset. If tierMax is None, there is nothing to do.
### otherwise, return empty or full list (tierResetPass True) depending on relation between treset and tiermax.
###
    tierResetPass = False
    if 'treset' in self.__dict__ and tierMax != None:
      if tierMax <= self.treset:
        return s
      else:
        tierResetPass = True


    if es._h.label == 'experiment':
      if tierMax == None or tierResetPass or es.tier[0] <= tierMax:
        s.add(es.uid)
    elif es._h.label in ['exptgroup','mip']:
      if 'experiment' in self._inx.iref_by_sect[self.esid].a:
        for id in self._inx.iref_by_sect[self.esid].a['experiment']:
          s.add(id)
      if not( tierMax == None or tierResetPass ):
        s = set( [x for x in s if self._inx.uid[x].tier[0] <= tierMax] )
    return s

def __requestLink__expt(self,tierMax=None, rql=None):
    """Return set of experiment item identifiers for experiments linked to this requestLink:
          tierMax: maximum experiment tier: if set, only return experiments with tier <= tierMax;
          rql: set of requestLink uid values: if set, return experiments for specified set."""
    assert self._h.label == 'requestLink', 'collect.__requestLink__expt attached to wrong object: %s [%s]' % (self._h.title,self._h.label)
    s = set()
    if rql == None:
      rql = [self.uid,]
    
## generate set of "esid" values (pointing to experiments, experiment groups, or MIPs)
    sesid = set()
    rqil = []
    for u in rql:
      if 'requestItem' in self._inx.iref_by_sect[u].a:
        for id in self._inx.iref_by_sect[u].a['requestItem']:
          rqil.append( id )
          sesid.add( self._inx.uid[id].esid )

    if len( rqil ) > 0:
      rqi = self._inx.uid[rqil[0]]

## flatten to list of experiments.
      for u in sesid:
        for x in rqi.__get__expt(tierMax=tierMax,esid=u):
           s.add( x )
    return s

def __mip__expt(self,tierMax=None,mips=None):
    """Return set of experiment item identifiers for experiments linked to this mip:
          tierMax: maximum experiment tier: if set, only return experiments with tier <= tierMax;
          mips: set of mip uid values: if set, return experiments for specified set."""

    assert self._h.label == 'mip', 'collect.__mip__expt attached to wrong object: %s [%s]' % (self._h.title,self._h.label)
    s = set()
    if mips == None:
      mips = [self.uid,]
    
    for u in mips:
      if 'requestLink' in self._inx.iref_by_sect[u].a:
        for id in self._inx.iref_by_sect[self.uid].a['requestLink']:
          for x in self._inx.uid[id].__get__expt(tierMax=tierMax):
            s.add( x )
    return s

def __mip__CMORvar(self,mips=None,pmax=None):
    """Return set of CMORvar item identifiers for CMORvar linked to this mip:
          pmax: maximum variable priority: if set, only return variables requested with priority <= pmax;
          mips: set of mip uid values: if set, return variables for specified set."""
    assert self._h.label == 'mip', 'collect.__mip__CMORvar attached to wrong object: %s [%s]' % (self._h.title,self._h.label)
    s = set()
    if mips == None:
      mips = [self.uid,]
    
    for u in mips:
      if 'requestLink' in self._inx.iref_by_sect[u].a:
        for id in self._inx.iref_by_sect[self.uid].a['requestLink']:
          for x in self._inx.uid[id].__get__CMORvar(pmax=pmax):
            s.add( x )
    return s

def __requestLink__CMORvar(self,rql=None,pmax=None):
    """Return set of CMORvar item identifiers for CMORvar linked to this requestLink, or to set of requestlinks in argument rql:
          pmax: maximum variable priority: if set, only return variables requested with priority <= pmax;
          rql: set of requestLink uid values: if set, return variables for specified set."""

    assert self._h.label == 'requestLink', 'collect.__requestLink__CMORvar attached to wrong object: %s [%s]' % (self._h.title,self._h.label)
    s = set()

    if rql == None:
      rql = [self.uid,]
    
## get set of requestVarGroups
    rvg = set( [self._inx.uid[u].refid for u in rql] )

    for u in rvg:
      if 'requestVar' in self._inx.iref_by_sect[u].a:
        for id in self._inx.iref_by_sect[u].a['requestVar']:
          this = self._inx.uid[id]
          if pmax == None or this.priority <= pmax:
            s.add( this.vid )
    return s


def __check__args(x,validItems=['dreqItem_mip',]):
  if type(x) == type('x'):
    return (1,'str')
  elif type(x) == type(u'x'):
    return (1,'unicode')
  elif type(x) not in [type([]), type((1,))]:
    if x.__class__.__name__ in validItems:
      return (2,x.__class__.__name__)
    else:
      return (-2,'Object type not accepted' )
  else:
    if all( [type(i) == type('x') for i in x] ):
      return (10,'str')
    elif all( [type(i) == type(u'x') for i in x] ):
      return (10,'unicode')
    else:
      s = set( [i.__class__.__name__ for i in x] )
      if len(s) > 1:
        return (-1,'Multiple object types in list' )
      else:
        this = list(s)[0]
        if this in validItems:
          return (20,this)
        else:
          return (-3,'Listed object type not accepted' )
 


### need dq here ...... or at least timeslice collection object ...
def __timeSlice__compare(self,other):
    """Compare two time slices, returning tuple (<return code>, <slice>, <comment>), with the larger slice if succesful.
      If return code is negative, no solution is found. If return code is 2, the slices are disjoint and both returned."""
 
    assert self._h.label == 'timeSlice', 'collect.__timeSlice__compare attached to wrong object: %s [%s]' % (self._h.title,self._h.label)
    if self.label == other.label:
      return (0,self,'Slices equal')

    sl = sorted( [self.label, other.label] )

## label dict allows look-up of objects by label ....
    ee = self._labelDict

## handle awkward cases
##
    if self.type != other.type or self.type == 'dayList':
###
      if sl in [['piControl030a','piControl200'],['piControl030', 'piControl200']]:
        return (1,ee['piControl200'],'Taking preferred slice (possible alignment issues)')
###
      elif sl == ['piControl030', 'piControl030a']:
        return (1,ee['piControl30'],'Taking preferred slice (possible alignment issues)')
###
      elif sl == ['RFMIP','RFMIP2']:
       ## this = [i for i in self._sectionList if i.label == 'RFMIP-union'][0]
##
##
## not coded yet .... create new slice on the fly ... or add union .....
       ## return (1,this, 'Taking ad-hoc union')
        return (-3,None,'slice type aggregation not supported')
##
      elif sl == ['RFMIP', 'hist55']:
###
        return (1,ee['hist55plus'], 'Taking ad-hoc union with extra ...')
##
      elif sl == ['RFMIP2', 'hist55']:
        return (1,ee['hist55'], 'Taking larger containing slice')
##
      elif sl == ['DAMIP20','DAMIP40']:
        return (1,ee['DAMIP40'], 'Taking larger containing slice')
##
      return (-1,None,'Multiple slice types: %s' % sorted(ee.keys()))

    if not ( self.type in ['simpleRange','relativeRange'] or (len(self.type) > 13 and self.type[:13] == 'branchedYears') ):
      return (-2,None,'slice type aggregation not supported')

    sa,ea = (self.start, self.end)
    sb,eb = (other.start, other.end )
    if sa <= sb and ea >= eb:
        return (1,self, 'Taking largest slice')
    if sb <= sa and eb >= ea:
        return (1,other, 'Taking largest slice')
    if ea < sb or eb < sa:
        return (2,(self,other), 'Slices are disjoint')
    return (-3,None, 'Overlapping slices')

def  add(dq):
   """Add extensions to data request section classes."""
   dq.coll['mip'].items[0].__class__.__get__expt = __mip__expt
   dq.coll['requestItem'].items[0].__class__.__get__expt = __requestItem__expt
   dq.coll['requestLink'].items[0].__class__.__get__expt = __requestLink__expt
   dq.coll['requestLink'].items[0].__class__.__get__CMORvar = __requestLink__CMORvar
   dq.coll['mip'].items[0].__class__.__get__CMORvar = __mip__CMORvar
   dq.coll['timeSlice'].items[0].__class__.__compare__ = __timeSlice__compare
   for k in dq.coll.keys():
     if len( dq.coll[k].items ) > 0:
       dq.coll[k].items[0].__class__._sectionList = dq.coll[k].items
       dq.coll[k].items[0].__class__._sectionObj = dq.coll[k]

   for k in ['var','experiment','timeSlice','mip','spatialShape','structure']:
     dq.coll[k].items[0].__class__._labelDict = dict()
     for i in dq.coll[k].items:
       dq.coll[k].items[0].__class__._labelDict[i.label] = i

    
    
