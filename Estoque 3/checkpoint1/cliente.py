"""O cliente das etapas 1 e 2 usa o mesmo protocolo da versão final."""
import argparse
import json
from protocolo import SKU, chamar


def executar(pedido, principal):
    try:
        return chamar(principal, pedido)
    except (OSError, ValueError):
        return {"ok": False, "erro": "Servidor sem resposta. Confira o saldo antes de repetir uma venda."}


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("op", choices=("consultar", "vender"))
    p.add_argument("quantidade", nargs="?", type=int)
    p.add_argument("--sku", default=SKU)
    p.add_argument("--etapa", type=int, choices=(1,), default=1)
    p.add_argument("--porta", type=int, default=7100)
    args = p.parse_args()
    if (args.op == "vender") != (args.quantidade is not None):
        p.error("Informe quantidade apenas para vender")
    pedido = dict(op=args.op, sku=args.sku)
    if args.quantidade is not None:
        pedido["quantidade"] = args.quantidade
    resultado = executar(pedido, args.porta)
    print(json.dumps(resultado, ensure_ascii=False))
    raise SystemExit(0 if resultado.get("ok") else 1)
