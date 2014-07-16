#!/usr/bin/env python

import sys, pprint, rebalance

fee, desiredport = rebalance.readconfig(sys.argv[1])

starterport = rebalance.read_cmc_pnl_to_portfdict(sys.argv[2],desiredport)

portfolios = [starterport]

print "starter portfolio"
rebalance.printport(starterport)
starterrating = rebalance.isrebalancegood(starterport)
print "starter rating", starterrating

totalspend = 0
fees = 0
for buycode,buyamount in zip(sys.argv[3:][::2],sys.argv[3:][1::2]):
   print  "buy ",buyamount," of ",buycode
   portfolios.append(rebalance.rebalance(float(buyamount),portfolios[-1],buycode))
   totalspend = totalspend + float(buyamount)
   fees = fees + fee
   rebalance.printport(portfolios[-1])
   print "rating of ",rebalance.isrebalancegood(portfolios[-1])

print "totalspend is: ",totalspend," (inc fees is: ",totalspend + fees," )"
print "fees are: ",fees," which is ",fees/(totalspend + fees) * 100," per cent"


