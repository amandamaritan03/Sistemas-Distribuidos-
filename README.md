# Estoque distribuído para marketplace

Trabalho de Amanda Maritan e Matheus Oliveira para Sistemas Distribuídos. Cada pasta de código é uma versão executável independente. O exemplo acompanha um único produto, TENIS-42, com 10 pares no primeiro uso. Testado com Python 3.12 em Linux. Usa apenas a biblioteca padrão.

## Comece pela demonstração

Extraia o ZIP, entre na pasta Estoque e execute:

    python3 demo.py --guiada

O programa inicia processos reais em portas locais livres e bancos temporários. Pressione Enter para vender, derrubar o principal e restaurá-lo. Pode repetir a apresentação desde o início sem alterar seus bancos manuais. Para rodar todos os testes sem pausas, execute python3 demo.py. No Windows, substitua python3 por py -3.

## Checkpoint 1

Em dois terminais abertos na pasta Estoque, inicie o servidor no primeiro e execute o cliente no segundo:

    python3 checkpoint1/servidor.py
    python3 checkpoint1/cliente.py consultar
    python3 checkpoint1/cliente.py vender 2

## Checkpoint 2

Encerre os servidores da etapa anterior com Ctrl+C antes de usar as mesmas portas. Em três terminais, execute o principal, a réplica e as operações de cliente, respectivamente:

    python3 checkpoint2/servidor.py
    python3 checkpoint2/servidor.py --replica
    python3 checkpoint1/cliente.py vender 2
    python3 checkpoint2/cliente.py consultar --porta 7101

Observe as respostas e o log “Cópia aplicada” da réplica. Os campos no, versao e saldo identificam o nó e o estado. A réplica busca atualizações a cada segundo por padrão. Use --intervalo 5 ao iniciá-la para ampliar a janela de atraso na demonstração.

## Checkpoint 3 e entrega final

Feche os servidores anteriores. Na pasta Estoque, use um terminal para cada servidor e um terceiro para os comandos de cliente:

    python3 codigo/servidor.py
    python3 codigo/servidor.py --replica
    python3 codigo/cliente.py vender 2
    python3 codigo/cliente.py consultar --porta 7101

Espere a réplica exibir a versão da venda. Interrompa apenas o principal com Ctrl+C. No terminal do cliente, execute:

    python3 codigo/cliente.py consultar
    python3 codigo/cliente.py vender 1

A consulta identifica a réplica. A escrita informa que falta confirmação. Reinicie o principal no mesmo diretório e repita a consulta: o campo no volta a indicar principal. Para reiniciar um nó após uma falha, use sempre o mesmo banco. A demo automática já cuida desses passos.

## Arquivos e preparação da entrega

- checkpoint1/ e checkpoint2/ guardam os códigos independentes das etapas anteriores. codigo/ contém a versão final completa.
- relatorios/ contém os três relatórios em PDF e seus textos editáveis em Markdown.
- apresentacao/ contém os slides em PDF e o roteiro de 8min30.
- testes/execucao.txt contém a saída da execução validada. Cada linha OK vem de uma verificação do resultado recebido.
- Na autoavaliação, cada integrante registra o que executou, quais resultados observou e que decisão de arquitetura consegue justificar.
- Os bancos manuais são separados por etapa e por papel no diretório de execução. Os serviços escutam em 127.0.0.1. O teste demonstra falha isolada de processo no mesmo computador.
