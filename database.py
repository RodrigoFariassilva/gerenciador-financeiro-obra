import sqlite3
from pathlib import Path
import pandas as pd

DB_DIR = Path(__file__).resolve().parent / "database"
DB_DIR.mkdir(exist_ok=True)
DB_PATH = DB_DIR / "obra.db"

def conectar():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def init_db():
    with conectar() as conn:
        conn.executescript("""
        CREATE TABLE IF NOT EXISTS obras (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            cliente TEXT,
            local TEXT,
            data_inicio TEXT,
            data_fim TEXT,
            orcamento_total REAL NOT NULL DEFAULT 0,
            observacoes TEXT
        );
        CREATE TABLE IF NOT EXISTS gastos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            obra_id INTEGER NOT NULL,
            data TEXT NOT NULL,
            descricao TEXT NOT NULL,
            categoria TEXT NOT NULL,
            fornecedor TEXT,
            valor REAL NOT NULL,
            status TEXT NOT NULL DEFAULT 'Pendente',
            forma_pagamento TEXT,
            parcelas INTEGER NOT NULL DEFAULT 1,
            extraordinario INTEGER NOT NULL DEFAULT 0,
            justificativa TEXT,
            comprovante TEXT,
            FOREIGN KEY (obra_id) REFERENCES obras(id) ON DELETE CASCADE
        );
        CREATE TABLE IF NOT EXISTS orcamentos_categoria (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            obra_id INTEGER NOT NULL,
            categoria TEXT NOT NULL,
            valor_orcado REAL NOT NULL DEFAULT 0,
            UNIQUE(obra_id, categoria),
            FOREIGN KEY (obra_id) REFERENCES obras(id) ON DELETE CASCADE
        );
        """)

def listar_obras():
    with conectar() as conn:
        return [dict(r) for r in conn.execute("SELECT * FROM obras ORDER BY id DESC").fetchall()]

def criar_obra(nome, cliente, local, data_inicio, data_fim, orcamento_total, observacoes):
    with conectar() as conn:
        cur = conn.execute("""INSERT INTO obras
            (nome, cliente, local, data_inicio, data_fim, orcamento_total, observacoes)
            VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (nome, cliente, local, data_inicio, data_fim, orcamento_total, observacoes))
        return cur.lastrowid

def obter_obra(obra_id):
    with conectar() as conn:
        row = conn.execute("SELECT * FROM obras WHERE id = ?", (obra_id,)).fetchone()
        return dict(row) if row else None

def atualizar_obra(obra_id, nome, cliente, local, orcamento_total, observacoes):
    with conectar() as conn:
        conn.execute("""UPDATE obras SET nome=?, cliente=?, local=?, orcamento_total=?, observacoes=?
                        WHERE id=?""", (nome, cliente, local, orcamento_total, observacoes, obra_id))

def adicionar_gasto(obra_id, data, descricao, categoria, fornecedor, valor, status,
                    forma_pagamento, parcelas, extraordinario, justificativa, comprovante):
    with conectar() as conn:
        conn.execute("""INSERT INTO gastos
            (obra_id, data, descricao, categoria, fornecedor, valor, status, forma_pagamento,
             parcelas, extraordinario, justificativa, comprovante)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (obra_id, data, descricao, categoria, fornecedor, valor, status, forma_pagamento,
             parcelas, extraordinario, justificativa, comprovante))

def listar_gastos(obra_id):
    with conectar() as conn:
        rows = conn.execute("SELECT * FROM gastos WHERE obra_id=? ORDER BY data DESC, id DESC", (obra_id,)).fetchall()
        return [dict(r) for r in rows]

def excluir_gasto(gasto_id):
    with conectar() as conn:
        conn.execute("DELETE FROM gastos WHERE id=?", (gasto_id,))

def listar_orcamentos(obra_id):
    with conectar() as conn:
        rows = conn.execute("SELECT * FROM orcamentos_categoria WHERE obra_id=? ORDER BY categoria", (obra_id,)).fetchall()
        return [dict(r) for r in rows]

def salvar_orcamento(obra_id, categoria, valor):
    with conectar() as conn:
        conn.execute("""INSERT INTO orcamentos_categoria (obra_id, categoria, valor_orcado)
                        VALUES (?, ?, ?)
                        ON CONFLICT(obra_id, categoria) DO UPDATE SET valor_orcado=excluded.valor_orcado""",
                     (obra_id, categoria, valor))

def resumo_obra(obra_id):
    gastos = listar_gastos(obra_id)
    if not gastos:
        return {
            "total_registrado": 0.0,
            "total_pago": 0.0,
            "total_extraordinario": 0.0,
            "por_categoria": pd.DataFrame(columns=["categoria", "total"])
        }
    df = pd.DataFrame(gastos)
    return {
        "total_registrado": float(df["valor"].sum()),
        "total_pago": float(df.loc[df["status"] == "Pago", "valor"].sum()),
        "total_extraordinario": float(df.loc[df["extraordinario"] == 1, "valor"].sum()),
        "por_categoria": df.groupby("categoria", as_index=False)["valor"].sum().rename(columns={"valor":"total"})
    }
