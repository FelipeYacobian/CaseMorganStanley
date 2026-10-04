from matching_engine import MatchingEngine


def aggregate(trades):
    # soma as quantidades de trades com o mesmo preço
    totals = {}
    for price, qty in trades:
        totals[price] = totals.get(price, 0) + qty
    return totals


def print_trades(trades):
    for price, qty in aggregate(trades).items():
        print(f"Trade, price: {price:g}, qty: {qty}")


def check(side, qty, price=1):
    if side not in ("buy", "sell") or qty <= 0 or price <= 0:
        raise ValueError


def handle(engine, line):
    try:
        p = line.lower().split()

        if p[0] == "limit":
            side, price, qty = p[1], float(p[2]), int(p[3])
            check(side, qty, price)
            order_id, trades = engine.limit_order(side, price, qty)
            print(f"Order created: {side} {qty} @ {price:g} {order_id}")
            print_trades(trades)

        elif p[0] == "market":
            side, qty = p[1], int(p[2])
            check(side, qty)
            print_trades(engine.market_order(side, qty))

        elif p[0] == "peg":
            peg_type, side, qty = p[1], p[2], int(p[3])
            check(side, qty)
            order_id = engine.peg_order(peg_type, side, qty)
            if order_id is None:
                raise ValueError
            print(f"Order created: peg {peg_type} {side} {qty} {order_id}")

        elif p[0] == "cancel":
            print("Order cancelled" if engine.cancel_order(p[2]) else "Order not found")

        elif p[0] == "modify":
            price, qty = float(p[3]), int(p[4])
            check("buy", qty, price)
            trades = engine.modify_order(p[2], price, qty)
            if trades is None:
                print("Order not found")
            else:
                print("Order modified")
                print_trades(trades)

        elif p[0] == "print":
            engine.print_book()

        else:
            raise ValueError

    except (ValueError, IndexError):
        print("Comando inválido")


def main():
    engine = MatchingEngine()
    while True:
        line = input(">>> ").strip()
        if line == "exit":
            break
        if line:
            handle(engine, line)


if __name__ == "__main__":
    main()