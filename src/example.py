
import scope
sc = scope.dreqQuery()

## set bytes per floating point number to be 2, assuming 50% compression
bytesPerFloat = 2.

priorityMax = 3
ll = ['C4MIP','CFMIP','LUMIP']
ee = {}
ss = 0.
for l in ll:
  x = sc.volByMip( l, pmax=priorityMax )*1.e-12*bytesPerFloat
  print '%9s  %5.1fTb'  % ( l,x )
  ss += x
z = sc.volByMip( set(ll), pmax=priorityMax )*1.e-12*bytesPerFloat


print 'Combined:  %5.1fTb'  % z
print 'Overlap:   %5.1fTb'  % (ss-z)
