from collections import deque
from order import Order

class MatchingEngine:
    def __init__(self):
        self.bids = {}
        self.offers = {}

    def limit_order(self, side, price, qty):
        order = Order("limit", side.lower(), qty, price)

        if order.side == "buy" :
            book = self.bids

        if order.side == "sell" :
            book = self.offers

        if order.price not in book :
            book[order.price] = deque()
            
        book[order.price].append(order)    

        