class Order:
    def __init__(self, order_type, side, qty, id=None, price=None):

        self.id = id
        self.order_type = order_type
        self.side = side
        self.qty = qty
        self.price = price
