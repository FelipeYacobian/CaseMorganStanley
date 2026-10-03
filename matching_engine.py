from collections import deque
from order import Order

class MatchingEngine:
    def __init__(self):
        self.bids = {}
        self.offers = {}
        self.next_id = 1

    def limit_order(self, side, price, qty):
        order_id = f"identificador_{self.next_id}"   
        self.next_id +=1

        order = Order("limit", side.lower(), qty, order_id, price)

        trades = self.match(order)

        if order.qty > 0:
            if order.side == "buy" :
                book = self.bids

            if order.side == "sell" :
                book = self.offers

            if order.price not in book :
                book[order.price] = deque()
                
            book[order.price].append(order)

        return order_id, trades    

    def market_order(self, side, qty):
        order = Order("market", side.lower(), qty)
        trades = self.match(order)
        return trades

    def match(self, order):
        trades = []

        if order.side == "buy":
            other_side = self.offers
        else :
            other_side = self.bids 

        while order.qty > 0 and other_side :
            if order.side == "buy":
                best_price = min(other_side)
            else :
                best_price = max(other_side)

            if order.order_type == "limit":
                if order.side == "buy" and order.price < best_price :
                    break
                if order.side == "sell" and order.price > best_price :
                    break

            queue = other_side[best_price]
            first_order = queue[0]

            traded = min(order.qty, first_order.qty)
            trades.append((best_price, traded))

            order.qty = order.qty - traded
            first_order.qty = first_order.qty - traded

            if first_order.qty == 0:
                queue.popleft()
            if not queue :
                del other_side[best_price]

        return trades

    def print_book(self):
        print("Ordens de Compra:")
        for price in sorted(self.bids, reverse=True):
            for order in self.bids[price]:
                print(f"  {order.qty} @ {price:g} ({order.id})")

        print("Ordens de Venda:")
        for price in sorted(self.offers):
            for order in self.offers[price]:
                print(f"  {order.qty} @ {price:g} ({order.id})")
