"""Uma conexão TCP transporta um pedido e uma resposta JSON, em UTF-8."""
import json
import socket

HOST = "127.0.0.1"
LIMITE = 8192
SKU = "TENIS-42"


def enviar(sock, mensagem):
    sock.sendall((json.dumps(mensagem, ensure_ascii=False) + "\n").encode())


def receber(sock):
    with sock.makefile("rb") as fluxo:
        linha = fluxo.readline(LIMITE + 1)
    if len(linha) > LIMITE or not linha.endswith(b"\n"):
        raise ValueError("Mensagem longa ou incompleta")
    objeto = json.loads(linha)
    if not isinstance(objeto, dict):
        raise ValueError("Envie um objeto JSON")
    return objeto


def chamar(porta, pedido):
    with socket.create_connection((HOST, porta), timeout=1) as sock:
        enviar(sock, pedido)
        return receber(sock)
