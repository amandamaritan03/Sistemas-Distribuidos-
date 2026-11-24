"""O cliente das etapas 1 e 2 usa o mesmo protocolo da versão final."""
import argparse
import json
from protocolo import SKU, chamar


def executar(pedido, principal, replica=None):
    try:
        return chamar(principal, pedido)
    except (OSError, ValueError):
        if pedido["op"] == "vender":
            return {"ok": False, "erro": "Principal sem resposta. Venda sem confirmação. Confira antes de repetir."}
        if replica is None:
            return {"ok": False, "erro": "Servidor indisponível"}
    try:
        resposta = chamar(replica, pedido)
        resposta["aviso"] = "Principal indisponível. Consulta da última cópia."
        return resposta
    except (OSError, ValueError):
        return {"ok": False, "erro": "Ambos os nós indisponíveis"}


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("op", choices=("consultar", "vender"))
    p.add_argument("quantidade", nargs="?", type=int)
    p.add_argument("--sku", default=SKU)
    p.add_argument("--etapa", type=int, choices=(1, 2, 3), default=3)
    p.add_argument("--porta", type=int, default=7100)
    p.add_argument("--secundaria", type=int, default=7101)
    args = p.parse_args()
    if (args.op == "vender") != (args.quantidade is not None):
        p.error("Informe quantidade apenas para vender")
    pedido = dict(op=args.op, sku=args.sku)
    if args.quantidade is not None:
        pedido["quantidade"] = args.quantidade
    resultado = executar(pedido, args.porta, args.secundaria if args.etapa == 3 else None)
    print(json.dumps(resultado, ensure_ascii=False))
    raise SystemExit(0 if resultado.get("ok") else 1)
