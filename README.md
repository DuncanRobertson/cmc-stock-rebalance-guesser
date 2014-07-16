cmc-stock-rebalance-guesser
===========================

Simple script for rebalancing a CMC Markets Australia stock portfolio managed with a passive buy and hold strategy.
Uses crude "Monte Carlo" style iterated random selections as a calculation method.

Generates buy approximate buy suggestions to keep a share portfolio to a certain percentage weighting.
This script is only aware of dollar amounts, not price per share, and is just for suggesting random share purchases that will tend towards a desired goal.

VERY LITTLE ERROR CHECKING IS DONE!

First tries the entire amount as a single buy.
Then does a number of iterations broken into two random buys.
Then does a number of iterations broken into three random buys.

Takes as input the CSV file saved from the CMC Markets "Profit and Loss" statement, as a source of the current state of the portfolio.

This script in no way should be construed as any kind of investment advice and is used entirely at your own risk, it was written for purely personal amusement - in fact I'll freely proclaim this as nearly useless.I have made it available in case someone else may find it's workings amusing as well.

example usage:

rebalance-monte.py rebalance.ini PnL-example.CSV 7000 10000

will try and allocate 7000 dollars worth of shares with 10000 random buy combinations

Also there is a "manual" version that allows calculating of the final portfolio weighting after a sequence of buys.

example usage:

python rebalance-manual.py  rebalance.ini PnL-example.CSV  HHV 10000 AAA 20000

will show the percentage weightings of the starter portfolio, then the weightings after 10000 of HHV and 20000 of AAA are added, also showing the "rating" (how close we measure the portfolio to the ideal weighting) and the fees.



