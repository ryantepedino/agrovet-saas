from __future__ import annotations
import sqlite3
from pathlib import Path
from typing import Optional, Tuple, Dict, Any, List

DB_PATH = Path(__file__).resolve().parent / "relatorios.db"

DDL = """
CREATE TABLE IF NOT EXISTS relatorios (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  nome_da_fazenda TEXT NOT NULL,
  data TEXT NOT NULL,
  taxa_prenhez REAL,
  taxa_concepcao REAL,
  taxa_servico REAL,
  partos_estimados REAL
);
"""

def conn() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    c = sqlite3.connect(DB_PATH)
    c.execute("PRAGMA journal_mode=WAL;")
    c.execute("PRAGMA synchronous=NORMAL;")
    return c

def init_db() -> None:
    with conn() as c:
        c.executescript(DDL)

def insert_relatorio(
    nome_da_fazenda: str,
    data: str,
    taxa_prenhez: Optional[float],
    taxa_concepcao: Optional[float],
    taxa_servico: Optional[float],
    partos_estimados: Optional[float],
) -> int:
    with conn() as c:
        cur = c.execute(
            """
            INSERT INTO relatorios
            (nome_da_fazenda, data, taxa_prenhez, taxa_concepcao, taxa_servico, partos_estimados)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (nome_da_fazenda, data, taxa_prenhez, taxa_concepcao, taxa_servico, partos_estimados),
        )
        return cur.lastrowid

def delete_relatorio(_id: int) -> None:
    with conn() as c:
        c.execute("DELETE FROM relatorios WHERE id=?", (_id,))

def list_relatorios(
    search: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    order: str = "recentes",
    limit: Optional[int] = 100,
):
    q = ["SELECT id, nome_da_fazenda, data, taxa_prenhez, taxa_concepcao, taxa_servico, partos_estimados FROM relatorios"]
    params: List[Any] = []
    wh = []
    if search:
        wh.append("nome_da_fazenda LIKE ?")
        params.append(f"%{search}%")
    if date_from:
        wh.append("date(data) >= date(?)")
        params.append(date_from)
    if date_to:
        wh.append("date(data) <= date(?)")
        params.append(date_to)
    if wh:
        q.append("WHERE " + " AND ".join(wh))

    if order == "nome":
        q.append("ORDER BY nome_da_fazenda COLLATE NOCASE ASC, date(data) DESC")
    elif order == "antigos":
        q.append("ORDER BY date(data) ASC")
    else:
        q.append("ORDER BY date(data) DESC")

    if limit and limit > 0:
        q.append(f"LIMIT {int(limit)}")

    sql = " ".join(q)
    with conn() as c:
        cur = c.execute(sql, params)
        cols = [d[0] for d in cur.description]
        rows = cur.fetchall()
    return cols, rows

def kpis():
    sql = """
    SELECT
      COUNT(*) AS total_registros,
      AVG(taxa_prenhez)    AS media_prenhez,
      AVG(taxa_concepcao)  AS media_concepcao,
      AVG(taxa_servico)    AS media_servico,
      AVG(partos_estimados) AS media_partos
    FROM relatorios;
    """
    with conn() as c:
        cur = c.execute(sql)
        row = cur.fetchone()
    keys = ["total_registros","media_prenhez","media_concepcao","media_servico","media_partos"]
    return dict(zip(keys, row or [0, None, None, None, None]))
