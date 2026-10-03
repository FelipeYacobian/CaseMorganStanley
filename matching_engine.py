from collections import deque
from order import Order

class MatchingEngine:
    def __init__(self):
        self.bids = {}
        self.offers = {}
        self.next_id = 1

    def limit_order(self, side, price, qty, order_id=None):

        if order_id is None:
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

        self.update_pegs()
        return order_id, trades    

    def market_order(self, side, qty):
        order = Order("market", side.lower(), qty)
        trades = self.match(order)
        self.update_pegs()
        return trades

    def cancel_order(self, order_id):
        if self.remove(self.bids, order_id):
            self.update_pegs()
            return True
        if self.remove(self.offers, order_id):
            self.update_pegs()
            return True
        return False

    def modify_order(self, order_id, new_price, new_qty):
        order = self.remove(self.bids, order_id) or self.remove(self.offers, order_id)
        if order is None:
            return None

        _, trades = self.limit_order(order.side, new_price, new_qty, order_id)
        return trades

    def remove(self, side_book, order_id):
        for price in list(side_book):
            queue = side_book[price]
            for order in queue:
                if order.id == order_id:
                    queue.remove(order)
                    if not queue:
                        del side_book[price]
                    return order      
        return None                   

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

    def peg_order(self, peg_type, side, qty):
        side = side.lower()
        if (peg_type, side) not in (("bid", "buy"), ("offer", "sell")):
            return None

        book = self.bids if side == "buy" else self.offers
        prices = [p for p, q in book.items()
                  if any(o.order_type == "limit" for o in q)]
        if not prices:
            return None

        price = max(prices) if side == "buy" else min(prices)
        order_id = f"identificador_{self.next_id}"
        self.next_id += 1
        book[price].append(Order("peg", side, qty, order_id, price))
        return order_id

    def update_pegs(self):
        for book, side in ((self.bids, "buy"), (self.offers, "sell")):
            prices = [p for p, q in book.items()
                      if any(o.order_type == "limit" for o in q)]
            if not prices:
                continue
            target = max(prices) if side == "buy" else min(prices)

            moving = []
            for price in list(book):
                if price != target:
                    for order in list(book[price]):
                        if order.order_type == "peg":
                            book[price].remove(order)
                            moving.append(order)
                    if not book[price]:
                        del book[price]

            for order in reversed(moving):
                order.price = target
                book[target].appendleft(order)