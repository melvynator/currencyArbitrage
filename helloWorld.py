from urlparse import urlunparse
from sets import Set
from random import randint
import random
import web
import json
import urllib2
import sys
import copy
import math
import time

urls = (
  '/', 'Index',
  '/data', 'Data'
)

app = web.application(urls, globals())

static = web.template.render('static/')
template = web.template.render('templates/')


def safe_list_get (l, idx, default):
    try:
        return l[idx]
    except IndexError:
        return default

def bellmanFord(currency,nb_currencies):
    tab=matrix = [[0]*nb_currencies for i in range(nb_currencies)]
    listOfRate = ["USD","JPY", "BTC", "EUR"]
    for i in range(0,nb_currencies):
        for j in range(0,nb_currencies):
          tab[i][j]=currency.getRateFromTo(listOfRate[i],listOfRate[j]).value

    for i in range(0,nb_currencies):
        for j in range(0,nb_currencies):
            tab[i][j]= -math.log(tab[i][j])

    dis = []
    pre = []

    for i in range(0,nb_currencies):
        dis.append(float("infinity"))
        pre.append(-1)

    dis[0]=0

    for k in range(0,nb_currencies):
        for i in range(0,nb_currencies):
            for j in range(0,nb_currencies):
                if(j != i):
                    if(dis[i]+tab[i][j] < dis[j]):
                        dis[j]=dis[i]+tab[i][j]
                        pre[j]=i

    findCycle = False
    cycle = []
    for i in range(0,nb_currencies):
        for j in range(0,nb_currencies):
            if(dis[i]+tab[i][j]<dis[j]):
                findCycle = True
                start = pre[i]

    if(findCycle):
        z = start
        cycle.append(listOfRate[z])
        count = 0
        while (pre[z] != start):
            count = count + 1
            z = pre[z]
            cycle.append(listOfRate[z])
            if (count > nb_currencies + 1):
                print("Error need to check that")
                for i in range(0,nb_currencies):
                    print(pre[i])
                break
        cycle.append(listOfRate[pre[z]])


    return cycle

def acceptance_probability(old_cost,new_cost,T):
    return math.exp((new_cost - old_cost)/T)

def anneal(currencies,nb_currencies):
    popInit = Individual(currencies)
    rateInit = popInit.getToTalValue(currencies)
    T = 1.0
    T_min = 0.00001
    alpha = 0.9
    population = copy.deepcopy(popInit)
    population.changeNeighbor(currencies,nb_currencies)
    while T > T_min :
        i = 1
        while i <= 100:
            population.changeNeighbor(currencies,nb_currencies)
            costNeighbor = population.getToTalValue(currencies)
            ap = acceptance_probability(rateInit,costNeighbor,T)
            if ap > random.random():
                popInit = copy.deepcopy(population)
                rateInit = popInit.getToTalValue(currencies)
            i += 1
        T = T * alpha
    return popInit

class Rate(object):
    value = 0.0
    fromCurrency = ""
    toCurrency = ""

    def __init__(self, value = 0.0, fromCurrency = "", toCurrency = ""):
        self.value = value
        self.fromCurrency = fromCurrency
        self.toCurrency = toCurrency

    def __str__(self):
        return str(self.value)

class Individual(object):

    way = []
    totalValue = 1

    def getToTalValue(self, currency):
        totalValue = 1
        newWay = self.way
        newWay = [elem for elem in self.way if elem != "NONE"]
        waySize = len(newWay)
        for i in range (1, waySize):
            totalValue = currency.getRateFromTo(safe_list_get(newWay, i - 1, "lol"), safe_list_get(newWay, i, "lol")).value * totalValue
        return totalValue

    def __init__(self, currency):
        way = []
        listOfRate = ["JPY", "BTC", "EUR"]
        way.append("USD")
        for i in range (1,4):
            way.append(random.choice(listOfRate))
        way.append("USD")
        self.way = way
        self.cleanWay()
        self.totalValue = self.getToTalValue(currency)

    def changeNeighbor(self,currencies,nb_currencies):
        listOfRate = ["JPY", "BTC", "EUR","NONE"]
        self.way[randint(1,nb_currencies - 1)]=listOfRate[randint(0,3)]
        self.cleanWay()
        self.totalValue = self.getToTalValue(currencies)


    def cleanWay(self):
        for i in range (0, len(self.way) - 1):
            for j in range (0, i):
                if safe_list_get(self.way, i, "lol") == safe_list_get(self.way, j, "lol"):
                    self.way[i] = "NONE"

    def __str__(self):
        wayToDisplay = []
        for i in range (len(self.way)):
            wayToDisplay.append(safe_list_get(self.way, i, "lol"))
        return str(wayToDisplay ) + " " + str(self.totalValue)

    def setWay(self, way):
        self.way = way

    def setTotalValue(self,currency):
        totalValue = 1
        wayWithoutNone = [elem for elem in self.way if elem != "NONE"]
        for i in range (0, len(wayWithoutNone)-1):
            totalValue = totalValue * currency.getRateFromTo(wayWithoutNone[i],wayWithoutNone[i+1]).value
        self.totalValue = totalValue

class Population():
    individuals = []

    def getBest5Indivuals(self):
        sortedIndividuals = sorted(self.individuals)
        best = []
        for i in range (4, 10):
            best.append(safe_list_get(sortedIndividuals, i, "lol"))
        return best

    def crossOver(self, listOfIndividuals, currencies):
        crossedIndividuals = []
        for i in range(0,2):
            individual1 = copy.deepcopy(safe_list_get(listOfIndividuals, randint(0,5), "lol"))
            individual2 = copy.deepcopy(safe_list_get(listOfIndividuals, randint(0,5), "lol"))
            crossPosition = 2
            DNAson1 = []
            DNAson2 = []
            for i in range(0, crossPosition):
                DNAson1.append(safe_list_get(individual1.way, i, "lol"))
                DNAson2.append(safe_list_get(individual2.way, i, "lol"))
            DNAson1.append(currencies.getRateFromTo(safe_list_get(individual1.way, crossPosition - 1, "lol").toCurrency, safe_list_get(individual2.way, crossPosition + 1, "lol").fromCurrency))
            DNAson2.append(currencies.getRateFromTo(safe_list_get(individual2.way, crossPosition - 1, "lol").toCurrency, safe_list_get(individual1.way, crossPosition + 1, "lol").fromCurrency))
            for i in range(crossPosition + 1, 3):
                DNAson1.append(safe_list_get(individual2.way, i, "lol"))
                DNAson2.append(safe_list_get(individual1.way, i, "lol"))
            individual1.setWay(DNAson1)
            individual2.setWay(DNAson2)
            individual1.setTotatlValue()
            individual2.setTotatlValue()
            crossedIndividuals.append(individual1)
            crossedIndividuals.append(individual2)
        return crossedIndividuals

    def mutation(self):
        print("mutation")

    def __init__(self, setOfIndividuals):
        self.individuals = setOfIndividuals

    def __str__(self):
        valueToDisplay = ""
        for i in range(0,10):
            valueToDisplay = valueToDisplay + str(safe_list_get(self.individuals, i, "lol"))
            valueToDisplay = valueToDisplay + "\n"
        return valueToDisplay

class Currencies(object):

    def __init__ (self):
        try:
            rates = urllib2.urlopen("http://fx.priceonomics.com/v1/rates/")
        except urllib2.URLError as e:
            return e.reasonx
        res = json.load(rates)
        self.EURToEUR = Rate(1.000000, "EUR", "EUR")
        self.USDToUSD = Rate(1.000000, "USD", "USD")
        self.JPYToJPY = Rate(1.000000, "JPY", "JPY")
        self.BTCToBTC = Rate(1.000000, "BTC", "BTC")
        self.EURToUSD = Rate(float(res['EUR_USD']), "EUR", "USD")
        self.EURToJPY = Rate(float(res['EUR_JPY']), "EUR", "JPY")
        self.EURToBTC = Rate(float(res['EUR_BTC']), "EUR", "BTC")
        self.USDToEUR = Rate(float(res['USD_EUR']), "USD", "EUR")
        self.USDToBTC = Rate(float(res['USD_BTC']), "USD", "BTC")
        self.USDToJPY = Rate(float(res['USD_JPY']), "USD", "JPY")
        self.BTCToEUR = Rate(float(res['BTC_EUR']), "BTC", "EUR")
        self.BTCToJPY = Rate(float(res['BTC_JPY']), "BTC", "JPY")
        self.BTCToUSD = Rate(float(res['BTC_USD']), "BTC", "USD")
        self.JPYToEUR = Rate(float(res['JPY_EUR']), "JPY", "EUR")
        self.JPYToUSD = Rate(float(res['JPY_USD']), "JPY", "USD")
        self.JPYToBTC = Rate(float(res['JPY_BTC']), "JPY", "BTC")

    def getRandomRateFromACurrency(self, currency):
        return random.choice([v for attr, v in vars(self).items()if len(attr) == 8 and attr[0:3] == currency])

    def getRandomRateToUSD(self, currency):
        if(currency == "JPY"):
            return self.JPYToUSD
        if(currency == "BTC"):
            return self.BTCToUSD
        if(currency == "EUR"):
            return self.EURToUSD

    def getRateFromTo(self, fromCurrency, toCurrency):
        return getattr(self, fromCurrency + "To" + toCurrency)

    def getRandomRate(self):
        return random.choice([v for attr, v in vars(self).items()if len(attr) == 8 and attr[3:5] == 'To'])

class Index(object):
    def GET(self):
        currencies = Currencies()
        t0_anneal = time.time()
        res = anneal(currencies,4)
        t_final_anneal = time.time() - t0_anneal
        t0_bellman = time.time()
        cycle = bellmanFord(currencies,4)
        t_final_bellman = time.time() - t0_bellman
        testBellmanFord = Individual(currencies)
        testBellmanFord.setWay(cycle)
        testBellmanFord.setTotalValue(currencies)
        print("BellmanFord : ")
        print(testBellmanFord)
        print(t_final_bellman)
        print("Anneal")
        print(res)
        print(t_final_anneal)
        return static.index(res = currencies, random = individual,negativeWay = testBellmanFord,time = time.time() - t0,bftime = t_final_bellman)


if __name__ == "__main__":
    app.run()
