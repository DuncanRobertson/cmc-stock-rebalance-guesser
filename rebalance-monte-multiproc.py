#!/usr/bin/env python

import csv, sys, pprint, random, rebalance

import multiprocessing

def usage():
   print "%s <config.ini> <profitloss.csv> cashtospenddollars iterationcount  .." % sys.argv[0]
   sys.exit(1)

if __name__ == '__main__':
   try:
      fee, desiredport = rebalance.readconfig(sys.argv[1])
      cmcpnlcsvfilename = sys.argv[2]
      addedcash = float(sys.argv[3])
      numtries = int(sys.argv[4])
   except:
      usage()

   starterport = rebalance.read_cmc_pnl_to_portfdict(cmcpnlcsvfilename,desiredport)

   buychoices = {}

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
	 buychoices[newrating] = [addedcash,asxcode]

   asxcodestochoose = starterport.keys()
   asxcodestochoose.remove(rebalance.TOTALS)

   maxlen = 0

def calcpurchases(statusbar,numtries,numpurchases,return_queue):
   buychoices = {}

   # print ".. trying options for ",numpurchases," number of purchases...tries",numtries
   # now running multiprocessor, only put out a status bar for the first job.
   for i in xrange(numtries):
      if (not i % 700) and statusbar:
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
      buychoices[newrating] = buypattern

   # just grab the top rated one, we dont have to pass the whole lot back
   # this step a holdover from when the non-parallel code putting it all in one global dict.
   sortratings = buychoices.keys()
   sortratings.sort()
   # print "ending worker with numtries",numtries,"numpurchases",numpurchases

   return_queue.put({ sortratings[0] : buychoices[sortratings[0]] })

#cribbed a bit from http://natpoor.blogspot.com/2014/07/python-multiprocessing-and-queues.html
if __name__ == '__main__':
   result_queue = multiprocessing.Queue()
   proc_list = list()

   # fire off the threads, this could be better as the larger buy combos run longer, so
   # TODO is to break these down.
   statusbar = True
   for numpurchases in xrange(2,len(asxcodestochoose) + 1):
      workertries = numtries/numpurchases
      # print "starting ",numpurchases,"workers with a total of ",numtries,"tries"
      for i in xrange(numpurchases):
         # print "   starting worker with numtries",workertries,"numpurchases",numpurchases
         a_proc = multiprocessing.Process(target=calcpurchases,args=(statusbar,workertries,numpurchases,result_queue))
         statusbar = False
         proc_list.append(a_proc)
         a_proc.start()

   # wait for workers to finish and gather the results.
   for p in proc_list:
      tempbuychoices = result_queue.get()
      buychoices.update(tempbuychoices)
      p.join()

   # now rate the results and just show the best of each buy count.
      
   sortratings = buychoices.keys()
   sortratings.sort()
   maxlen = len(asxcodestochoose) * 2 + 1
   prevlen = maxlen
   for rating in sortratings:
      if maxlen >= len(buychoices[rating]):
	 maxlen = len(buychoices[rating])
	 if maxlen != prevlen:
	    # have found the best rated of the next number of fees.
	    prevlen = maxlen
	    print
	    print "buy the following combos"
	    portresult = [starterport]
	    for buyamount,buycode in zip(buychoices[rating][::2],buychoices[rating][1::2]):
	       print buyamount,buycode
	       portresult.append(rebalance.rebalance(buyamount,portresult[-1],buycode))
	       # rebalance.printport(portresult[-1])
	    rebalance.printport(portresult[-1])
	    print "rating: ",rebalance.isrebalancegood(portresult[-1])
	    print "broker fees: % ", len(buychoices[rating])/2 * fee / addedcash * 100
            
