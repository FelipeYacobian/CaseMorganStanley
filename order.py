class Order:
    def __init__(self, orderType, side, qty, price=None):

        self.type = orderType
        self.side = side
        self.qty = qty
        self.price = price
