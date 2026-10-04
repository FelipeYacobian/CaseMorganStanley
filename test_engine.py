from matching_engine import MatchingEngine
from main import aggregate, handle


# helpers pra ver o livro na ordem em que as ordens seriam executadas
def bids(engine):
    return [(o.qty, p, o.id)
            for p in sorted(engine.bids, reverse=True)
            for o in engine.bids[p]]


def offers(engine):
    return [(o.qty, p, o.id)
            for p in sorted(engine.offers)
            for o in engine.offers[p]]


# roda um comando como no terminal e pega o que foi printado
def run(engine, capsys, command):
    handle(engine, command)
    return capsys.readouterr().out.strip()


# --- limit e market ---

def test_exemplo_do_enunciado_saida_exata(capsys):
    engine = MatchingEngine()
    run(engine, capsys, "limit buy 10 100")
    run(engine, capsys, "limit sell 20 100")
    run(engine, capsys, "limit sell 20 200")

    assert run(engine, capsys, "market buy 150") == "Trade, price: 20, qty: 150"
    assert run(engine, capsys, "market buy 200") == "Trade, price: 20, qty: 150"
    assert run(engine, capsys, "market sell 200") == "Trade, price: 10, qty: 100"


def test_limit_que_nao_cruza_fica_no_livro():
    engine = MatchingEngine()
    engine.limit_order("sell", 20, 100)
    order_id, trades = engine.limit_order("buy", 10, 100)

    assert trades == []
    assert bids(engine) == [(100, 10, order_id)]


def test_limit_que_cruza_executa_ao_preco_do_livro_e_guarda_o_resto():
    engine = MatchingEngine()
    engine.limit_order("sell", 20, 100)
    order_id, trades = engine.limit_order("buy", 25, 150)

    assert trades == [(20, 100)]
    assert bids(engine) == [(50, 25, order_id)]
    assert offers(engine) == []


def test_limit_executada_inteira_nao_fica_no_livro():
    engine = MatchingEngine()
    engine.limit_order("sell", 20, 100)
    engine.limit_order("buy", 20, 100)

    assert bids(engine) == []
    assert offers(engine) == []


def test_limit_nao_passa_do_seu_preco():
    engine = MatchingEngine()
    engine.limit_order("sell", 20, 100)
    engine.limit_order("sell", 22, 100)
    order_id, trades = engine.limit_order("buy", 21, 150)

    assert trades == [(20, 100)]
    assert bids(engine) == [(50, 21, order_id)]


def test_venda_limit_que_cruza_usa_o_preco_do_comprador():
    engine = MatchingEngine()
    engine.limit_order("buy", 10, 100)
    _, trades = engine.limit_order("sell", 9, 100)

    assert trades == [(10, 100)]


def test_market_sem_liquidez_nao_quebra():
    engine = MatchingEngine()
    assert engine.market_order("buy", 100) == []
    assert engine.market_order("sell", 100) == []


def test_market_parcial_descarta_o_resto():
    engine = MatchingEngine()
    engine.limit_order("sell", 20, 60)

    assert engine.market_order("buy", 100) == [(20, 60)]
    assert offers(engine) == []
    assert bids(engine) == []


def test_trades_de_mesmo_preco_sao_somados():
    assert aggregate([(20, 100), (20, 50)]) == {20: 150}
    assert aggregate([(20, 100), (21, 50)]) == {20: 100, 21: 50}


# --- print book ---

def test_print_book_ordenado_por_prioridade(capsys):
    engine = MatchingEngine()
    engine.limit_order("buy", 9.99, 100)
    engine.limit_order("buy", 10, 200)
    engine.limit_order("sell", 11, 50)
    engine.limit_order("sell", 10.5, 100)

    output = run(engine, capsys, "print book")

    assert output.index("200 @ 10 ") < output.index("100 @ 9.99")
    assert output.index("100 @ 10.5") < output.index("50 @ 11")


# --- prioridade (preço e depois chegada) ---

def test_mesmo_preco_respeita_ordem_de_chegada():
    engine = MatchingEngine()
    engine.limit_order("sell", 20, 100)
    second, _ = engine.limit_order("sell", 20, 200)

    engine.market_order("buy", 150)

    assert offers(engine) == [(150, 20, second)]


def test_melhor_preco_executa_antes_da_ordem_mais_antiga():
    engine = MatchingEngine()
    engine.limit_order("sell", 21, 100)
    engine.limit_order("sell", 20, 100)

    assert engine.market_order("buy", 150) == [(20, 100), (21, 50)]


# --- cancelamento ---

def test_cancelamento_saida_do_enunciado(capsys):
    engine = MatchingEngine()
    created = run(engine, capsys, "limit buy 10 100")

    assert created == "Order created: buy 100 @ 10 identificador_1"
    assert run(engine, capsys, "cancel order identificador_1") == "Order cancelled"
    assert engine.bids == {}


def test_cancelamento_mantem_o_resto_da_fila():
    engine = MatchingEngine()
    first, _ = engine.limit_order("buy", 10, 100)
    second, _ = engine.limit_order("buy", 10, 50)

    assert engine.cancel_order(first) is True
    assert bids(engine) == [(50, 10, second)]


def test_cancelar_id_inexistente_ou_ja_cancelado(capsys):
    engine = MatchingEngine()
    order_id, _ = engine.limit_order("buy", 10, 100)
    engine.cancel_order(order_id)

    assert engine.cancel_order(order_id) is False
    assert run(engine, capsys, "cancel order identificador_99") == "Order not found"


# --- alteração ---

def test_alteracao_exemplo_do_enunciado():
    engine = MatchingEngine()
    first, _ = engine.limit_order("buy", 10, 200)
    second, _ = engine.limit_order("buy", 9.99, 100)
    engine.limit_order("sell", 10.5, 100)

    engine.modify_order(first, 9.98, 200)

    assert bids(engine) == [(100, 9.99, second), (200, 9.98, first)]


def test_alteracao_perde_prioridade_no_mesmo_preco():
    engine = MatchingEngine()
    first, _ = engine.limit_order("buy", 10, 200)
    second, _ = engine.limit_order("buy", 9.99, 100)

    engine.modify_order(first, 9.99, 200)

    assert bids(engine) == [(100, 9.99, second), (200, 9.99, first)]


def test_alteracao_so_de_quantidade():
    engine = MatchingEngine()
    first, _ = engine.limit_order("buy", 10, 200)
    second, _ = engine.limit_order("buy", 10, 100)

    engine.modify_order(first, 10, 50)

    assert bids(engine) == [(100, 10, second), (50, 10, first)]


def test_alteracao_que_cruza_executa():
    engine = MatchingEngine()
    order_id, _ = engine.limit_order("buy", 10, 100)
    engine.limit_order("sell", 10.5, 100)

    assert engine.modify_order(order_id, 11, 100) == [(10.5, 100)]
    assert bids(engine) == []


def test_alterar_id_inexistente():
    engine = MatchingEngine()
    assert engine.modify_order("identificador_99", 10, 100) is None


# --- pegged ---

def test_peg_exemplo_do_enunciado():
    engine = MatchingEngine()
    a, _ = engine.limit_order("buy", 10, 200)
    b, _ = engine.limit_order("buy", 9.99, 100)
    engine.limit_order("sell", 10.5, 100)

    peg = engine.peg_order("bid", "buy", 150)
    assert bids(engine) == [(200, 10, a), (150, 10, peg), (100, 9.99, b)]

    c, _ = engine.limit_order("buy", 10.1, 300)
    assert bids(engine) == [(150, 10.1, peg), (300, 10.1, c),
                            (200, 10, a), (100, 9.99, b)]


def test_peg_desce_quando_o_bid_cai():
    engine = MatchingEngine()
    engine.limit_order("buy", 10, 200)
    peg = engine.peg_order("bid", "buy", 150)
    top, _ = engine.limit_order("buy", 10.1, 300)

    engine.cancel_order(top)

    assert engine.bids[10][0].id == peg
    assert 10.1 not in engine.bids


def test_peg_offer_acompanha_o_offer():
    engine = MatchingEngine()
    engine.limit_order("sell", 10.5, 100)
    peg = engine.peg_order("offer", "sell", 150)
    engine.limit_order("sell", 10.4, 300)

    assert offers(engine)[0] == (150, 10.4, peg)


def test_peg_sem_preco_de_referencia():
    engine = MatchingEngine()
    assert engine.peg_order("bid", "buy", 100) is None


def test_peg_combinacao_invalida():
    engine = MatchingEngine()
    engine.limit_order("buy", 10, 100)
    assert engine.peg_order("bid", "sell", 100) is None
    assert engine.peg_order("offer", "buy", 100) is None


def test_peg_e_executada_por_market():
    engine = MatchingEngine()
    engine.limit_order("buy", 10, 100)
    engine.peg_order("bid", "buy", 50)

    assert engine.market_order("sell", 150) == [(10, 100), (10, 50)]
    assert engine.bids == {}


def test_peg_pode_ser_cancelada():
    engine = MatchingEngine()
    engine.limit_order("buy", 10, 100)
    peg = engine.peg_order("bid", "buy", 50)

    assert engine.cancel_order(peg) is True
    assert all(o.id != peg for q in engine.bids.values() for o in q)


# --- entradas inválidas ---

def test_comandos_invalidos_nao_quebram(capsys):
    engine = MatchingEngine()
    for command in ["limit buy dez 100", "limit compra 10 100", "limit buy 10 -5",
                    "market", "peg bid sell 10", "foo"]:
        assert run(engine, capsys, command) == "Comando inválido"


def test_comandos_aceitam_maiusculas(capsys):
    engine = MatchingEngine()
    assert run(engine, capsys, "LIMIT BUY 10 100").startswith("Order created")