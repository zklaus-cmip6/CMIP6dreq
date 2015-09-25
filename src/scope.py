import dreq
import collections, string

class baseException(Exception):
  """Basic exception for general use in code."""

  def __init__(self,msg):
    self.msg = 'scope:: %s' % msg

  def __str__(self):
    return repr( self.msg )

  def __repr__(self):
    return self.msg

nt_mcfg = collections.namedtuple( 'mcfg', ['nho','nlo','nha','nla','nlas','nls','nh1'] )

npy = {'daily':365, u'Annual':1, u'fx':0.01, u'1hr':24*365, u'3hr':8*365, u'monClim':12, u'Timestep':100, u'6hr':4*365, u'day':365, u'1day':365, u'mon':12, u'yr':1, u'1mon':12, 'month':12, 'year':1, 'monthly':12, 'hr':24*365, 'other':24*365, 'subhr':24*365, 'Day':365, '6h':4*365,
'3 hourly':8*365, '':1 }
## There are 4 cmor variables with blank frequency ....

def vol01( sz, v, npy, freq, inx ):
  n1 = npy[freq]
  s = sz[inx.uid[v][1].stid]
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
  def __init__(self,dq=None):
    if dq == None:
      self.dq = dreq.loadDreq()
    else:
      self.dq=dq
    self.rlu = {}
    for i in self.dq.coll['objective'].items:
      k = '%s.%s' % (i.mip,i.label)
      assert not self.rlu.has_key(k), 'Duplicate label in objectives: %s' % k
      self.rlu[k] = i.uid

    self.mips = { i.mip for i in  self.dq.coll['requestItem'].items}
    self.mipls = sorted( list( self.mips ) )

    self.default_mcfg = nt_mcfg._make( [259200,60,64800,40,20,5,100] )
    self.mcfg = {}
    for k in self.default_mcfg.__dict__.keys():
      self.mcfg[k] = self.default_mcfg.__dict__[k]
    self.szcfg()

  def szcfg(self):
    self.szss = {}
    self.sz = {}
    for i in self.dq.coll['spatialShape'].items:
      type = 'a'
      if i.levelFlag == 'false':
        ds =  string.split( i.dimensions, '|' )
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
          print 'Failed to parse dimensions %s' % i.dimensions
          raise
      else:
        nz = i.levels

      dims = set( string.split( i.dimensions, '|' ) )
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
    self.rqs = list({self.dq.inx.uid[i.rid][1] for i in self.dq.coll['objectiveLink'].items if t1(i.label) })
    return self.rqs

  def getRequestLinkByObjective( self, objSel ):
    """Return the set of request links which are associated with specified objectives"""
    if type(objSel) == type(''):
      t1 = lambda x: x == self.rlu[objSel]
    elif type(objSel) == type({1,2}):
      t1 = lambda x: x in {self.rlu[i] for i in objSel}

    self.rqs = list({self.dq.inx.uid[i.rid][1] for i in self.dq.coll['objectiveLink'].items if t1(i.oid) })
    return self.rqs

  def varGroupXexpt(self, rqList ):
    """For a list of request links, return a list of variable group IDs for each experiment"""
    self.cc = collections.defaultdict( list )
    dummy = {self.cc[i.expt].append(i.rlid) for i in self.dq.coll['requestItem'].items if i.rlid in {j.uid for j in rqList} }
    return self.cc

  def yearsInRequest(self, rql ):
    self.ntot = sum( [i.ny for i in self.dq.coll['requestItem'].items if i.rlid == rql.uid] )
    return self.ntot

  def volByExpt( self, l1, ex, pmax=2, cc=None ):
    """volByExpt: calculates the total data volume associated with an experiment/experiment group and a list of request items.
          The calculation has some approximations concerning the number of years in each experiment group."""
##
## cc: an optional collector, to accumulate indexed volumes
##
    inx = self.dq.inx
    rql = {i.rlid for i in l1 if i.expt == ex}

## The complete set of variables associated with these requests:
    rqvg = list({inx.uid[i][1].refid for i in rql})

###To obtain a set of variables associated with this collection of variable groups:
    col1 = set()
    x = {tuple( {col1.add(i) for i in inx.iref_by_sect[vg].a['requestVar']} ) for vg in rqvg}
###The collector col1 here accumulates all the record uids, resulting in a single collection. These are request variables, to get a set of CMOR variables at priority <= pmax:
    vars = {inx.uid[l][1].vid for l in list(col1) if inx.uid[l][1].priority <= pmax}

### filter out cases where the request does not point to a CMOR variable.
    vars = {vid for vid in vars if inx.uid[vid][0] == u'CMORvar'}

    e = {}
    for u in rql:
### for request variables which reference the variable group attached to the link, add the associate CMOR variables, subject to priority
      i = inx.uid[u][1]
      e[i.uid] = { inx.uid[x][1].vid for x in inx.iref_by_sect[i.refid].a['requestVar'] if inx.uid[x][1].priority <= pmax}

#
# for each variable, calculate the maximum number of years across all the request links which reference that variable.
#
    nym = {}
    for v in vars:
      ### for each request item, check if v is in the set of variables and then add the number of years.
      nym[v] = max( {i.ny for i in l1 if i.expt == ex and v in e[i.rlid]} )

    szv = {}
    ov = []
    for v in vars:
      szv[v] = self.sz[inx.uid[v][1].stid]*npy[inx.uid[v][1].frequency]
      ov.append( self.dq.inx.uid[v][1] )
    ee = self.listIndexDual( ov, 'frequency', 'mipTable', acount=None, alist=None, cdict=szv, cc=cc )
    self.ngptot = sum( [  self.sz[inx.uid[v][1].stid]* npy[inx.uid[v][1].frequency] *nym[v]  for v in vars] )
    return (self.ngptot, ee )

  def summaryByMip( self, pmax=1 ):
    bytesPerFloat = 2.
    for m in self.mipls:
      v = self.volByMip( m, pmax=pmax )
      print '%12.12s: %6.2fTb' % (m,v*bytesPerFloat*1.e-12)

  def volByMip( self, mip, pmax=2):

    if type(mip) in {type( '' ),type( u'') }:
      if mip not in self.mips:
        print self.mips
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
    exps = {i.expt for i in l1}
    self.volByE = {}
    vtot = 0
    cc = collections.defaultdict( col_count )
    for e in exps:
      self.volByE[e] = self.volByExpt( l1, e, pmax=pmax, cc=cc )
      vtot += self.volByE[e][0]
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
