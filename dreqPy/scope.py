"""Date Request Scoping module
---------------------------
The scope.py module contains the dreqQuery class and a set of ancilliary functions. The dreqQuery class contains methods for analysing the data request.
"""
import dreq
from utilities import cmvFilter 
import collections, string, operator
import sys

python2 = True
if sys.version_info[0] == 3:
  python2 = False
  from functools import reduce
  from utilP3 import mlog3
  mlg = mlog3()
else:
  from utilP2 import mlog
  mlg = mlog()

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

npy = {'daily':365, u'Annual':1, u'fx':0.01, u'1hr':24*365, u'3hr':8*365, u'monClim':12, u'Timestep':100, u'6hr':4*365, u'day':365, u'1day':365, u'mon':12, u'yr':1, u'1mon':12, 'month':12, 'year':1, 'monthly':12, 'hr':24*365, 'other':24*365, 'subhr':24*365, 'Day':365, '6h':4*365,
'3 hourly':8*365, '':1 }
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
    self.mipls = sorted( list( self.mips ) )

    self.default_mcfg = nt_mcfg._make( [259200,60,64800,40,20,5,100] )
    self.mcfg = self.default_mcfg._asdict()
    ##for k in self.default_mcfg.__dict__.keys():
      ##self.mcfg[k] = self.default_mcfg.__dict__[k]
    self.szcfg()
    self.requestItemExpAll(  )

  def szcfg(self):
    self.szss = {}
    self.sz = {}
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
    for i in self.dq.coll['structure'].items:
      s = self.szss[i.spid]
      if i.odims != '':
        s = s*5
      self.sz[i.uid] = s

  def getRequestLinkByMip( self, mipSel ):
    """Return the set of request links which are associated with specified MIP"""
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

  def volByExpt( self, l1, ex, pmax=1, cc=None, retainRedundantRank=False, intersection=False,expFullEx=False ):
    """volByExpt: calculates the total data volume associated with an experiment/experiment group and a list of request items.
          The calculation has some approximations concerning the number of years in each experiment group.
          cc: an optional collector, to accumulate indexed volumes. """
##
    inx = self.dq.inx
    imips = set()
    for i in l1:
      imips.add(i.mip)
    ##imips = {i.mip for i in l1}
    
    rql, l1p, exset = self.rqlByExpt( l1, ex, pmax=pmax, expFullEx=expFullEx )
    dn = False
    if dn:
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

#####
    if len( rql ) == 0:
      self.vars = set()
      return (0,{},{} )

## The complete set of variables associated with these requests:
    vars = self.varsByRql( rql, pmax=pmax, intersection=intersection) 
    tm = 3
    if tm == 0:
      s = set()
      for i in rql:
        s.add( inx.uid[i].refid )
      rqvg = list( s )
    elif tm == 1:
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

###The collector col1 here accumulates all the record uids, resulting in a single collection. These are request variables, to get a set of CMOR variables at priority <= pmax:
        ##vars = set()
        ##for l in list(col1):
           ##if inx.uid[l].priority <= pmax:
             ##vars.add(inx.uid[l].vid)
##

### filter out cases where the request does not point to a CMOR variable.
    ##vars = {vid for vid in vars if inx.uid[vid][0] == u'CMORvar'}
      thisvars = set()
      for vid in vars:
         if inx.uid[vid]._h.label == u'CMORvar':
             thisvars.add(vid)
      vars = thisvars
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
      for x in inx.iref_by_sect[i.refid].a['requestVar']:
           if inx.uid[x].priority <= pmax:
              e[i.uid].add( inx.uid[x].vid )
#
# for each variable, calculate the maximum number of years across all the request links which reference that variable.
##
## for each request item we have nymax, nenmax, nexmax.
##
    nym = {}
    for v in vars:
      s = set()
      for i in l1p:
        if i.esid in exset and v in e[i.rlid]:
          s.add( self.rqiExp[i.uid][2] )
      ##nym[v] = max( {self.rqiExp[i.uid][2] for i in l1p if i.esid == ex and v in e[i.rlid]} )
      if len(s) == 0:
        nym[v] == 0
      else:
        nym[v] = max( s )

    szv = {}
    ov = []
    for v in vars:
      szv[v] = self.sz[inx.uid[v].stid]*npy[inx.uid[v].frequency]
      ov.append( self.dq.inx.uid[v] )
    ee = self.listIndexDual( ov, 'mipTable', 'label', acount=None, alist=None, cdict=szv, cc=cc )
    ff = {}
    for v in vars:
      ff[v] = self.sz[ inx.uid[v].stid ] * npy[inx.uid[v].frequency] * nym[v]
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
          if self.dq.inx.uid[i].tier <= self.tierMax:
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
      a,b,c = self.requestItemExp( rqi )
      if a != None:
        self.rqiExp[rqi.uid] = (a,b,c)

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
      return (None, None, None)

    if self.tierMax > 0:
      expts = [i for i in expts if self.dq.inx.uid[i].tier <= self.tierMax]

    if len(expts) > 0:
      e = [self.dq.inx.uid[i] for i in expts]
      for i in e:
        if i._h.label != 'experiment':
          mlg.prnt ( 'ERROR: %s, %s, %s ' % ( u,i._h.label, i.label, i.title ) )
      dat = [ (i.ntot, i.yps, i.ensz, i.nstart, filter1(i.yps,rqi.nymax), filter1(i.ensz,rqi.nenmax) ) for i in e]
      nytot = sum( [x[-2]*x[-1] for x in dat ] )
    else:
      dat = [ (0,0,0,0,0) ]
      nytot = 0
    
    return (expts, dat, nytot )
    

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

    if type(mip) in [type( '' ),type( u'') ]:
      if mip not in self.mips:
        mlg.prnt ( self.mips )
        raise baseException( 'rqiByMip: Name of mip not recognised: %s' % mip )
      l1 = [i for i in  self.dq.coll['requestItem'].items if i.mip == mip]
    elif type(mip) == type( set()):
      nf = [ m for m in mip if m not in self.mips]
      if len(nf) > 0:
        raise baseException( 'rqiByMip: Name of mip(s) not recognised: %s' % str(nf) )
      l1 = [i for i in  self.dq.coll['requestItem'].items if i.mip in mip]
    else:
      raise baseException( 'rqiByMip: "mip" (1st explicit argument) should be type string or set: %s -- %s' % (mip, type(mip))   )
    return l1
      
  def volByMip( self, mip, pmax=2, retainRedundantRank=False, intersection=False):

    l1 = self.rqiByMip( mip )
      
    #### The set of experiments/experiment groups:
    exps = set()
    for i in l1:
      exps.add( i.esid )
    exps = self.mips
    self.volByE = {}
    vtot = 0
    cc = collections.defaultdict( col_count )
    self.allVars = set()
    for e in exps:
      expts = self.esid_to_exptList(e,deref=True,full=False)
      if expts != None:
        self.volByE[e] = self.volByExpt( l1, e, pmax=pmax, cc=cc, retainRedundantRank=retainRedundantRank, intersection=intersection )
        vtot += self.volByE[e][0]
        self.allVars = self.allVars.union( self.vars )
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
      -m <mip>:  MIP of list of MIPs (comma separated);
      -h :       help: print help text;
      -t <tier> maxmum tier;
      -p <priority>  maximum priority;
      --printLinesMax <n>: Maximum number of lines to be printed
      --printVars  : If present, a summary of the variables fitting the selection options will be printed
      --intersection : Analyse the intersection of requests rather than union.
"""
  def __init__(self,args):
    self.adict = {}
    self.knownargs = {'-m':('m',True), '-p':('p',True), '-t':('t',True), '-h':('h',False), '--printLinesMax':('plm',True), '--printVars':('vars',False), '--intersection':('intersection',False)} 
    aa = args[:]
    while len(aa) > 0:
      a = aa.pop(0)
      if a in self.knownargs:
        b = self.knownargs[a][0]
        if self.knownargs[a][1]:
          v = aa.pop(0)
          self.adict[b] = v
        else:
          self.adict[b] = True

    if 'm' in self.adict:
      self.adict['m'] = set(self.adict['m'].split(',') )

    integerArgs = set( ['p','t','plm'] )
    for i in integerArgs.intersection( self.adict ):
      self.adict[i] = int( self.adict[i] )

    self.intersection = self.adict.get( 'intersection', False )

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

    sc = dreqQuery( dq=self.dq )

    ok = True
    for i in self.adict['m']:
        if i not in sc.mips:
          ok = False
          mlg.prnt ( 'NOT FOUND: ',i )
    assert ok,'Available MIPs: %s' % str(sc.mips)

    tierMax = self.adict.get( 't', 2 )
    sc.setTierMax(  tierMax )
    pmax = self.adict.get( 'p', 2 )
    v0 = sc.volByMip( self.adict['m'], pmax=pmax, intersection=self.intersection )
    mlg.prnt ( '%7.2fTb' % (v0*2.*1.e-12) )
    cc = collections.defaultdict( int )
    for e in sc.volByE:
      for v in sc.volByE[e][2]:
          cc[v] += sc.volByE[e][2][v]
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
        mlg.prnt ( self.dq.inx.uid[v].label, '%7.2fTb' % (cc[v]*2.*1.e-12) )
