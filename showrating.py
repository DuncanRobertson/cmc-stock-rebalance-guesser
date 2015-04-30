#!/usr/bin/env python

import csv, sys, pprint, random, rebalance, copy

def usage():
   print "Just shows the portfolio and it's rating from one or more ProfitLoss CSV files"
   print "%s <config.ini> <profitloss.csv>  .." % sys.argv[0]
   sys.exit(1)

for cmcpnlcsvfilename in  sys.argv[2:]:
   fee, desiredport = rebalance.readconfig(sys.argv[1])
   starterport = rebalance.read_cmc_pnl_to_portfdict(cmcpnlcsvfilename,desiredport)

   print "portfolio, loaded from the file ",cmcpnlcsvfilename
   rebalance.printport(starterport)
   starterrating = rebalance.isrebalancegood(starterport)
   print "rating (i.e. how close to the desired balance):", starterrating
   print

