import abc
from scipy.stats import norm
from numpy.random import normal
import streamlit as st

class OptionClass(metaclass=abc.ABCMeta):
    def __init__(self, principal, stockprice, sigma, numTrades=1000):
        self.principal = principal
        self.stockprice = stockprice
        self.sigma = sigma
        self.numTrades = numTrades
        
    
    def simulateTrades(self):
        # Main template function to simulate 1000s of trades
        
        self.kelly = self.calculateKelly()
        self.ev = self.calculateEV()

        changing_principal = self.principal
        trades = normal(self.stockprice, self.sigma, self.numTrades)
        
        for trade in trades:
            trade_outcome = self.makeTrade(trade)
            changing_principal += trade_outcome
        
        self.changed_principal = changing_principal
    

    @abc.abstractmethod
    def makeTrade(self, trade):
        raise NotImplementedError
    

    @abc.abstractmethod
    def calculateKelly(self):
        raise NotImplementedError


    def print_metrics(self):
        print(f'Stock Price : {self.stockprice}')
        print(f'Long Strike Price : {self.longstrike}')
        print(f'Short Strike Price : {self.shortstrike}')
        print(f'Credit (total) : {self.credit}')
        print(f'Probability of Profit : {self.pop}')
        print(f'Expected Value : {self.ev}')
        print(f'Kelly Allocation : {self.kelly}')
        print(f'Actual Allocation : {self.maxloss / self.principal}')


    def calculateEV(self):
        EV = self.p2 * self.credit + self.p1 * 0.5 * self.credit - self.q2 * self.maxloss - self.q1 * 0.5 * self.maxloss
        return EV


class PutSpread(OptionClass):
    def __init__(self, shortstrike, longstrike, credit, lots=1, **kwargs):
        super().__init__(**kwargs)
        # Price, at expiration, at which you neither lose nor make money
        self.breakeven = shortstrike - credit/(100*lots)
        # Probability of Profit
        self.pop = norm.sf(self.breakeven, self.stockprice, self.sigma)
        # Triangular Positive probability
        self.p1 = norm.cdf(shortstrike, self.stockprice, self.sigma) - norm.cdf(self.breakeven, self.stockprice, self.sigma)
        # Rectangular Positive probability
        self.p2 = self.pop - self.p1
        # Triangular Negative probability
        self.q1 = norm.cdf(self.breakeven, self.stockprice, self.sigma)-norm.cdf(longstrike, self.stockprice, self.sigma)
        # Rectangular Negative probability
        self.q2 = norm.cdf(self.breakeven, self.stockprice, self.sigma) - self.q1

        self.shortstrike = shortstrike
        self.longstrike = longstrike
        self.credit = credit
        self.lots = lots

        # Slope
        self.m = self.credit/(self.shortstrike-self.breakeven)
        # Maximum absolute loss on trade (credit is total credit)
        self.maxloss = (self.shortstrike-self.longstrike-self.credit/(100*self.lots))*100*self.lots
        # Kelly odds
        self.odds = (0.5 * self.credit * self.p1 + self.credit *  self.p2)/(0.5 * self.maxloss * self.q1 + self.maxloss * self.q2)


    def calculateKelly(self):
        #kelly criteria allocation
        kelly = (self.pop*(self.odds+1) - 1) / self.odds
        return kelly


    def makeTrade(self, trade):
        # Make Vertical Put Credit Spread Trade, return a credit/debit to add to principal
        allocation = self.maxloss / self.principal
        if trade >= self.shortstrike:
            outcome = self.principal * allocation * self.odds
        elif self.longstrike < trade < self.shortstrike:
            outcome = self.credit - self.m * (self.shortstrike-trade)
        elif trade <= self.longstrike:
            outcome = -self.maxloss
        return outcome


class CallSpread(OptionClass):
    def __init__(self):
        pass


    def makeTrade(self):
        pass

if __name__ == '__main__':
    st.title('Options Put Credit Spread')
    st.write('Default values are provided. Please update each field with the specifics of your trade.')
    st.header('Stock and Account Info')
    price = st.number_input(label='Stock Price', min_value=0., step=0.01, value=98.)
    sigma = st.slider(label='Stock Sigma (std. dev.)', min_value=0.1, max_value=100., value=5., step=0.1)
    principal = st.number_input(label='Liquid Principal: ', min_value=2000)
    st.header('Credit Spread Info')
    short = st.number_input(label='Short Strike Price', min_value=0., step=0.01, value=95.)
    long = st.number_input(label='Long Strike Price', min_value=0., step=0.01, value=93.)
    credit = st.number_input(label='Credit (Total)', min_value=0., step=0.1, value=55.)

    puttrade = PutSpread(principal=principal, stockprice=price, sigma=sigma, numTrades=100000, shortstrike=short, longstrike=long, credit=credit)
    puttrade.simulateTrades()

    allocation = round(puttrade.maxloss / puttrade.principal * 100, 2)
    kelly = round(puttrade.kelly*100, 2)

    if puttrade.pop > 0.5 and kelly > 0 and allocation < kelly and puttrade.changed_principal > puttrade.principal:
        trade_recommendation = 'Enter Trade'
    else:
        trade_recommendation = 'Do not enter trade'

    st.header('Results')
    col1, col2 = st.beta_columns(2)
    with col1:
        st.write('Expected Value: ', round(puttrade.ev, 2))
        st.write('Probability of Profit: ', round(puttrade.pop*100, 3), '%')
        st.write('Max. Loss: $', puttrade.maxloss)
    with col2:
        st.write('Actual Allocation: ', allocation, '%')
        st.write('Kelly Allocation: ', kelly, '%')
        st.markdown(f'Trade Recommendation: **{trade_recommendation}**')