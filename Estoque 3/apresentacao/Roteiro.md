# Roteiro de Amanda Maritan e Matheus Oliveira • 8min30

Antes de começar, extraiam a pasta, abram o terminal dentro dela e rodem a demonstração uma vez para conferir o ambiente. Deixem python3 demo.py --guiada digitado e pronto para o slide 5. Quem não estiver falando cuida do terminal.

| Tempo | Slide | Quem | Fala e ação |
|---|---|---|---|
| 0:00–0:45 | 1 | Amanda | Abre com a pergunta: “Uma loja de Franca tem dez pares do mesmo tênis. Se o servidor de estoque cair logo depois de uma venda, que número o vendedor vai ver?” Apresenta o produto TENIS-42. |
| 0:45–1:55 | 2 | Amanda | Explica que cliente e servidor são processos separados. Mostra no código onde o cliente chama create_connection e onde o servidor chama accept. Comenta que a quebra de linha marca o fim do JSON. Uma venda de dois pares leva o saldo a oito. |
| 1:55–3:10 | 3 | Amanda | Fala dos dois bancos separados e de como a réplica busca saldo e versão no principal. Mostra que, no intervalo entre uma cópia e outra, a réplica ainda pode responder dez mesmo com o principal já em oito. |
| 3:10–4:05 | 4 | Matheus | Explica por que só o principal vende. Basta perder a comunicação para o cliente mandar a consulta para a réplica. Comenta que, só pelo timeout, não dá para saber se o servidor caiu ou se foi a rede. |
| 4:05–7:20 | 5 | Matheus | Roda python3 demo.py --guiada. Na primeira pausa, mostra saldo 8 e versão 1 nos dois nós. Na segunda, derruba o principal e mostra a consulta na réplica e a venda sem confirmação. Na terceira, reinicia o principal e mostra as vendas voltando até o saldo chegar a zero. |
| 7:20–8:30 | 6 | Amanda | Comenta os seis pedidos disputando dois pares. Fecha com o compromisso da arquitetura: dá para consultar durante a queda, mas só o principal confirma venda. Os 90 segundos que sobram ficam para perguntas. |

A divisão pode ser trocada. O importante é cada um conseguir explicar a parte do outro se o professor perguntar.

## Perguntas para ensaiar

**Para que serve a versão?** A réplica só aplica estados mais novos que o seu. Como temos um único produto, copiar saldo e versão já basta para chegar ao estado atual, mesmo que ela tenha perdido várias vendas no meio do caminho.

**E se a resposta de uma venda se perder?** A venda pode ter sido gravada. O cliente avisa que falta confirmação e não reenvia sozinho. Numa loja de verdade, cada venda precisaria de um identificador próprio, para que o reenvio não descontasse duas vezes e desse para consultar se ela entrou.

**E se os dois servidores caírem?** Enquanto os dois estiverem fora, a consulta falha com uma mensagem clara. Os arquivos SQLite continuam lá quando os processos voltam. Já a perda do disco do principal pode apagar vendas que ainda não chegaram à réplica.

**Como dividir a demonstração?** Quem cuida do terminal avança as pausas. Quem está falando explica antes o que deve aparecer na tela. Depois da recuperação, voltem ao slide 6 para fechar.
