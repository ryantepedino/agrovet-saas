from fastapi import APIRouter
import os
from glob import glob

router = APIRouter()

@router.get("/history")
def listar_historico():
    """
    Lista os relatórios PDF salvos em data/history/.
    Retorna nome e tamanho em KB de cada arquivo.
    """
    os.makedirs("data/history", exist_ok=True)
    arquivos = sorted(glob("data/history/*.pdf"), reverse=True)
    historico = []
    for arq in arquivos:
        nome = os.path.basename(arq)
        tamanho_kb = round(os.path.getsize(arq) / 1024, 1)
        historico.append({
            "arquivo": nome,
            "tamanho_kb": tamanho_kb
        })
    return {"ok": True, "historico": historico}
