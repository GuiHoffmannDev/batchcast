"""Carrega o CSV do IndPenSim contornando o defeito de cabecalho.

O arquivo original tem 2239 campos de cabecalho contra 2237 por linha de dados:
dois rotulos extras, 'Batch ID' e 'Fault flag', antes das colunas Raman.
Lemos por posicao e reconstruimos o identificador de batelada.
"""
import sys
import numpy as np
import pandas as pd


def diagnose(path, n=3):
    with open(path, "r", errors="replace") as fh:
        head = fh.readline().rstrip("\n").split(",")
        rows = [fh.readline().rstrip("\n").split(",") for _ in range(n)]
    print(f"campos no cabecalho : {len(head)}")
    print(f"campos nas linhas   : {[len(r) for r in rows]}")
    print(f"primeiros 12 rotulos: {head[:12]}")
    sus = [(i, h) for i, h in enumerate(head) if h.strip() in ("Batch ID", "Fault flag")]
    print(f"rotulos suspeitos   : {sus}")
    nonraman = [(i, h) for i, h in enumerate(head) if "raman" not in h.lower()]
    print(f"colunas nao-Raman   : {len(nonraman)}")
    for i, h in nonraman[:60]:
        print(f"   [{i:4d}] {h}")
    return head, rows


if __name__ == "__main__":
    diagnose(sys.argv[1])
