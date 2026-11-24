"""Servidor de estoque. Um processo por nó e um banco SQLite por processo."""
import argparse
import socket
import sqlite3
import threading
from contextlib import closing
from pathlib import Path

from protocolo import HOST, SKU, enviar, receber


def banco(caminho):
    return sqlite3.connect(caminho, timeout=3)


def iniciar(caminho):
    with closing(banco(caminho)) as db, db:
        db.execute("CREATE TABLE IF NOT EXISTS estoque (id INTEGER PRIMARY KEY, saldo INTEGER, versao INTEGER)")
        db.execute("INSERT OR IGNORE INTO estoque VALUES (1, ?, ?)", (10, 0))


def processar(cfg, pedido):
    op = pedido.get("op")
    if pedido.get("sku") != SKU or op not in ("consultar", "vender"):
        return {"ok": False, "erro": "Produto ou operação desconhecidos"}
    with closing(banco(cfg.banco)) as db, db:
        if op == "vender":
            qtd = pedido.get("quantidade")
            if type(qtd) is not int or qtd < 1:
                return {"ok": False, "erro": "Quantidade deve ser um inteiro positivo"}
            db.execute("BEGIN IMMEDIATE")
            saldo, = db.execute("SELECT saldo FROM estoque WHERE id=1").fetchone()
            if qtd > saldo:
                return {"ok": False, "erro": "Estoque insuficiente"}
            db.execute("UPDATE estoque SET saldo=saldo-?, versao=versao+1 WHERE id=1", (qtd,))
        saldo, versao = db.execute("SELECT saldo, versao FROM estoque WHERE id=1").fetchone()
        return dict(ok=True, sku=SKU, saldo=saldo, versao=versao,
                    no="principal")


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
    parser.add_argument("--etapa", type=int, choices=(1,), default=1)
    parser.add_argument("--porta", type=int)
    parser.add_argument("--banco", type=Path)
    cfg = parser.parse_args()
    cfg.banco = cfg.banco or Path("etapa1-principal.sqlite")
    porta = cfg.porta or 7100
    papel = "principal"
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as servidor:
        servidor.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        servidor.bind((HOST, porta))
        servidor.listen()
        iniciar(cfg.banco)
        print(f"{papel} em {HOST}:{porta}, banco {cfg.banco}", flush=True)
        while True:
            conexao, _ = servidor.accept()
            threading.Thread(target=atender, args=(conexao, cfg), daemon=True).start()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        pass
