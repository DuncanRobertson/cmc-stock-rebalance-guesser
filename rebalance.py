
#
# rebalance common function module.. almost ready to be refactored into OO if we add more features here.
#

import csv, sys, pprint, random, ConfigParser


TOTALS = 'TOTALS'

def read_cmc_pnl_to_portfdict(filename,desiredport):
   currentport = {}

   pnlcsv = csv.reader(open(filename))

   # read in currenportfolio from "profit and loss" CSV generated by https://www.cmcmarketsstockbroking.com.au/
   for row in pnlcsv:
      print row
      if row[5] != 'Market Value $':
	 currentport[row[0]] = float(row[5])

   # calculate percentages from the total provided in the CSV file.
   for asxcode in currentport.keys():
      if isinstance(currentport[TOTALS],tuple):
	 currentport[asxcode] = currentport[asxcode],currentport[asxcode]/currentport[TOTALS][0] * 100
      else:
	 currentport[asxcode] = currentport[asxcode],currentport[asxcode]/currentport[TOTALS] * 100

   # crossindex with the desired percentages so we have a dict keyed on ASX code (with one element TOTALS" that stores the total
   # containing tuple: desired percentage,current value dollars,current percentage dollars, with shares we dont have yet set to zero.
   for asxcode in desiredport.keys():
      if currentport.has_key(asxcode):
	 desiredport[asxcode] = desiredport[asxcode],currentport[asxcode][0],currentport[asxcode][1]
      else:
	 desiredport[asxcode] = desiredport[asxcode],0.0,0.0

   readport = desiredport.copy()
   return readport

# http://stackoverflow.com/questions/3589214/generate-multiple-random-numbers-to-equal-a-value-in-python
# for getting 3 or... random numbers that add to our amount
def constrained_sum_sample_pos(n, total):
    """Return a randomly chosen list of n positive integers summing to total.
    Each such list is equally likely to occur."""

    dividers = sorted(random.sample(xrange(1, total), n - 1))
    return [a - b for a, b in zip(dividers + [total], [0] + dividers)]

# function that determines the "goodness" of a rebalance.. currently just the
# average of the percentage differences between desired % balance and current balance.
def isrebalancegood(newport):
   percdifftotal = 0
   asxcodes = newport.keys()
   asxcodes.remove(TOTALS)

   # containing tuple: desired percentage,current value dollars,current percentage dollars
   for asxcode in asxcodes:
      pdiff = abs(newport[asxcode][0] - newport[asxcode][2])
      # print asxcode,pdiff
      percdifftotal = percdifftotal + pdiff
   # print percdifftotal / len(asxcodes)
   return percdifftotal / len(asxcodes)

# does a rebalance, "purchases" amount dollars of codetobuy and
# returns a copied dicionary with the recalculated portfolio.

def rebalance(amount,portpassed,codetobuy):

   portf = portpassed.copy()
   # get the new totals first as we dont know what order we
   # will process the elements
   newtotal =  portf[TOTALS][1] + amount

   for asxcode in portf.keys():
      if asxcode == codetobuy:
         portf[asxcode] = portf[asxcode][0], \
                          portf[asxcode][1] + amount, \
                          (portf[asxcode][1] + amount) / newtotal * 100

      if not asxcode == codetobuy and not asxcode == TOTALS:
         portf[asxcode] = portf[asxcode][0], \
         portf[asxcode][1], \
         (portf[asxcode][1] / newtotal * 100)
            
      if asxcode == TOTALS:
         portf[asxcode] = portf[asxcode][0],newtotal,portf[asxcode][2]
   return portf

# slightly less ugly display method than pprint.pprint
def printport(portf):
   asxcodes = portf.keys()
   asxcodes.sort()
   print "%8s%12s%12s%12s" % ('ASXcode','%wanted','$total','%current')
   for asxcode in asxcodes:
      print "%8s%12.2f%12.2f%12.2f" % ((asxcode,) + portf[asxcode])

# read in the fees and desired portfolio weighting from an ini file
def readconfig(configfile):

   settings = ConfigParser.ConfigParser()
   settings.read(configfile)
   sections = settings.sections()
   if 'settings' not in sections:
      print "config file needs [settings] section"
      sys.exit(1)

   if settings.has_option('settings','fee'):
      fee = settings.getfloat('settings','fee')
   else:
      fee = 0.0

   if 'desiredbalance' not in sections:
      print "config file needs [desiredbalance] section"
      sys.exit(1)

   desiredport = {}
   total = 0.0
   for confread in settings.items('desiredbalance'):
      desiredport[confread[0].upper()] = float(confread[1])
      total = desiredport[confread[0].upper()] + total
      
   desiredport[TOTALS] = total
   if not total == 100.0:
      print "WARNING: total percentage of desired mix read from config does not add up to 100%"
   return fee,desiredport

