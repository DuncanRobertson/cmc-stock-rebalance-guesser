#!/usr/bin/env python

import csv, sys, pprint, random, rebalance, copy

import multiprocessing

# set this to true if we just want to run sequentially, helpful for debug or performance tests.
# singlethread = True
singlethread = False

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

   print "starter portfolio, loaded from the file ",cmcpnlcsvfilename
   rebalance.printport(starterport)
   starterrating = rebalance.isrebalancegood(starterport)
   print "starter balance rating (i.e. how close to the desired balance):", starterrating
   print

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

   # get list of ASXcodes in order of share price, highest to lowest, with TOTALS removed.
   asxcodestochoose = starterport.keys()
   asxcodestochoose.remove(rebalance.TOTALS)
   asxcodestochoosesorted = []
   for asxcode in asxcodestochoose:
      asxcodestochoosesorted.append([starterport[asxcode][3],asxcode])

   asxcodestochoosesorted.sort(reverse=True)


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
      asxcodestobuy = copy.copy(asxcodestochoosesorted)
      # we have the sorted list of ASX codes, so randomly remove some from the list until we
      # only have numpurchases left
      while len(asxcodestobuy) > numpurchases:
          asxcodestobuy.remove(random.choice(asxcodestobuy))

      # print "for numpurchases",numpurchases,"have  asxcodestobuy", asxcodestobuy
          
      codestobuy = asxcodestochoosesorted
      for purchase in xrange(numpurchases):
         # since the intervals chosen are random anyway, we dont need to randomly choose an ASX code?
         # so we can do it in order of largest to smallest shareprice
	 buycode.append(asxcodestobuy[purchase][1])
         # lets grab the asx code in order of lowest to highest share price, deleting 
         # lets round the amount down to a multiple of share price, and add the remainder to the next purchase..
         # proivided we got a share price (which we may have not if it is not a share already in the portfolio)
         if starterport[buycode[purchase]][3] > 0.0:
            remainder = buyamounts[purchase] % starterport[buycode[purchase]][3]
            # print remainder,purchase,numpurchases,buyamounts
            if purchase < numpurchases -1:
               buyamounts[purchase] = buyamounts[purchase] - remainder
               buyamounts[purchase + 1] = buyamounts[purchase + 1] + remainder
         
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
         if singlethread:
            print "   starting worker with numtries",workertries,"numpurchases",numpurchases
            calcpurchases(statusbar,workertries,numpurchases,result_queue)
         else:
            # print "   starting worker with numtries",workertries,"numpurchases",numpurchases
            a_proc = multiprocessing.Process(target=calcpurchases,args=(statusbar,workertries,numpurchases,result_queue))
            statusbar = False
            proc_list.append(a_proc)
            a_proc.start()

   # wait for workers to finish and gather the results.
   if singlethread:
      while not result_queue.empty():
         tempbuychoices = result_queue.get()
         buychoices.update(tempbuychoices)
   else:
      for p in proc_list:
         tempbuychoices = result_queue.get()
         buychoices.update(tempbuychoices)
         p.join()

   # now rate the results and just show the best of each buy count.
   # if a larger number of trades rates worse, we dont show it.
      
   sortratings = buychoices.keys()
   sortratings.sort()
   maxlen = len(asxcodestochoose) * 2 + 1
   prevlen = maxlen
   print
   print
   for rating in sortratings:
      if maxlen >= len(buychoices[rating]):
	 maxlen = len(buychoices[rating])
	 if maxlen != prevlen:
            print "the best rating discovered for ",maxlen/2," share trades"
	    # have found the best rated of the next number of fees.
	    prevlen = maxlen
	    print "buy the following combos"
	    portresult = [starterport]
	    for buyamount,buycode in zip(buychoices[rating][::2],buychoices[rating][1::2]):
               if portresult[-1][buycode][3] > 0.0:
	          print "%4s qty: %12.2f $amount: %12.2f" % (buycode,buyamount/portresult[-1][buycode][3],buyamount)
               else:
                  print "%4s qty: %12s $amount: %12.2f" % (buycode,"share price unknown",buyamount)
	       portresult.append(rebalance.rebalance(buyamount,portresult[-1],buycode))
            print 
	    rebalance.printport(portresult[-1])
	    print "rating: ",rebalance.isrebalancegood(portresult[-1])
	    print "broker fees: % ", len(buychoices[rating])/2 * fee / addedcash * 100
            print
            print
            

