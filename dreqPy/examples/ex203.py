import sys, os

if len(sys.argv) > 1 and __name__ == '__main__':
  if os.path.isdir( sys.argv[1] ):
    if os.path.isfile( '%s/scope.py' % sys.argv[1] ):
      sys.path.insert(0, sys.argv[1] )
      import scope
    else:
      print ( 'No scope.py in specified directory' )
      sys.exit(0)
  else:
    print ( 'Specified directory does not exist: %s' % sys.argv[1] )
    sys.exit(0)
else:
  from dreqPy import scope

sc = scope.dreqQuery()

## set bytes per floating point number to be 2, assuming 50% compression
bytesPerFloat = 2.

priorityMax = 3
def runExample( priorityMax ):
    ll = ['C4MIP','CFMIP','LUMIP']
    ee = {}
    ss = 0.
    for l in ll:
      x = sc.volByMip( l, pmax=priorityMax )*1.e-12*bytesPerFloat
      print ( '%9s  %5.1fTb'  % ( l,x ) )
      ss += x
    z = sc.volByMip( set(ll), pmax=priorityMax )*1.e-12*bytesPerFloat

    print ( 'Combined:  %5.1fTb'  % z )
    print ( 'Overlap:   %5.1fTb'  % (ss-z) )

    sc.setTierMax( 1 )
    z1 = sc.volByMip( set(ll), pmax=priorityMax )*1.e-12*bytesPerFloat
    sc.setTierMax( 2 )
    z2 = sc.volByMip( set(ll), pmax=priorityMax )*1.e-12*bytesPerFloat
    print ( '' )
    print ( 'Combined, tier 1 only:  %5.1fTb'  % z1 )
    print ( 'Combined, tier 1+2 only:  %5.1fTb'  % z2 )

print ( '######### All variables ###########' )
priorityMax = 3
runExample( priorityMax )
print ( '######### Top priority variables ###########' )
priorityMax = 1
runExample( priorityMax )
