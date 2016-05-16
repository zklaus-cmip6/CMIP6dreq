"""Date Request Scoping module
---------------------------
The scope.py module contains the dreqQuery class and a set of ancilliary functions. The dreqQuery class contains methods for analysing the data request.
"""
try:
  import dreq
  from utilities import cmvFilter 
except:
  import dreqPy.dreq
  from dreqPy.utilities import cmvFilter 

import collections, string, operator
import makeTables
import sys, os

python2 = True
if sys.version_info[0] == 3:
  python2 = False
  from functools import reduce
  try: 
    from utilP3 import mlog3
  except:
    from dreqPy.utilP3 import mlog3
  mlg = mlog3()
else:
  from utilP2 import mlog
  mlg = mlog()

class c1(object):
  def __init__(self):
    self.a = collections.defaultdict( int )
class c1s(object):
  def __init__(self):
    self.a = collections.defaultdict( set )

class baseException(Exception):
  """Basic exception for general use in code."""

  def __init__(self,msg):
    self.msg = 'scope:: %s' % msg

  def __str__(self):
    return repr( self.msg )

  def __repr__(self):
    return self.msg

nt_mcfg = collections.namedtuple( 'mcfg', ['nho','nlo','nha','nla','nlas','nls','nh1'] )
class cmpd(object):
  def __init__(self,dct):
    self.d = dct
  def cmp(self,x,y,):
    return cmp( self.d[x], self.d[y] )

    self.default_mcfg = nt_mcfg._make( [259200,60,64800,40,20,5,100] )

def filter1( a, b ):
  if b < 0:
    return a
  else:
    return min( [a,b] )

def filter2( a, b, tt, tm ):
## largest tier less than or equal to tm
  t1 = [t for t in tt if t <= tm][-1]
  it1 = tt.index(t1)
  aa = a[it1]
  if b < 0:
    return aa
  else:
    return min( [aa,b] )

npy = {'1hrClimMon':24*12, 'daily':365, u'Annual':1, u'fx':0.01, u'1hr':24*365, u'3hr':8*365,
       u'monClim':12, u'Timestep':100, u'6hr':4*365, u'day':365, u'1day':365, u'mon':12, u'yr':1,
       u'1mon':12, 'month':12, 'year':1, 'monthly':12, 'hr':24*365, 'other':24*365,
        'subhr':24*365, 'Day':365, '6h':4*365, '3 hourly':8*365, '':1 }

## There are 4 cmor variables with blank frequency ....

def vol01( sz, v, npy, freq, inx ):
  n1 = npy[freq]
  s = sz[inx.uid[v].stid]
  assert type(s) == type(1), 'Non-integer size found for %s' % v
  assert type(n1) in (type(1),type(0.)), 'Non-number "npy" found for %s, [%s]' % (v,freq)
  return s*n1

class col_list(object):
  def __init__(self):
    self.a = collections.defaultdict(list)

class col_count(object):
  def __init__(self):
    self.a = collections.defaultdict(int)

class dreqQuery(object):
  __doc__ = """Methods to analyse the data request, including data volume estimates"""
  def __init__(self,dq=None,tierMax=1):
    if dq == None:
      self.dq = dreq.loadDreq()
    else:
      self.dq=dq
    self.rlu = {}
    for i in self.dq.coll['objective'].items:
      k = '%s.%s' % (i.mip,i.label)
      assert not k in self.rlu, 'Duplicate label in objectives: %s' % k
      self.rlu[k] = i.uid

    self.cmvFilter = cmvFilter( self )
    self.tierMax = tierMax

    self.mips = set( [x.label for x in self.dq.coll['mip'].items ] )
    self.mips = ['AerChemMIP', 'C4MIP', 'CFMIP', 'DAMIP', 'DCPP', 'FAFMIP', 'GeoMIP', 'GMMIP', 'HighResMIP', 'ISMIP6', 'LS3MIP', 'LUMIP', 'OMIP', 'PMIP', 'RFMIP', 'ScenarioMIP', 'VolMIP', 'CORDEX', 'DynVar', 'SIMIP', 'VIACSAB']
    self.mipsp = ['DECK','CMIP6',] + self.mips[:-4]

    self.experiments = set( [x.uid for x in self.dq.coll['experiment'].items ] )
    self.exptByLabel = {}
    for x in self.dq.coll['experiment'].items:
      if x.label in self.exptByLabel:
        print ( 'ERROR: experiment label duplicated: %s' % x.label )
      self.exptByLabel[x.label] = x.uid
    self.mipls = sorted( list( self.mips ) )

    self.default_mcfg = nt_mcfg._make( [259200,60,64800,40,20,5,100] )
    self.mcfg = self.default_mcfg._asdict()
    ##for k in self.default_mcfg.__dict__.keys():
      ##self.mcfg[k] = self.default_mcfg.__dict__[k]
    self.szcfg()
    self.requestItemExpAll(  )

  def szcfg(self):
    szr = {'100km':64800, '1deg':64800, '2deg':16200 }
    self.szss = {}
    self.sz = {}
    self.szg = collections.defaultdict( dict )
    self.szgss = collections.defaultdict( dict )
    for i in self.dq.coll['spatialShape'].items:
      type = 'a'
      if i.levelFlag == False:
        ds =  i.dimensions.split( '|' )
        if ds[-1] in ['site', 'basin']:
          vd = ds[-2]
        else:
          vd = ds[-1]
 
        if vd[:4] == 'olev' or vd == 'rho':
          type = 'o'
          nz = self.mcfg['nlo']
        elif vd[:4] == 'alev':
          nz = self.mcfg['nla']
        elif vd in ['slevel','sdepth']:
          nz = self.mcfg['nls']
        elif vd == 'aslevel':
          nz = self.mcfg['nlas']
        else:
          mlg.prnt( 'Failed to parse dimensions %s' % i.dimensions )
          raise
      else:
        nz = i.levels

      dims = set( i.dimensions.split( '|' ) )
      if 'latitude' in dims and 'longitude' in dims:
        if type == 'o':
          nh = self.mcfg['nho']
        else:
          nh = self.mcfg['nha']
      else:
        nh = 10

      self.szss[i.uid] = nh*nz
      for k in szr:
        self.szgss[k][i.uid] = szr[k]*nz
    for i in self.dq.coll['structure'].items:
      s = 1
      if i.odims != '':
        s = s*5
      self.sz[i.uid] = self.szss[i.spid]*s
      for k in szr:
        self.szg[k][i.uid] = self.szgss[k][i.spid]*s

  def getRequestLinkByMip( self, mipSel ):
    """Return the set of request links which are associated with specified MIP"""

    if type(mipSel) == type( {} ):
      return self.getRequestLinkByMipObjective(self,mipSel)

    if type(mipSel) == type(''):
      t1 = lambda x: x == mipSel
    elif type(mipSel) == type(set()):
      t1 = lambda x: x in mipSel

    s = set()
    for i in self.dq.coll['objectiveLink'].items:
      if t1(i.label):
        s.add( self.dq.inx.uid[i.rid] )

    ##self.rqs = list({self.dq.inx.uid[i.rid] for i in self.dq.coll['objectiveLink'].items if t1(i.label) })
    self.rqs = list( s )
    return self.rqs

  def getRequestLinkByMipObjective( self, mipSel ):
    """Return the set of request links which are associated with specified MIP and its objectives"""

    assert type(mipSel) == type( {} ),'Argument must be a dictionary, listing objectives for each MIP'

    s = set()
    for i in self.dq.coll['objectiveLink'].items:
      if i.label in mipSel:
        if len(mipSel[i]) == 0 or self.dq.inx.uid[i.oid].label in mipSel[i]:
          s.add( self.dq.inx.uid[i.rid] )
    ##self.rqs = list({self.dq.inx.uid[i.rid] for i in self.dq.coll['objectiveLink'].items if t1(i.label) })
    self.rqs = list( s )
    return self.rqs

  def getRequestLinkByObjective( self, objSel ):
    """Return the set of request links which are associated with specified objectives"""
    if type(objSel) == type(''):
      t1 = lambda x: x == self.rlu[objSel]
    elif type(objSel) == type(set()):
      t1 = lambda x: x in [self.rlu[i] for i in objSel]

    s = set()
    for i in self.dq.coll['objectiveLink'].items:
      if t1(i.label):
        s.add( self.dq.inx.uid[i.oid] )
##
    self.rqs = list( s )
    ##self.rqs = list({self.dq.inx.uid[i.rid] for i in self.dq.coll['objectiveLink'].items if t1(i.oid) })
    return self.rqs

  def varGroupXexpt(self, rqList ):
    """For a list of request links, return a list of variable group IDs for each experiment"""
    self.cc = collections.defaultdict( list )
    ## dummy = {self.cc[i.expt].append(i.rlid) for i in self.dq.coll['requestItem'].items if i.rlid in {j.uid for j in rqList} }
    return self.cc

  def yearsInRequest(self, rql ):
    self.ntot = sum( [i.ny for i in self.dq.coll['requestItem'].items if i.rlid == rql.uid] )
    return self.ntot

  def rqlByExpt( self, l1, ex, pmax=2, expFullEx=False ):
    """rqlByExpt: return a set of request links for an experiment"""
##
    inx = self.dq.inx

    if ex != None:
    
      exi = self.dq.inx.uid[ex]
      if exi._h.label == 'experiment':
        exset = set( [ex,exi.egid,exi.mip] )
      else:
        exset = set( self.esid_to_exptList(ex,deref=False,full=expFullEx) )
##
## rql is the set of all request links which are associated with a request item for this experiment set
##
   
      l1p = set()
      for i in l1:
        if i.preset < 0 or i.preset <= pmax:
          if i.esid in exset:
            l1p.add(i)
    else:
      exset = None
      l1p = l1

    rql0 = set()
    for i in l1p:
       rql0.add(i.rlid)

    rqlInv = set()
    for u in rql0:
      if inx.uid[u]._h.label == 'remarks':
        rqlInv.add( u )
    if len(rqlInv) != 0:
      mlg.prnt ( 'WARNING.001.00002: %s invalid request links from request items ...' % len(rqlInv) )
    rql = set()
    for u in rql0:
       if inx.uid[u]._h.label != 'remarks':
         rql.add( u ) 

    return rql, l1p, exset

  def varsByRql( self, rql, pmax=2, intersection=False): 
      """The complete set of variables associated with a set of rquest links."""
      inx = self.dq.inx
      cc1 = collections.defaultdict( set )
      for i in rql:
        o = inx.uid[i]
        if o.opt == 'priority':
          p = int( float( o.opar ) )
          assert p in [1,2,3], 'Priority incorrectly set .. %s, %s, %s' % (o.label,o.title, o.uid)
          cc1[inx.uid[i].mip].add( (inx.uid[i].refid,p) )
        else:
          cc1[inx.uid[i].mip].add( inx.uid[i].refid )

      if intersection:
        ccv = {}
#
# set of request variables for each MIP
#
        for k in cc1:
          thisc = reduce( operator.or_, [set( inx.iref_by_sect[vg].a['requestVar'] ) for vg in cc1[k] ] )
          rqvgs = collections.defaultdict( set )
          for x in cc1[k]:
            if type(x) == type( () ):
              rqvgs[x[0]].add( x[1] )
            else:
              rqvgs[x].add( 3 )
          
          s = set()
          for vg in rqvgs:
            for l in inx.iref_by_sect[vg].a['requestVar']:
              if inx.uid[l].priority <= min(pmax,max(rqvgs[vg])):
                s.add( inx.uid[l].vid )
          ccv[k] = s

        if len( ccv.keys() ) < len( list(imips) ):
          vars = set()
        else:
          vars =  reduce( operator.and_, [ccv[k] for k in ccv] )
      else:
        rqvgs = collections.defaultdict( set )
        for k in cc1:
          for x in cc1[k]:
            if type(x) == type( () ):
              rqvgs[x[0]].add( x[1] )
            else:
              rqvgs[x].add( 3 )
          
###To obtain a set of variables associated with this collection of variable groups:

        vars = set()
        for vg in rqvgs:
          for l in inx.iref_by_sect[vg].a['requestVar']:
            if inx.uid[l].priority <= min(pmax,max(rqvgs[vg])):
               vars.add(inx.uid[l].vid)

        ##col1 = reduce( operator.or_, [set( inx.iref_by_sect[vg].a['requestVar'] ) for vg in rqvg ] )
### filter out cases where the request does not point to a CMOR variable.
    ##vars = {vid for vid in vars if inx.uid[vid][0] == u'CMORvar'}

      thisvars = set()
      for vid in vars:
         if inx.uid[vid]._h.label == u'CMORvar':
             thisvars.add(vid)

      return thisvars

  def volByExpt( self, l1, ex, pmax=1, cc=None, retainRedundantRank=False, intersection=False,expFullEx=False, adsCount=False ):
    """volByExpt: calculates the total data volume associated with an experiment/experiment group and a list of request items.
          The calculation has some approximations concerning the number of years in each experiment group.
          cc: an optional collector, to accumulate indexed volumes. """
##
    inx = self.dq.inx
    imips = set()
    for i in l1:
      imips.add(i.mip)
    
    rql, l1p, exset = self.rqlByExpt( l1, ex, pmax=pmax, expFullEx=expFullEx )
    verbose = False
    if verbose:
      for i in rql:
        r = inx.uid[i]
        print ( '%s, %s, %s' % (r.label, r.title, r.uid) )

    dn = False
    if dn:
## obsolete code deleted here
      pass
    elif ex != None:
      
      exi = self.dq.inx.uid[ex]
      if exi._h.label == 'experiment':
        exset = set( [ex,exi.egid,exi.mip] )
#####
    if len( rql ) == 0:
      self.vars = set()
      return (0,{},{} )

## The complete set of variables associated with these requests:
    vars = self.varsByRql( rql, pmax=pmax, intersection=intersection) 
    tm = 3
    if tm == 0:
      pass
    elif tm == 1:
      pass
##
## filter by configuration option and rank
##
    if not retainRedundantRank:
      len1 = len(vars)
      cmv = self.cmvFilter.filterByChoiceRank(cmv=vars)

      vars = cmv
    
    self.vars = vars

    e = {}
    for u in rql:
### for request variables which reference the variable group attached to the link, add the associate CMOR variables, subject to priority
      i = inx.uid[u]
      e[i.uid] = set()
      si = collections.defaultdict( list )
      for x in inx.iref_by_sect[i.refid].a['requestVar']:
           if inx.uid[x].priority <= pmax:
              e[i.uid].add( inx.uid[x].vid )

              if verbose:
                cmv = inx.uid[inx.uid[x].vid]
                if cmv._h.label == 'CMORvar':
                  si[ cmv.mipTable ].append( inx.uid[x].label )
#
# for each variable, calculate the maximum number of years across all the request links which reference that variable.
##
## for each request item we have nymax, nenmax, nexmax.
##
    nymg = collections.defaultdict( dict )
##
## if dataset count rather than volume is wanted, use item 3 from rqiExp tuple.
    if adsCount:
      irqi = 3
    else:
      irqi = 2

    sgg = set()
    for v in vars:
      s = set()
      sg = collections.defaultdict( set )
      cc2 = collections.defaultdict( set )
      cc2s = collections.defaultdict( c1s )
      for i in l1p:
##################
        if (exset == None or i.esid in exset) and v in e[i.rlid]:
          ix = inx.uid[i.esid]
          rl = inx.uid[i.rlid]
          sgg.add( rl.grid )
          if rl.grid in ['100km','1deg','2deg']:
            grd = rl.grid
          else:
            grd = 'native'

          this = None
          if exset == None:
            thisz = 100
## 
## for a single experiment, look up n years, and n ensemble.
## should have nstart????
##
          elif exi._h.label == 'experiment' or ix._h.label == 'experiment':
            this = None
            if ex in self.rqiExp[i.uid][1]:
              this = self.rqiExp[i.uid][1][ex]
            elif ix.uid in self.rqiExp[i.uid][1]:
              this = self.rqiExp[i.uid][1][ix.uid]
            if this != None:
              thisns = this[-3]
              thisny = this[-2]
              thisne = this[-1]
              cc2s[grd].a[u].add( filter1( thisns*thisny*thisne, i.nymax) )
          else:
            thisz = None
            if 'experiment' in inx.iref_by_sect[i.esid].a:
              for u in inx.iref_by_sect[i.esid].a['experiment']:
                if u in self.rqiExp[i.uid][1]:
                  this = self.rqiExp[i.uid][1][u]
                  thisns = this[-3]
                  thisny = this[-2]
                  thisne = this[-1]
                  cc2s[grd].a[u].add( filter1( thisns*thisny*thisne, i.nymax) )

          ##if thisny != None and thisne != None:
              ##cc2s[grd].a[i.esid].add( thisny*thisne )
          
          if exset != None:
            sg[grd].add( self.rqiExp[i.uid][irqi] )
      
      ##if len(s) == 0:
        ##nym[v] = 0
      ##else:
###
### sum over experiments of maximum within each experiment
###
        ##nym[v] = sum( [max( cc2[k] ) for k in cc2] )
      for g in sg:
        nymg[v][g] = sum( [max( cc2s[g].a[k] ) for k in cc2s[g].a] )

    szv = {}
    ov = []
    for v in vars:
      szv[v] = self.sz[inx.uid[v].stid]*npy[inx.uid[v].frequency]
      ov.append( self.dq.inx.uid[v] )
    ee = self.listIndexDual( ov, 'mipTable', 'label', acount=None, alist=None, cdict=szv, cc=cc )

    ff = {}
    for v in vars:
      if adsCount:
        ff[v] = 1
      else:
        if 'native' in nymg[v]:
          ff[v] = self.sz[ inx.uid[v].stid ] * npy[inx.uid[v].frequency]
          ny = nymg[v]['native']
        else:
          if len( nymg[v] ) > 1:
            print ( '########### Selecting first in list .............' )
          ks0 = nymg[v].keys()
          if len(ks0) == 0:
            ##print 'WARN: no nymg entry for %s [%s]' % (v,ex)
            ff[v] = 0.
            ny = 0.
          else:
            ks = list( nymg[v].keys() )[0]
            ny = nymg[v][ks]
            ff[v] = self.szg[ks][ inx.uid[v].stid ] * npy[inx.uid[v].frequency]

        if inx.uid[v].frequency != 'monClim':
          ff[v] = ff[v]*ny
    self.ngptot = sum( [  ff[v]  for v in vars] )
    return (self.ngptot, ee, ff )

  def esid_to_exptList(self,esid,deref=False,full=False):
    if not esid in self.dq.inx.uid:
      mlg.prnt ( 'Attempt to dereferece invalid uid: %s' % esid )
      raise

    if self.dq.inx.uid[esid]._h.label == 'experiment':
      expts = [esid,]
    elif self.dq.inx.uid[esid]._h.label != 'remarks':
      if esid in self.dq.inx.iref_by_sect and 'experiment' in self.dq.inx.iref_by_sect[esid].a:
        expts = list( self.dq.inx.iref_by_sect[esid].a['experiment'][:] )
      else:
        expts = []

## add in groups and mips for completeness
##
      if full:
        if self.dq.inx.uid[esid]._h.label == 'mip':
          s = set()
          for e in expts:
            if self.dq.inx.uid[e]._h.label != 'experiment':
              mlg.prnt ( 'ERROR: %s, %s, %s ' % (esid,e, self.dq.inx.uid[e].title ) )
            s.add( self.dq.inx.uid[e].egid )
          for i in s:
            expts.append( i )
        expts.append( esid )
    else:
      ##print ( 'WARNING: request link not associated with valid experiment group' )
      ##raise
      return None

    if self.tierMax > 0:
      expts1 = []
      for i in expts:
        if self.dq.inx.uid[i]._h.label == 'experiment':
          if self.dq.inx.uid[i].tier[0] <= self.tierMax:
            expts1.append( i )
        elif self.dq.inx.uid[i]._h.label == 'exptgroup':
          if self.dq.inx.uid[i].tierMin <= self.tierMax:
            expts1.append( i )
        else:
            expts1.append( i )
    else:
      expts1 = expts

    if deref:
      return [self.dq.inx.uid[e] for e in expts1]
    else:
      return expts1
  
##
## need to call this on load
## then use instead of i.ny etc below
##
  def requestItemExpAll( self ):
    self.rqiExp = {}
    for rqi in self.dq.coll['requestItem'].items:
      a,b,c,d = self.requestItemExp( rqi )
      if a != None:
        self.rqiExp[rqi.uid] = (a,b,c,d)

  def requestItemExp( self, rqi ):
    assert rqi._h.label == "requestItem", 'Argument to requestItemExp must be a requestItem'
    u = rqi.esid
    if self.dq.inx.uid[u]._h.label == 'experiment':
      expts = [u,]
    elif self.dq.inx.uid[u]._h.label != 'remarks':
      if u in self.dq.inx.iref_by_sect and 'experiment' in self.dq.inx.iref_by_sect[u].a:
        expts = self.dq.inx.iref_by_sect[u].a['experiment']
      else:
        expts = []
    else:
      # print ( 'WARNING: request link not associated with valid experiment group'  )
      ##rqi.__info__()
      ##raise
      return (None, None, None, None)

    if self.tierMax > 0:
      expts = [i for i in expts if self.dq.inx.uid[i].tier[0] <= self.tierMax]

    self.multiTierOnly = False
    if self.multiTierOnly:
      expts = [i for i in expts if len(self.dq.inx.uid[i].tier) > 1]
      print ('Len expts: %s' % len(expts) )

    if len(expts) > 0:
      e = [self.dq.inx.uid[i] for i in expts]
      for i in e:
        if i._h.label != 'experiment':
          mlg.prnt ( 'ERROR: %s, %s, %s ' % ( u,i._h.label, i.label, i.title ) )
      ##dat = [ (i.ntot, i.yps, i.ensz, i.tier, i.nstart, filter1(i.yps,rqi.nymax), filter2(i.ensz,rqi.nenmax,i.tier,self.tierMax) ) for i in e]
      dat2 = {}
      for i in e:
        dat2[i.uid] = (i.ntot, i.yps, i.ensz, i.tier, i.nstart, filter1(i.yps,rqi.nymax), filter2(i.ensz,rqi.nenmax,i.tier,self.tierMax) )
        ##print i.label, rqi.title, dat2[i.uid]
      ### number of 
      nytot = sum( [dat2[x][-2]*dat2[x][-3] for x in dat2 ] )
      netot = sum( [dat2[x][-1] for x in dat2 ] )
      ##print 'debug1:: ',dat, nytot, netot
    else:
      dat2 = {}
      nytot = 0
      netot = 0
    
    return (expts, dat2, nytot, netot )

  def setTierMax( self, tierMax ):
    """Set the maxium tier and recompute request sizes"""
    if tierMax != self.tierMax:
      self.tierMax = tierMax
      self.requestItemExpAll(  )

  def summaryByMip( self, pmax=1 ):
    bytesPerFloat = 2.
    for m in self.mipls:
      v = self.volByMip( m, pmax=pmax )
      mlg.prnt ( '%12.12s: %6.2fTb' % (m,v*bytesPerFloat*1.e-12) )

  def rqiByMip( self, mip):

    if mip == 'TOTAL':
        mip = self.mips
    if type(mip) in [type( '' ),type( u'') ]:
      if mip not in self.mips:
        mlg.prnt ( self.mips )
        raise baseException( 'rqiByMip: Name of mip not recognised: %s' % mip )
      l1 = [i for i in  self.dq.coll['requestItem'].items if i.mip == mip]
    elif type(mip) in [ type( set()), type( [] ) ]:
      nf = [ m for m in mip if m not in self.mips]
      if len(nf) > 0:
          raise baseException( 'rqiByMip: Name of mip(s) not recognised: %s' % str(nf) )
      l1 = [i for i in  self.dq.coll['requestItem'].items if i.mip in mip]
    elif type(mip) == type( dict()):
      nf = [ m for m in mip if m not in self.mips]
      if len(nf) > 0:
        raise baseException( 'rqiByMip: Name of mip(s) not recognised: %s' % str(nf) )
      l1 = []
      for i in  self.dq.coll['requestLink'].items:
        if i.mip in mip:
          ok = False
          if len( mip[i.mip] ) == 0:
            ok = True
          else:
            for ol in self.dq.inx.iref_by_sect[i.uid].a['objectiveLink']:
              o = self.dq.inx.uid[ol]
              if self.dq.inx.uid[o.oid].label in mip[i.mip]:
                ok = True
          if ok:
              if 'requestItem' in self.dq.inx.iref_by_sect[i.uid].a:
                for u in self.dq.inx.iref_by_sect[i.uid].a['requestItem']:
                  l1.append( self.dq.inx.uid[u] )
    else:
      raise baseException( 'rqiByMip: "mip" (1st explicit argument) should be type string or set: %s -- %s' % (mip, type(mip))   )

    return l1

  def checkDir(self,odir,msg):
      if not os.path.isdir( odir ):
         try:
            os.mkdir( odir )
         except:
            print ('\n\nFailed to make directory "%s" for: %s: make necessary subdirectories or run where you have write access' % (odir,msg) )
            print ( '\n\n' )
            raise
         print ('Created directory %s for: %s' % (odir,msg) )


  def xlsByMipExpt(self,m,ex,pmax,odir='xls'):
    import scope_utils
    mxls = scope_utils.xlsTabs(self,tiermax=self.tierMax,pmax=pmax)

    ##tabs = makeTables.tables( self, mips, odir=odir )
    mlab = makeTables.setMlab( m )
    ##mm = list( m )[0]
    ##r = overviewTabs.r1( self, tiermax=1, pmax=pmax, only=mm )

    mxls.run( m, mlab=mlab )

  def xlsByMipExptxx(self,m,ex,pmax,odir='xls'):

    mips = ['AerChemMIP', 'C4MIP', 'CFMIP', 'DAMIP', 'DCPP', 'FAFMIP', 'GeoMIP', 'GMMIP', 'HighResMIP', 'ISMIP6', 'LS3MIP', 'LUMIP', 'OMIP', 'PMIP', 'RFMIP', 'ScenarioMIP', 'VolMIP', 'CORDEX', 'DynVar', 'SIMIP', 'VIACSAB']
    tabs = makeTables.tables( self, mips, odir=odir )
    cc = collections.defaultdict( c1 )
    mlab = makeTables.setMlab( m )
    cc[mlab].dd = {}
    cc[mlab].ee = {}
    if m == 'TOTAL':
        l1 = self.rqiByMip( set( mips ) )
    else:
        l1 = self.rqiByMip( m )

    ###print 'len l1:',len(l1)
    self.checkDir( odir, 'xls files' )
    tabs.accReset()
    vcc = collections.defaultdict( int  )
    if ex == None and False:
      for m2 in self.mipsp:
        if m2 == 'TOTAL':
          xx = self.dq.coll['experiment'].items
        else:
          xx = [i for i in self.dq.coll['experiment'].items if i.mip == m2]
        xxi = set( [i.label for i in xx] )
        cc[mlab].ee[m2] = xx
##
## populate collector ....
##
        if m2 != 'TOTAL':
            for i in xx:
              tabs.doTable(m,l1,i.uid,pmax,self.cc,acc=False,cc=vcc,exptids=xxi)
        tabs.doTable(m,l1,m2,pmax,self.cc,cc=vcc,exptids=xxi)

    for i in self.dq.coll['experiment'].items:
            tabs.doTable(m,l1,i.uid,pmax,cc, mlab=mlab,acc=False)
    ex = 'TOTAL'
         
    print 'xlsBxMip ... ', m, ex
    l1 = self.rqiByMip( set( mips ) )
    tabs.doTable(m,l1,ex,pmax,cc, mlab=mlab)
      
  def volByMip( self, mip, pmax=2, retainRedundantRank=False, intersection=False, adsCount=False, exptid=None):

    l1 = self.rqiByMip( mip )
      
    #### The set of experiments/experiment groups:
    if exptid == None:
      ##exps = self.mips
      exps = self.experiments
    else:
      exps = set( [exptid,] )
      ##print exptid, exps
    
    self.volByE = {}
    vtot = 0
    cc = collections.defaultdict( col_count )
    self.allVars = set()
    for e in exps:
      expts = self.esid_to_exptList(e,deref=True,full=False)
      if expts not in  [None,[]]:
        ###print 'EXPTS: ',e,len(expts), list( expts )[0].label
        for ei in expts:
          self.volByE[ei.label] = self.volByExpt( l1, ei.uid, pmax=pmax, cc=cc, retainRedundantRank=retainRedundantRank, intersection=intersection, adsCount=adsCount )
          vtot += self.volByE[ei.label][0]
        self.allVars = self.allVars.union( self.vars )
      ##else:
        ##print 'No expts found: ',e
    self.indexedVol = cc

    return vtot

  def listIndexDual(self, ll, a1, a2, acount=None, alist=None, cdict=None, cc=None ):
    do_count = acount != None
    do_list = alist != None
    assert not (do_count and do_list), 'It is an error to request both list and count'
    if not (do_count or do_list):
      acount = '__number__'
      do_count = True

    if cc == None:
      if do_count:
        cc = collections.defaultdict( col_count )
      elif do_list:
        cc = collections.defaultdict( col_list )

    if do_count:
      for l in ll:
        if cdict != None:
          v = cdict[l.uid]
        elif acount == '__number__':
          v = 1
        else:
          v = l.__dict__[acount]

        cc[ l.__dict__[a1] ].a[ l.__dict__[a2] ] += v
    elif do_list:
      for l in ll:
        if cdict != None:
          v = cdict[l.uid]
        elif alist == '__item__':
          v = l
        else:
          v = l.__dict__[alist]
        cc[ l.__dict__[a1] ].a[ l.__dict__[a2] ].append( v )

    od = {}
    for k in cc.keys():
      d2 = {}
      for k2 in cc[k].a.keys():
        d2[k2] = cc[k].a[k2]
      od[k] = d2
    return od

class dreqUI(object):
  """Data Request Command line.
-------------------------
      -v : print version and exit;
      --unitTest : run some simple tests;
      -m <mip>:  MIP of list of MIPs (comma separated; for objective selection see note [1] below);
      -h :       help: print help text;
      -e <expt>: experiment;
      -t <tier> maxmum tier;
      -p <priority>  maximum priority;
      --xls : Create Excel file with requested variables;
      --xlsDir <directory> : Directory in which to place variable listing [xls];
      --printLinesMax <n>: Maximum number of lines to be printed
      --printVars  : If present, a summary of the variables fitting the selection options will be printed
      --intersection : Analyse the intersection of requests rather than union.

NOTES
-----
[1] A set of objectives within a MIP can be specified in the command line. The extended syntax of the "-m" argument is:
-m <mip>[:objective[.obj2[.obj3 ...]]][,<mip2]...]

e.g.
drq -m HighResMIP:Ocean.DiurnalCycle
"""
  def __init__(self,args):
    self.adict = {}
    self.knownargs = {'-m':('m',True), '-p':('p',True), '-e':('e',True), '-t':('t',True), \
                      '-h':('h',False), '--printLinesMax':('plm',True), \
                      '--printVars':('vars',False), '--intersection':('intersection',False), \
                      '--count':('count',False), \
                      '--xlsDir':('xlsdir',True), '--xls':('xls',False) \
                       } 
    aa = args[:]
    notKnownArgs = []
    while len(aa) > 0:
      a = aa.pop(0)
      if a in self.knownargs:
        b = self.knownargs[a][0]
        if self.knownargs[a][1]:
          v = aa.pop(0)
          self.adict[b] = v
        else:
          self.adict[b] = True
      else:
        notKnownArgs.append(a)

    assert self.checkArgs( notKnownArgs ), 'FATAL ERROR 001: Arguments not recognised: %s' % (str(notKnownArgs) )

    if 'm' in self.adict:
      if self.adict['m'].find( ':' ) != -1:
        ee = {}
        for i in self.adict['m'].split(','):
          bits =  i.split( ':' )
          if len( bits ) == 1:
             ee[bits[0]] = []
          else:
             assert len(bits) == 2, 'Cannot parse %s' % self.adict['m']
             ee[bits[0]] = bits[1].split( '.' )
        self.adict['m'] = ee
      else:
        self.adict['m'] = set(self.adict['m'].split(',') )

    integerArgs = set( ['p','t','plm'] )
    for i in integerArgs.intersection( self.adict ):
      self.adict[i] = int( self.adict[i] )

    self.intersection = self.adict.get( 'intersection', False )

  
  def checkArgs( self, notKnownArgs ):
    if len( notKnownArgs ) == 0:
      return True
    print ('--------------------------------------')
    print ('------------  %s Arguments Not Recognised ------------' % len(notKnownArgs) )
    k = 0
    for x in notKnownArgs:
      k += 1
      if x[1:] in self.knownargs:
        print ( '%s PERHAPS %s instead of %s' % (k, x[1:],x) )
      elif '-%s' % x in self.knownargs:
        print ( '%s PERHAPS -%s instead of %s' % (k, x,x) )
      elif x[0] == '\xe2':
        print ( '%s POSSIBLY -- (double hyphen) instead of long dash in %s' % (k, x) )
    print ('--------------------------------------')

    return len( notKnownArgs ) == 0
      
  def run(self, dq=None):
    if 'h' in self.adict:
      mlg.prnt ( self.__doc__ )
      return

    if not 'm' in self.adict:
      mlg.prnt ( 'Current version requires -m argument'  )
      mlg.prnt ( self.__doc__ )
      sys.exit(0)

    if dq == None:
      self.dq = dreq.loadDreq()
    else:
      self.dq = None

    self.sc = dreqQuery( dq=self.dq )

    ok = True
    for i in self.adict['m']:
        if i not in self.sc.mips:
          ok = False
          mlg.prnt ( 'NOT FOUND: %s' % i )

    eid = None
    ex = None
    if 'e' in self.adict:
      ex = self.adict['e']
      for i in self.dq.coll['experiment'].items:
        if i.label == self.adict['e']:
          eid = i.uid
      assert eid != None, 'Experiment %s not found' % self.adict['e']

    assert ok,'Available MIPs: %s' % str(self.sc.mips)
    adsCount = self.adict.get( 'count', False )

    tierMax = self.adict.get( 't', 1 )
    self.sc.setTierMax(  tierMax )
    pmax = self.adict.get( 'p', 1 )
    self.getVolByMip(pmax,eid,adsCount)
    makeXls = self.adict.get( 'xls', False )
    if makeXls:
      mips = self.adict['m']
      odir = self.adict.get( 'xlsdir', 'xls' )
      self.sc.checkDir( odir, 'xls files' )

      print mips, eid
      self.sc.xlsByMipExpt(mips,eid,pmax,odir=odir)

  def getVolByMip(self,pmax,eid,adsCount):

    v0 = self.sc.volByMip( self.adict['m'], pmax=pmax, intersection=self.intersection, adsCount=adsCount, exptid=eid )
    #mlg.prnt ( '%7.2fTb' % (v0*2.*1.e-12) )
    mlg.prnt ( 'getVolByMip: %s [%s]' % (v0,makeTables.vfmt(v0*2.)) )
    cc = collections.defaultdict( int )
    for e in self.sc.volByE:
      for v in self.sc.volByE[e][2]:
          cc[v] += self.sc.volByE[e][2][v]
    x = 0
    for v in cc:
      x += cc[v]
    
    if python2:
      vl = sorted( cc.keys(), cmp=cmpd(cc).cmp, reverse=True )
    else:
      vl = sorted( cc.keys(), key=lambda x: cc[x], reverse=True )
    if self.adict.get( 'vars', False ):
      printLinesMax = self.adict.get( 'plm', 20 )
      if printLinesMax > 0:
        mx = min( [printLinesMax,len(vl)] )
      else:
        mx = len(vl)

      for v in vl[:mx]:
        mlg.prnt ( '%s: %7.2fTb' % (self.dq.inx.uid[v].label, cc[v]*2.*1.e-12) )

