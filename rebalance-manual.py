#!/usr/bin/env python

import sys, pprint, rebalance

def usage():
   print "%s <config.ini> <profitloss.csv> [profitloss2.csv ...]  ASXCODE ammount [ASXCODE amount ....]  .." % sys.argv[0]
   print "can accept one or more profitloss.csv files on command line, one or more ASX codes and amount to purchase"
   sys.exit(1)
inputcsvfiles = []

try:
   fee, desiredport, singleproc = rebalance.readconfig(sys.argv[1])
   argcount = 2
   while sys.argv[argcount].lower()[-4:] == '.csv':
      inputcsvfiles.append(sys.argv[argcount])
      argcount = argcount + 1
   # print "argcount when leaving loop was ",argcount
   buysequence = zip(sys.argv[argcount:][::2],sys.argv[argcount:][1::2])
   print buysequence
except:
   usage()

# print buysequence
# print  zip(buysequence)

starterports = []
firstcsv = True
for csvfile in inputcsvfiles:
   starterports.append(rebalance.read_cmc_pnl_to_portfdict(csvfile,desiredport))
   if not firstcsv:
      starterports.append(rebalance.add_portfdict(starterports[-2],starterports[-1]))
   else:
      firstcsv = False

portfolios = [starterports[-1]]
starterport = starterports[-1]

print "starter portfolio"
rebalance.printport(starterport)
starterrating = rebalance.isrebalancegood(starterport)
print "starter rating", starterrating

totalspend = 0
fees = 0
for buycode,buyamount in buysequence:
   print  "buy ",buyamount," of ",buycode
   portfolios.append(rebalance.rebalance(float(buyamount),portfolios[-1],buycode))
   totalspend = totalspend + float(buyamount)
   fees = fees + fee
   rebalance.printport(portfolios[-1])
   print "rating of ",rebalance.isrebalancegood(portfolios[-1])

print "totalspend is: ",totalspend," (inc fees is: ",totalspend + fees," )"
print "fees are: ",fees," which is ",fees/(totalspend + fees) * 100," per cent"

