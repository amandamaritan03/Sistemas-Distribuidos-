"""Demonstração ao vivo e testes de integração, com processos e bancos isolados."""
import argparse
from concurrent.futures import ThreadPoolExecutor
from contextlib import ExitStack
import json
from pathlib import Path
import socket
import subprocess
import sys
from tempfile import TemporaryDirectory
from time import monotonic, sleep

CODIGO = Path(__file__).resolve().parent / "codigo"
sys.path.insert(0, str(CODIGO))
from protocolo import HOST, SKU, chamar

LEITURA = dict(op="consultar", sku=SKU)


def conferir(condicao, mensagem):
    if not condicao:
        raise RuntimeError(mensagem)
    print("OK  " + mensagem, flush=True)


def aguardar(porta, versao=None):
    limite = monotonic() + 7
    while monotonic() < limite:
        try:
            r = chamar(porta, LEITURA)
            if r.get("ok") and (versao is None or r["versao"] == versao):
                return r
        except (OSError, ValueError):
            pass
        sleep(0.05)
    raise RuntimeError("Tempo de espera esgotado para o nó")


def parar(processo):
    if processo.poll() is None:
        processo.kill()
        processo.wait(timeout=5)


def demonstrar(interativo):
    def pausa(texto):
        if interativo:
            input(texto + " [Enter] ")

    with TemporaryDirectory() as pasta, ExitStack() as recursos:
        with socket.socket() as a, socket.socket() as b:
            a.bind((HOST, 0))
            b.bind((HOST, 0))
            principal, replica = a.getsockname()[1], b.getsockname()[1]

        def iniciar(etapa, secundario=False):
            papel = "replica" if secundario else "principal"
            porta = replica if secundario else principal
            args = ["--etapa", str(etapa), "--porta", str(porta), "--banco", str(Path(pasta) / papel)]
            if secundario:
                args += ["--replica", "--origem", str(principal), "--intervalo", "0.2"]
            proc = subprocess.Popen([sys.executable, str((CODIGO if etapa == 3 else CODIGO.parent / f"checkpoint{etapa}") / "servidor.py"), *args],
                                    stdout=subprocess.DEVNULL)
            recursos.callback(parar, proc)
            return proc

        def cliente(op, *extras, etapa=3):
            cmd = [sys.executable, str((CODIGO if etapa == 3 else CODIGO.parent / f"checkpoint{etapa}") / "cliente.py"), op, *extras, "--etapa", str(etapa),
                   "--porta", str(principal)]
            if etapa == 3:
                cmd += ["--secundaria", str(replica)]
            res = subprocess.run(cmd, capture_output=True, text=True, timeout=6)
            print("  cliente:", res.stdout.strip(), flush=True)
            return json.loads(res.stdout)

        print("CHECKPOINT 1 | comunicação TCP")
        p = iniciar(1)
        conferir(aguardar(principal)["saldo"] == 10, "Saldo inicial de 10 pares")
        conferir(cliente("consultar", etapa=1)["saldo"] == 10, "Cliente do CP1 conectado")
        with ThreadPoolExecutor(max_workers=2) as pool:
            leituras = list(pool.map(lambda _: chamar(principal, LEITURA), range(2)))
        conferir(all(r["saldo"] == 10 for r in leituras), "Dois clientes consultaram o servidor do CP1")
        parar(p)

        print("CHECKPOINT 2 | replicação")
        p = iniciar(2)
        aguardar(principal)
        s = iniciar(2, True)
        aguardar(replica, 0)
        pausa("Registrar a venda de dois pares?")
        conferir(cliente("vender", "2", etapa=1)["saldo"] == 8, "Cliente do CP1 vende no CP2")
        copia = aguardar(replica, 1)
        print("  réplica:", copia)
        conferir(copia["saldo"] == 8, "Réplica convergiu para 8 pares na versão 1")
        parar(s)
        parar(p)

        print("CHECKPOINT 3 | falha real de processo")
        p = iniciar(3)
        aguardar(principal, 1)
        s = iniciar(3, True)
        aguardar(replica, 1)
        pausa("Encerrar o processo principal e repetir a consulta?")
        parar(p)
        r = cliente("consultar")
        conferir(r["no"] == "replica" and r["saldo"] == 8, "Consulta desviada para a cópia")
        conferir(not cliente("vender", "1")["ok"], "Venda sem confirmação durante a falha")
        venda = dict(op="vender", quantidade=1, sku=SKU)
        conferir(not chamar(replica, venda)["ok"], "Réplica recusa escrita direta")
        pausa("Restaurar o primário com o mesmo banco?")
        p = iniciar(3)
        aguardar(principal, 1)
        conferir(cliente("consultar")["no"] == "principal", "Cliente volta ao principal automaticamente")
        parar(s)
        conferir(cliente("vender", "6")["saldo"] == 2, "Venda aceita com a réplica parada")
        s = iniciar(3, True)
        conferir(aguardar(replica, 2)["saldo"] == 2, "Réplica recupera a atualização perdida")
        with ThreadPoolExecutor(max_workers=6) as pool:
            respostas = list(pool.map(lambda _: chamar(principal, venda), range(6)))
        conferir(sum(r["ok"] for r in respostas) == 2, "Seis vendas concorrentes disputam dois pares: duas aceitas")
        conferir(aguardar(replica, 4)["saldo"] == 0, "Ambos convergem para saldo zero")
        parar(s)
        parar(p)
        conferir(not cliente("consultar")["ok"], "Falha dos dois nós gera erro controlado")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--guiada", action="store_true", help="Pausa nos pontos da apresentação")
    demonstrar(parser.parse_args().guiada)
