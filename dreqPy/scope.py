"""Date Request Scoping module
---------------------------
The scope.py module contains the dreqQuery class and a set of ancilliary functions. The dreqQuery class contains methods for analysing the data request.
"""
import dreq
from utilities import cmvFilter
import collections, string, operator
import sys

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
  def __init__(self,dq=None,tierMax=-1):
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
    self.mips = { i.mip for i in  self.dq.coll['requestItem'].items}
    self.mipls = sorted( list( self.mips ) )

    self.default_mcfg = nt_mcfg._make( [259200,60,64800,40,20,5,100] )
    self.mcfg = {}
    for k in self.default_mcfg.__dict__.keys():
      self.mcfg[k] = self.default_mcfg.__dict__[k]
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
          print ( 'Failed to parse dimensions %s' % i.dimensions )
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
    elif type(mipSel) == type({1,2}):
      t1 = lambda x: x in mipSel
    self.rqs = list({self.dq.inx.uid[i.rid] for i in self.dq.coll['objectiveLink'].items if t1(i.label) })
    return self.rqs

  def getRequestLinkByObjective( self, objSel ):
    """Return the set of request links which are associated with specified objectives"""
    if type(objSel) == type(''):
      t1 = lambda x: x == self.rlu[objSel]
    elif type(objSel) == type({1,2}):
      t1 = lambda x: x in {self.rlu[i] for i in objSel}

    self.rqs = list({self.dq.inx.uid[i.rid] for i in self.dq.coll['objectiveLink'].items if t1(i.oid) })
    return self.rqs

  def varGroupXexpt(self, rqList ):
    """For a list of request links, return a list of variable group IDs for each experiment"""
    self.cc = collections.defaultdict( list )
    dummy = {self.cc[i.expt].append(i.rlid) for i in self.dq.coll['requestItem'].items if i.rlid in {j.uid for j in rqList} }
    return self.cc

  def yearsInRequest(self, rql ):
    self.ntot = sum( [i.ny for i in self.dq.coll['requestItem'].items if i.rlid == rql.uid] )
    return self.ntot

  def volByExpt( self, l1, ex, exptList, pmax=2, cc=None, retainRedundantRank=False, intersection=False ):
    """volByExpt: calculates the total data volume associated with an experiment/experiment group and a list of request items.
          The calculation has some approximations concerning the number of years in each experiment group."""
##
## cc: an optional collector, to accumulate indexed volumes
##
    inx = self.dq.inx
    imips = {i.mip for i in l1}
##
## rql is the set of all request links which are associated with a request item for this experiment set
##
    rql0 = {i.rlid for i in l1 if i.esid == ex}
    rqlInv = {u for u in rql0 if inx.uid[u]._h.label == 'remarks' }
    if len(rqlInv) != 0:
      print ( 'WARNING.001.00002: %s invalid request links from request items ...' % len(rqlInv) )
    rql = {u for u in rql0 if inx.uid[u]._h.label != 'remarks' }

## The complete set of variables associated with these requests:
    tm = 1
    if tm == 0:
      rqvg = list({inx.uid[i].refid for i in rql})
    else:
      cc1 = collections.defaultdict( set )
      for i in rql:
        cc1[inx.uid[i].mip].add( inx.uid[i].refid )

      if intersection:
        ccv = {}
#
# set of request variables for each MIP
##
        for k in cc1:
          thisc = reduce( operator.or_, [set( inx.iref_by_sect[vg].a['requestVar'] ) for vg in cc1[k] ] )
          ccv[k] = {inx.uid[l].vid for l in list(thisc) if inx.uid[l].priority <= pmax}

        if len( ccv.keys() ) < len( list(imips) ):
          vars = set()
        else:
          vars =  reduce( operator.and_, [ccv[k] for k in ccv] )
      else:
        rqvg = reduce( operator.or_, [cc1[k] for k in cc1] )

###To obtain a set of variables associated with this collection of variable groups:

        col1 = reduce( operator.or_, [set( inx.iref_by_sect[vg].a['requestVar'] ) for vg in rqvg ] )

###The collector col1 here accumulates all the record uids, resulting in a single collection. These are request variables, to get a set of CMOR variables at priority <= pmax:
        vars = {inx.uid[l].vid for l in list(col1) if inx.uid[l].priority <= pmax}
##
## if looking for the union, would have to do a filter here ... after looking up which vars are requested by each MIP ...
##
## possibly some code re-arrangement would help.
## e.g. create a set for each MIP a couple of lines back ....

### filter out cases where the request does not point to a CMOR variable.
    ##vars = {vid for vid in vars if inx.uid[vid][0] == u'CMORvar'}
    vars = {vid for vid in vars if inx.uid[vid]._h.label == u'CMORvar'}
##
## filter by configuration option and rank
##
    if not retainRedundantRank:
      len1 = len(vars)
      cmv = self.cmvFilter.filterByChoiceRank(cmv=vars)
      ## print 'After filter: %s [%s]' % (len(cmv),len1)

      vars = cmv
    
    self.vars = vars

    e = {}
    for u in rql:
### for request variables which reference the variable group attached to the link, add the associate CMOR variables, subject to priority
      i = inx.uid[u]
      e[i.uid] = { inx.uid[x].vid for x in inx.iref_by_sect[i.refid].a['requestVar'] if inx.uid[x].priority <= pmax}
#
# for each variable, calculate the maximum number of years across all the request links which reference that variable.
##
## for each request item we have nymax, nenmax, nexmax.
##
    nym = {}
    for v in vars:
      ### for each request item, check if v is in the set of variables and then add the number of years.
      nym[v] = max( {self.rqiExp[i.uid][2] for i in l1 if i.esid == ex and v in e[i.rlid]} )

    szv = {}
    ov = []
    for v in vars:
      szv[v] = self.sz[inx.uid[v].stid]*npy[inx.uid[v].frequency]
      ov.append( self.dq.inx.uid[v] )
    ee = self.listIndexDual( ov, 'frequency', 'label', acount=None, alist=None, cdict=szv, cc=cc )
    ff = {}
    for v in vars:
      ff[v] = self.sz[ inx.uid[v].stid ] * npy[inx.uid[v].frequency] * nym[v]
    self.ngptot = sum( [  ff[v]  for v in vars] )
    return (self.ngptot, ee, ff )

  def esid_to_exptList(self,esid,deref=False):
    if not esid in self.dq.inx.uid:
      print ( 'Attempt to dereferece invalid uid: %s' % esid )
      raise

    if self.dq.inx.uid[esid]._h.label == 'experiment':
      expts = [esid,]
    elif self.dq.inx.uid[esid]._h.label != 'remarks':
      if esid in self.dq.inx.iref_by_sect and 'experiment' in self.dq.inx.iref_by_sect[esid].a:
        expts = self.dq.inx.iref_by_sect[esid].a['experiment']
      else:
        expts = []
    else:
      print ( 'WARNING: request link not associated with valid experiment group' )
      raise

    if self.tierMax > 0:
      expts = [i for i in expts if self.dq.inx.uid[i].tier <= self.tierMax]

    if deref:
      return [self.dq.inx.uid[e] for e in expts]
    else:
      return expts
  
##
## need to call this on load
## then use instead of i.ny etc below
##
  def requestItemExpAll( self ):
    self.rqiExp = {}
    for rqi in self.dq.coll['requestItem'].items:
      a,b,c = self.requestItemExp( rqi )
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
      print ( 'WARNING: request link not associated with valid experiment group'  )
      i.__info__()
      raise

    if self.tierMax > 0:
      expts = [i for i in expts if self.dq.inx.uid[i].tier <= self.tierMax]

    if len(expts) > 0:
      e = [self.dq.inx.uid[i] for i in expts]
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
      print ( '%12.12s: %6.2fTb' % (m,v*bytesPerFloat*1.e-12) )

  def volByMip( self, mip, pmax=2, retainRedundantRank=False):

    if type(mip) in {type( '' ),type( u'') }:
      if mip not in self.mips:
        print ( self.mips )
        raise baseException( 'volByMip: Name of mip not recognised: %s' % mip )
      l1 = [i for i in  self.dq.coll['requestItem'].items if i.mip == mip]
    elif type(mip) == type( set()):
      nf = [ m for m in mip if m not in self.mips]
      if len(nf) > 0:
        raise baseException( 'volByMip: Name of mip(s) not recognised: %s' % str(nf) )
      l1 = [i for i in  self.dq.coll['requestItem'].items if i.mip in mip]
    else:
      raise baseException( 'volByMip: "mip" (1st explicit argument) should be type string or set: %s -- %s' % (mip, type(mip))   )
      
    #### The set of experiments/experiment groups:
    exps = {i.esid for i in l1}
    self.volByE = {}
    vtot = 0
    cc = collections.defaultdict( col_count )
    self.allVars = set()
    for e in exps:
      expts = self.esid_to_exptList(e,deref=True)
      self.volByE[e] = self.volByExpt( l1, e, expts, pmax=pmax, cc=cc, retainRedundantRank=retainRedundantRank )
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
      -m <mip>:  MIP of list of MIPs (comma separated);
      -h :       help: print help text;
      -t <tier> maxmum tier;
      -p <priority>  maximum priority;
      --printLinesMax <n>: Maximum number of lines to be printed
      --printVars  : If present, a summary of the variables fitting the selection options will be printed
"""
  def __init__(self,args):
    self.adict = {}
    self.knownargs = {'-m':('m',True), '-p':('p',True), '-t':('t',True), '-h':('h',False), '--printLinesMax':('plm',True), '--printVars':('vars',False)} 
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

    integerArgs = {'p','t','plm'}
    for i in integerArgs.intersection( self.adict ):
      self.adict[i] = int( self.adict[i] )

  def run(self, dq=None):
    if 'h' in self.adict:
      print self.__doc__
      return

    if not 'm' in self.adict:
      print 'Current version requires -m argument' 
      print self.__doc__
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
          print 'NOT FOUND: ',i
    assert ok,'Available MIPs: %s' % str(sc.mips)

    tierMax = self.adict.get( 't', 2 )
    sc.setTierMax(  tierMax )
    pmax = self.adict.get( 'p', 2 )
    v0 = sc.volByMip( self.adict['m'], pmax=pmax )
    print '%7.2fTb' % (v0*2.*1.e-12)
    cc = collections.defaultdict( int )
    for e in sc.volByE:
      for v in sc.volByE[e][2]:
          cc[v] += sc.volByE[e][2][v]
    x = 0
    for v in cc:
      x += cc[v]
    
    vl = sorted( cc.keys(), cmp=cmpd(cc).cmp, reverse=True )
    if self.adict.get( 'vars', False ):
      printLinesMax = self.adict.get( 'plm', 20 )
      if printLinesMax > 0:
        mx = min( [printLinesMax,len(vl)] )
      else:
        mx = len(vl)

      for v in vl[:mx]:
        print self.dq.inx.uid[v].label, '%7.2fTb' % (cc[v]*2.*1.e-12)
