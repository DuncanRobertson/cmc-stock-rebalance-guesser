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
   if asxcode == 'TOTALS:':
      # print "dont bother with", asxcode
      pass
   else:
      portfolios[newrating] = (addedcash,asxcode)


asxcodestochoose = starterport.keys()
asxcodestochoose.remove('TOTALS:')

# now split into two random amounts and buy two random ones.
for i in xrange(numtries):
   buyamounts = rebalance.constrained_sum_sample_pos(2,int(addedcash - (fee * 2)))
   buy1amount = buyamounts[0]
   buy2amount = buyamounts[1]
   buy1code = random.choice(asxcodestochoose)
   buy2code = random.choice(asxcodestochoose)
   intermedport = rebalance.rebalance(buy1amount,starterport,buy1code)
   newport = rebalance.rebalance(buy2amount,intermedport,buy2code)
   newrating = rebalance.isrebalancegood(newport)
   # if newrating > starterrating:
   #  # print "dont bother with", buy1amount, buy1code, buy2amount, buy2code
   #   pass
   # else:
   portfolios[newrating] = (buy1amount, buy1code, buy2amount, buy2code)

# now split into three random amounts and buy three random ones.
for i in xrange(numtries):
   buyamounts = rebalance.constrained_sum_sample_pos(3,int(addedcash - (fee * 3)))
   buy1amount = buyamounts[0]
   buy2amount = buyamounts[1]
   buy3amount = buyamounts[2]
   buy1code = random.choice(asxcodestochoose)
   buy2code = random.choice(asxcodestochoose)
   buy3code = random.choice(asxcodestochoose)
   intermedport1 = rebalance.rebalance(buy1amount,starterport,buy1code)
   intermedport2 = rebalance.rebalance(buy2amount,intermedport1,buy2code)
   newport = rebalance.rebalance(buy3amount,intermedport2,buy3code)
   newrating = rebalance.isrebalancegood(newport)
   #if newrating > starterrating:
   #   # print "dont bother with", buy1amount, buy1code, buy2amount, buy2code
   #   pass
   #else:
   portfolios[newrating] = (buy1amount, buy1code, buy2amount, buy2code,buy3amount,buy3code)


# now rate the results and just show the best of each buy count.
   
sortratings = portfolios.keys()
sortratings.sort()
maxlen = 10
prevlen = maxlen
for rating in sortratings:
   if maxlen >= len(portfolios[rating]):
      maxlen = len(portfolios[rating])
      if maxlen != prevlen:
         # have found the best rated of the next number of fees.
         prevlen = maxlen
         print "buy the following combos"
         portresult = [starterport]
         for buyamount,buycode in zip(portfolios[rating][::2],portfolios[rating][1::2]):
            print buyamount,buycode
            portresult.append(rebalance.rebalance(buyamount,portresult[-1],buycode))
            rebalance.printport(portresult[-1])
         
         print "rating: ",rebalance.isrebalancegood(portresult[-1])
         print "broker fees: % ", len(portfolios[rating])/2 * fee / addedcash * 100
            
