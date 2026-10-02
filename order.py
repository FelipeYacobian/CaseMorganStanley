class Order:
    def __init__(self, order_type, side, qty, price=None):

        self.order_type = order_type
        self.side = side
        self.qty = qty
        self.price = price
