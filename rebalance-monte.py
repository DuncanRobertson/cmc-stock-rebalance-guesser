#!/usr/bin/env python

import csv, sys, pprint, random, rebalance

def usage():
   print "%s <config.ini> <profitloss.csv> cashtospenddollars iterationcount  .." % sys.argv[0]
   sys.exit(1)

try:
   fee, desiredport = rebalance.readconfig(sys.argv[1])
   cmcpnlcsvfilename = sys.argv[2]
   addedcash = float(sys.argv[3])
   numtries = int(sys.argv[4])
except:
   usage()

starterport = rebalance.read_cmc_pnl_to_portfdict(cmcpnlcsvfilename,desiredport)

portfolios = {}

print "starter portfolio"
rebalance.printport(starterport)
starterrating = rebalance.isrebalancegood(starterport)
print "starter rating", starterrating

# first gather all the single buy choices.
for asxcode in starterport.keys():
   newport = rebalance.rebalance(addedcash - fee,starterport,asxcode)
   newrating = rebalance.isrebalancegood(newport)
   # print asxcode,newrating
   # if newrating > starterrating or asxcode == 'TOTALS:':
   if asxcode == rebalance.TOTALS:
      # print "dont bother with", asxcode
      pass
   else:
      portfolios[newrating] = [addedcash,asxcode]


asxcodestochoose = starterport.keys()
asxcodestochoose.remove(rebalance.TOTALS)

maxlen = 0

for numpurchases in xrange(2,len(asxcodestochoose) + 1):
   # now split into four random amounts and buy four random ones.
   print
   print ".. trying options for ",numpurchases," number of purchases..."
   for i in xrange(numtries):
      if not i % 700:
	 rebalance.update_progress(float(i)/float(numtries))
      buyamounts = rebalance.constrained_sum_sample_pos(numpurchases,int(addedcash - (fee * numpurchases)))
      buycode = []
      intermedport = []
      buypattern = []
      for purchase in xrange(numpurchases):
	 buycode.append(random.choice(asxcodestochoose))
	 if purchase == 0:
	    intermedport.append(rebalance.rebalance(buyamounts[purchase],starterport,buycode[purchase]))
	 else:
	    intermedport.append(rebalance.rebalance(buyamounts[purchase],intermedport[purchase - 1],buycode[purchase]))
	 buypattern.append(buyamounts[purchase])
	 buypattern.append(buycode[purchase])
      newport = intermedport[-1]
      newrating = rebalance.isrebalancegood(newport)
      portfolios[newrating] = buypattern
         

# now rate the results and just show the best of each buy count.
   
sortratings = portfolios.keys()
sortratings.sort()
maxlen = len(asxcodestochoose) * 2 + 1
prevlen = maxlen
for rating in sortratings:
   if maxlen >= len(portfolios[rating]):
      maxlen = len(portfolios[rating])
      if maxlen != prevlen:
         # have found the best rated of the next number of fees.
         prevlen = maxlen
         print
         print "buy the following combos"
         portresult = [starterport]
         for buyamount,buycode in zip(portfolios[rating][::2],portfolios[rating][1::2]):
            print buyamount,buycode
            portresult.append(rebalance.rebalance(buyamount,portresult[-1],buycode))
            # rebalance.printport(portresult[-1])
         rebalance.printport(portresult[-1])
         print "rating: ",rebalance.isrebalancegood(portresult[-1])
         print "broker fees: % ", len(portfolios[rating])/2 * fee / addedcash * 100
            
