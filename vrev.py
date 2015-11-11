"""This module has a class which will analyse the usage of variables in the data request"""
import operator
from dreqPy import dreq

class checkVar(object):
  """checkVar
--------
Class to analyse the usage of variables in the data request.
"""
  def __init__(self,dq):
    self.dq = dq
    self.mips = {i.label for i in  dq.coll['mip'].items}
    for i in ['PDRMIP', 'DECK', 'VIACSAB', 'SolarMIP', 'CMIP6' ]:
      self.mips.discard(i)

  def chk(self,vn):
    ks = [i for i in dq.coll['var'].items if i.label == vn ]

    v = ks[0]
    l = dq.inx.iref_by_sect[v.uid].a['CMORvar']

## set of all request variables 
    s = set()
    for i in l:
      for j in dq.inx.iref_by_sect[i].a['requestVar']:
        s.add(j)

## filter out the ones whch link to a remark
    s0 = {i for i in s if dq.inx.uid[dq.inx.uid[i].vgid]._h.label != 'remarks'}

## set of request groups

    s1  = {dq.inx.uid[i].vgid for i in s0}

    #s2 = set()
#for i in s1:
  #for j in dq.inx.iref_by_sect[i].a['requestLink']:
    #s2.add(j)
    s2 = reduce( operator.or_, [set(dq.inx.iref_by_sect[i].a['requestLink']) for i in s1 if dq.inx.iref_by_sect[i].a.has_key('requestLink')] )

    mips = {dq.inx.uid[i].mip for i in s2}
    self.missing = self.mips.difference( mips )
    self.inc = mips

#############
  def chkCmv(self,cmvid):
    dq = self.dq
    s = set( dq.inx.iref_by_sect[cmvid].a['requestVar'] )

## filter out the ones whch link to a remark

    s0 = {i for i in s if dq.inx.uid[dq.inx.uid[i].vgid]._h.label != 'remarks'}

## set of request groups

    s1  = {dq.inx.uid[i].vgid for i in s0}

    ll = [set(dq.inx.iref_by_sect[i].a['requestLink']) for i in s1 if dq.inx.iref_by_sect[i].a.has_key('requestLink')]
    if len(ll) == 0:
      return set()
    s2 = reduce( operator.or_, ll) 

    mips = {dq.inx.uid[i].mip for i in s2}
    return mips

if __name__ == '__main__':
  dq = dreq.loadDreq()
  c = checkVar(dq)
  c.chk( 'tas' )
  print c.inc, c.missing
