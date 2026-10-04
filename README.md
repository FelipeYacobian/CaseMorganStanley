# Matching Engine

Matching engine em memória para um único ativo, com ordens **limit**, **market** e **pegged**, seguindo **prioridade preço-tempo**.

Desenvolvida em Python 3.12, sem dependências externas (exceto `pytest` para os testes).

## Como rodar

```
python3 main.py
```

Comandos aceitos:

| Comando  | Exemplo                                  | O que faz                                                   |
| -------- | ---------------------------------------- | ----------------------------------------------------------- |
| Limit    | `limit buy 10 100`                       | Ordem de compra/venda a um preço fixo (preço, quantidade)   |
| Market   | `market sell 50`                         | Executa imediatamente contra o melhor preço disponível      |
| Pegged   | `peg bid buy 150` / `peg offer sell 150` | Ordem que acompanha o melhor preço do próprio lado          |
| Cancelar | `cancel order identificador_1`           | Remove a ordem do livro                                     |
| Alterar  | `modify order identificador_1 12 80`     | Altera preço e quantidade (id, novo preço, nova quantidade) |
| Livro    | `print book`                             | Mostra o livro de ofertas                                   |
| Sair     | `exit`                                   | Encerra o programa                                          |

Exemplo de sessão:

```
>>> limit buy 10 100
Order created: buy 100 @ 10 identificador_1
>>> limit sell 20 100
Order created: sell 100 @ 20 identificador_2
>>> market buy 50
Trade, price: 20, qty: 50
>>> cancel order identificador_1
Order cancelled
```

## Como rodar os testes

```
pip install pytest          # ou, no Ubuntu: sudo apt install python3-pytest
python3 -m pytest
```

## Testes

Os testes ficam em `test_engine.py` (29 testes, organizados por requisito do enunciado):

| Grupo                 | O que é verificado                                                                                                                                                                       |
| --------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Limit e market        | Exemplo do enunciado com a saída exata; limit que cruza e que não cruza; limit que não passa do seu preço; preço do trade; market sem liquidez e parcial; soma dos trades de mesmo preço |
| Visualização do livro | `print book` ordenado por prioridade nos dois lados                                                                                                                                      |
| Prioridade            | Mesmo preço respeita a ordem de chegada; melhor preço executa antes da ordem mais antiga                                                                                                 |
| Cancelamento          | Saída do enunciado (`Order created` / `Order cancelled`); fila preservada; id inexistente ou já cancelado                                                                                |
| Alteração             | Exemplo do enunciado; perda de prioridade no mesmo preço; alteração só de quantidade; alteração que cruza o livro; id inexistente                                                        |
| Pegged                | Exemplo do enunciado; peg descendo quando o bid cai; peg offer; sem preço de referência; combinação inválida; peg executada por market; peg cancelada                                    |
| Entradas inválidas    | Comandos inválidos não interrompem o programa; maiúsculas são aceitas                                                                                                                    |

A maior parte dos testes chama a engine diretamente. Os que verificam a saída de texto executam o comando como no terminal e capturam o que foi impresso.

## Estrutura

| Arquivo              | Responsabilidade                                                     |
| -------------------- | -------------------------------------------------------------------- |
| `order.py`           | Classe `Order`: tipo, lado, quantidade, preço e id                   |
| `matching_engine.py` | Classe `MatchingEngine`: o livro e todas as regras de negociação     |
| `main.py`            | Lê os comandos do terminal, valida a entrada e imprime os resultados |
| `test_engine.py`     | Testes automatizados com pytest                                      |

A engine aplica as regras e devolve resultados; o `main.py` lê, valida e imprime. Por isso a engine pode ser testada diretamente, sem simular digitação.

## Decisões técnicas

- **Livro:** dois dicionários (`bids` e `offers`) que mapeiam cada preço para uma fila (`deque`) de ordens. A fila deixa explícita a prioridade por ordem de chegada: ordens novas entram com `append` e a execução consome o início com `popleft`, ambos O(1).
- **Melhor preço:** calculado na hora com `max` (compras) e `min` (vendas) sobre os preços do lado, em O(n) no número de preços. Para imprimir o livro, os preços são ordenados com `sorted`.
- **Matching único:** limit e market usam o mesmo método de cruzamento (`match`). A diferença é que a limit para quando o preço do outro lado passa do seu limite e guarda o restante no livro, enquanto a market descarta o restante.
- **Ids:** gerados por um contador (`identificador_1`, `identificador_2`, ...) e nunca reaproveitados.
- **Alteração:** reaproveita a criação de limit orders, passando o id existente; por isso a ordem vai para o fim da fila.
- **Remoção segura:** ao procurar uma ordem, o loop percorre uma cópia das chaves (`list(...)`), o que permite apagar um preço vazio do dicionário durante a busca.
- **Retornos em vez de prints:** os métodos da engine devolvem ids e trades em vez de imprimir, o que permite testá-los diretamente. A impressão fica no `main.py`.

## Decisões de design

**Limit que cruza o livro:** é executada imediatamente contra o lado oposto, respeitando seu limite de preço. A quantidade restante permanece no livro. Esse comportamento evita que o livro permaneça cruzado (compra e venda paradas que concordam no preço) e é consistente com o funcionamento de mercados eletrônicos.

**Limit que não cruza:** permanece no livro, respeitando preço e prioridade temporal.

**Preço do trade:** sempre o preço da ordem que já estava no livro (a ordem _resting_), independentemente de qual lado iniciou o negócio.

**Prioridade:** preço primeiro (maior preço nas compras, menor nas vendas); no mesmo preço, a ordem que chegou antes é executada antes (FIFO).

**Market sem liquidez suficiente:** a market executa o que houver disponível do outro lado e descarta o restante. Se o outro lado tiver menos do que o pedido (por exemplo, `market buy 100` com só 60 à venda), executa 60 e os 40 restantes são descartados. Se o outro lado estiver vazio, nenhum trade acontece e a ordem inteira é descartada, sem erro. Market orders nunca ficam no livro, porque não têm preço. O próprio exemplo do enunciado segue essa regra: o segundo `market buy 200` executa só 150.

**Saída dos trades:** trades de mesmo preço gerados pela mesma ordem são somados numa única linha, como no exemplo do enunciado (`Trade, price: 20, qty: 150` para 100 + 50).

**Cancelamento de id inexistente:** mostra `Order not found`, sem gerar erro.

**Alteração de ordem:** a ordem é removida e recolocada com o mesmo id, no fim da fila do novo preço. Por isso perde a prioridade temporal, inclusive quando só a quantidade muda. Se o novo preço cruzar o livro, ela é executada como uma limit.

**Pegged orders:**

- `peg bid` acompanha o melhor preço de compra (best bid) e só é aceita com `buy`; `peg offer` acompanha o melhor preço de venda (best offer) e só é aceita com `sell`. As combinações cruzadas executariam imediatamente contra o outro lado e são rejeitadas.
- Uma peg nova entra no fim da fila do melhor preço do seu lado.
- Quando o melhor preço muda (para cima ou para baixo), a peg vai para a frente da fila do novo preço. Essa regra reproduz o exemplo do enunciado, em que a peg fica à frente da ordem que criou o novo preço.
- O preço de referência é calculado ignorando as próprias pegs; caso contrário, uma peg seguiria a si mesma.
- Se não houver ordens limit do seu lado, a peg não é criada. Se o lado ficar sem limits depois, as pegs permanecem no último preço.
- Quando a peg volta para um preço mais baixo, ela também entra na frente da fila, inclusive à frente de ordens criadas antes dela. É uma consequência direta da regra acima.
- Alterar uma peg a transforma numa limit com o preço informado.

**Mensagem de criação:** toda limit order imprime `Order created` com o seu id, inclusive quando é executada na hora, para que o usuário sempre saiba o identificador da ordem.

**Validação de entrada:** feita no `main.py` (lado válido, números positivos, comando completo). Comandos inválidos mostram `Comando inválido`, sem interromper o programa. Uma peg sem preço de referência também é recusada com `Comando inválido`. A engine assume que recebe valores válidos.

**Maiúsculas:** os comandos são convertidos para minúsculas, então `LIMIT BUY 10 100` funciona como `limit buy 10 100`.

## Limitações e melhorias possíveis

- O cancelamento procura a ordem no livro inteiro (O(n)). Um dicionário id → ordem permitiria encontrá-la diretamente.
- O melhor preço é calculado com `min`/`max` sobre os preços (O(n)). Uma estrutura ordenada (heap ou árvore) manteria o melhor preço disponível diretamente.
- Não há proteção contra erros de preço ("fat finger"); nas bolsas reais, isso é tratado com bandas de preço e circuit breakers.
- Todos os dados ficam em memória e são perdidos ao encerrar o programa, como o enunciado permite.
