"""Servidor de estoque. Um processo por nó e um banco SQLite por processo."""
import argparse
import socket
import sqlite3
import threading
from contextlib import closing
from pathlib import Path
from time import sleep

from protocolo import HOST, SKU, chamar, enviar, receber


def banco(caminho):
    return sqlite3.connect(caminho, timeout=3)


def iniciar(caminho, replica):
    with closing(banco(caminho)) as db, db:
        db.execute("CREATE TABLE IF NOT EXISTS estoque (id INTEGER PRIMARY KEY, saldo INTEGER, versao INTEGER)")
        # Versão -1 indica que esta réplica ainda não recebeu uma cópia.
        db.execute("INSERT OR IGNORE INTO estoque VALUES (1, ?, ?)", (0 if replica else 10, -1 if replica else 0))


def processar(cfg, pedido):
    op = pedido.get("op")
    if pedido.get("sku") != SKU or op not in ("consultar", "vender"):
        return {"ok": False, "erro": "Produto ou operação desconhecidos"}
    with closing(banco(cfg.banco)) as db, db:
        if op == "vender":
            if cfg.replica:
                return {"ok": False, "erro": "Réplica em modo somente leitura"}
            qtd = pedido.get("quantidade")
            if type(qtd) is not int or qtd < 1:
                return {"ok": False, "erro": "Quantidade deve ser um inteiro positivo"}
            db.execute("BEGIN IMMEDIATE")
            saldo, = db.execute("SELECT saldo FROM estoque WHERE id=1").fetchone()
            if qtd > saldo:
                return {"ok": False, "erro": "Estoque insuficiente"}
            db.execute("UPDATE estoque SET saldo=saldo-?, versao=versao+1 WHERE id=1", (qtd,))
        saldo, versao = db.execute("SELECT saldo, versao FROM estoque WHERE id=1").fetchone()
        if versao < 0:
            return {"ok": False, "erro": "Aguardando primeira sincronização"}
        return dict(ok=True, sku=SKU, saldo=saldo, versao=versao,
                    no="replica" if cfg.replica else "principal")


def sincronizar(cfg):
    online = None
    while True:
        try:
            estado = chamar(cfg.origem, dict(op="consultar", sku=SKU))
            if not estado.get("ok") or estado.get("no") != "principal":
                raise ValueError("Origem inválida")
            with closing(banco(cfg.banco)) as db, db:
                mudou = db.execute("UPDATE estoque SET saldo=?, versao=? WHERE id=1 AND versao<?",
                                   (estado["saldo"], estado["versao"], estado["versao"])).rowcount
            if mudou:
                print("Cópia aplicada:", estado, flush=True)
            atual = True
        except (OSError, ValueError, sqlite3.Error):
            atual = False
        if atual != online:
            print("Origem acessível" if atual else "Origem indisponível", flush=True)
            online = atual
        sleep(cfg.intervalo)


def atender(sock, cfg):
    with sock:
        sock.settimeout(2)
        try:
            resposta = processar(cfg, receber(sock))
        except (ValueError, RecursionError):
            resposta = {"ok": False, "erro": "Mensagem inválida"}
        except sqlite3.Error:
            resposta = {"ok": False, "erro": "Falha local de armazenamento"}
        except OSError:
            return
        try:
            enviar(sock, resposta)
        except OSError:
            pass


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--etapa", type=int, choices=(1, 2, 3), default=3)
    parser.add_argument("--replica", action="store_true")
    parser.add_argument("--porta", type=int)
    parser.add_argument("--origem", type=int, default=7100)
    parser.add_argument("--intervalo", type=float, default=1)
    parser.add_argument("--banco", type=Path)
    cfg = parser.parse_args()
    if cfg.replica and cfg.etapa == 1:
        parser.error("A etapa 1 possui apenas o servidor principal")
    if cfg.intervalo <= 0:
        parser.error("Intervalo deve ser positivo")
    papel = "replica" if cfg.replica else "principal"
    cfg.banco = cfg.banco or Path(f"etapa{cfg.etapa}-{papel}.sqlite")
    porta = cfg.porta or (7101 if cfg.replica else 7100)
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as servidor:
        servidor.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        servidor.bind((HOST, porta))
        servidor.listen()
        iniciar(cfg.banco, cfg.replica)
        if cfg.replica:
            threading.Thread(target=sincronizar, args=(cfg,), daemon=True).start()
        print(f"{papel} em {HOST}:{porta}, banco {cfg.banco}", flush=True)
        while True:
            conexao, _ = servidor.accept()
            threading.Thread(target=atender, args=(conexao, cfg), daemon=True).start()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        pass
