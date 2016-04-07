#!/usr/bin/env python

import csv, sys, pprint, random, rebalance, copy

import multiprocessing

def usage():
   print "%s <config.ini> <profitloss.csv> [profitloss2.csv ...]  cashtospenddollars iterationcount  .." % sys.argv[0]
   print "can accept one or more profitloss.csv files on command line"
   sys.exit(1)

inputcsvfiles = []

if __name__ == '__main__':
   try:
      fee, desiredport, singleproc = rebalance.readconfig(sys.argv[1])
      argcount = 2
      while sys.argv[argcount].lower()[-4:] == '.csv':
         inputcsvfiles.append(sys.argv[argcount])
         argcount = argcount + 1
      # print "argcount when leaving loop was ",argcount
      addedcash = float(sys.argv[argcount])
      numtries = int(sys.argv[argcount + 1])
   except:
      usage()
   starterports = []
   firstcsv = True
   for csvfile in inputcsvfiles:
      starterports.append(rebalance.read_cmc_pnl_to_portfdict(csvfile,desiredport))
      if not firstcsv:
         starterports.append(rebalance.add_portfdict(starterports[-2],starterports[-1]))
      else:
         firstcsv = False

   starterport = starterports[-1]

   buychoices = {}

   print "starter portfolio, loaded from the files ",inputcsvfiles
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

def calcpurchases(numtries,numpurchases):
   buychoices = {}

   # print ".. trying options for ",numpurchases," number of purchases...tries",numtries
   # now running multiprocessor, only put out a status bar for the first job.
   for i in xrange(numtries):
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

   return({ sortratings[0] : buychoices[sortratings[0]] })

#cribbed a bit from http://natpoor.blogspot.com/2014/07/python-multiprocessing-and-queues.html
# then improved with using a pool so the processes are balanced better.
if __name__ == '__main__':
   poolresults = []

   print "CPU count is ", multiprocessing.cpu_count()
   pool =  multiprocessing.Pool(processes=multiprocessing.cpu_count())
   for numpurchases in xrange(2,len(asxcodestochoose) + 1):
      workertries = numtries/numpurchases/2
      for i in xrange(numpurchases * 2):
         if singleproc:
            print "iteration:",numpurchases - 2," of ",len(asxcodestochoose) - 2,i + 1," of ",numpurchases * 2," tries:",workertries
            buychoices.update(calcpurchases(workertries,numpurchases))
         else:
            poolresults.append(pool.apply_async(calcpurchases,args=(workertries,numpurchases)))

   # if not in single processor mode gather the results as the pool of workers finish.
   if not singleproc:
      i = 0.0
      for p in poolresults:
         i = i + 1
         buychoices.update(p.get())
         # print "have result ",i," of ",len(poolresults)
         rebalance.update_progress(i/len(poolresults))

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
            
