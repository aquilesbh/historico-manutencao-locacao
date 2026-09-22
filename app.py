"""
Histórico de Manutenção — Locação
----------------------------------
Aplicativo simples para registrar reclamações/manutenções de imóveis
alugados: toda vez que um inquilino ou proprietário ligar, o atendente
registra a ocorrência aqui. Fica salvo no histórico do imóvel e visível
para toda a equipe, com uma tela de pendências para quem precisa
acompanhar o que ainda está em aberto.

Como rodar:
    python3 -m venv .venv
    source .venv/bin/activate        (Windows: .venv\\Scripts\\activate)
    pip install -r requirements.txt
    python app.py
Depois abra http://localhost:5000 no navegador.
"""

import os
import sqlite3
from datetime import date, datetime

from flask import Flask, g, redirect, render_template, request, url_for

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "instance", "historico.db")

# Lista fixa de pessoas que podem registrar ocorrências.
# Para adicionar/remover alguém da equipe, edite esta lista.
EQUIPE = ["Aquiles", "Durval", "Gisela", "Ingrid", "Elizete"]

QUEM_LIGOU_OPCOES = ["Inquilino", "Proprietário", "Outro"]

app = Flask(__name__)


# ---------------------------------------------------------------------------
# Banco de dados
# ---------------------------------------------------------------------------

def get_db():
    if "db" not in g:
        os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
        g.db = sqlite3.connect(DB_PATH)
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON")
    return g.db


@app.teardown_appcontext
def close_db(_exc=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    db = sqlite3.connect(DB_PATH)
    db.executescript(
        """
        CREATE TABLE IF NOT EXISTS registros (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            data TEXT NOT NULL,
            codigo_contrato TEXT NOT NULL,
            imovel TEXT NOT NULL DEFAULT '',
            quem_ligou_tipo TEXT NOT NULL DEFAULT 'Inquilino',
            quem_ligou_nome TEXT NOT NULL DEFAULT '',
            quem_ligou_telefone TEXT NOT NULL DEFAULT '',
            descricao TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'pendente',   -- 'pendente' | 'resolvido'
            acao_andamento TEXT NOT NULL DEFAULT '',
            autor TEXT NOT NULL,
            criado_em TEXT NOT NULL,
            atualizado_em TEXT NOT NULL
        );
        """
    )
    db.commit()
    db.close()


# ---------------------------------------------------------------------------
# Páginas
# ---------------------------------------------------------------------------

@app.route("/")
def index():
    return redirect(url_for("pendencias"))


@app.route("/pendencias")
def pendencias():
    """Painel para a equipe acompanhar o que ainda está em aberto,
    em todos os imóveis/contratos."""
    db = get_db()
    rows = db.execute(
        """
        SELECT * FROM registros
        WHERE status = 'pendente'
        ORDER BY data ASC, id ASC
        """
    ).fetchall()

    hoje = date.today()
    pendencias_list = []
    dias_max = 0
    imoveis = set()
    for r in rows:
        try:
            dias = (hoje - date.fromisoformat(r["data"])).days
        except ValueError:
            dias = 0
        dias = max(dias, 0)
        dias_max = max(dias_max, dias)
        imoveis.add(r["codigo_contrato"])
        pendencias_list.append({**dict(r), "dias_em_aberto": dias})

    pendencias_list.sort(key=lambda x: x["dias_em_aberto"], reverse=True)

    stats = {
        "total": len(pendencias_list),
        "urgentes": sum(1 for p in pendencias_list if p["dias_em_aberto"] > 7),
        "imoveis": len(imoveis),
    }

    just_saved = request.args.get("salvo")
    return render_template(
        "pendencias.html", pendencias=pendencias_list, stats=stats, just_saved=just_saved
    )


@app.route("/historico")
def historico():
    """Histórico completo, com busca por contrato/descrição e filtro de status."""
    db = get_db()
    busca = request.args.get("q", "").strip()
    status_filtro = request.args.get("status", "todos")

    query = "SELECT * FROM registros WHERE 1=1"
    params = []
    if busca:
        query += " AND (codigo_contrato LIKE ? OR imovel LIKE ? OR descricao LIKE ?)"
        like = f"%{busca}%"
        params += [like, like, like]
    if status_filtro == "resolvidos":
        query += " AND status = 'resolvido'"
    elif status_filtro == "pendentes":
        query += " AND status = 'pendente'"
    query += " ORDER BY data DESC, id DESC"

    rows = db.execute(query, params).fetchall()
    return render_template(
        "historico.html", registros=rows, busca=busca, status_filtro=status_filtro
    )


@app.route("/novo", methods=["GET", "POST"])
def novo():
    if request.method == "POST":
        db = get_db()
        agora = datetime.now().isoformat(timespec="seconds")
        status = "resolvido" if request.form.get("status") == "resolvido" else "pendente"
        acao = request.form.get("acao_andamento", "").strip() if status == "pendente" else ""

        db.execute(
            """
            INSERT INTO registros (
                data, codigo_contrato, imovel, quem_ligou_tipo, quem_ligou_nome,
                quem_ligou_telefone, descricao, status, acao_andamento, autor,
                criado_em, atualizado_em
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                request.form.get("data") or date.today().isoformat(),
                request.form.get("codigo_contrato", "").strip(),
                request.form.get("imovel", "").strip(),
                request.form.get("quem_ligou_tipo", "Inquilino"),
                request.form.get("quem_ligou_nome", "").strip(),
                request.form.get("quem_ligou_telefone", "").strip(),
                request.form.get("descricao", "").strip(),
                status,
                acao,
                request.form.get("autor", ""),
                agora,
                agora,
            ),
        )
        db.commit()
        return redirect(url_for("pendencias", salvo="1"))

    return render_template(
        "novo.html",
        hoje=date.today().isoformat(),
        equipe=EQUIPE,
        quem_ligou_opcoes=QUEM_LIGOU_OPCOES,
    )


@app.route("/registros/<int:registro_id>/status", methods=["POST"])
def alternar_status(registro_id):
    """Botão de alternar entre Resolvido / Não resolvido."""
    db = get_db()
    row = db.execute("SELECT status FROM registros WHERE id = ?", (registro_id,)).fetchone()
    if row is None:
        return redirect(request.referrer or url_for("pendencias"))

    novo_status = "pendente" if row["status"] == "resolvido" else "resolvido"
    agora = datetime.now().isoformat(timespec="seconds")
    acao = request.form.get("acao_andamento", "").strip()

    if novo_status == "resolvido":
        db.execute(
            "UPDATE registros SET status = ?, atualizado_em = ? WHERE id = ?",
            (novo_status, agora, registro_id),
        )
    else:
        db.execute(
            "UPDATE registros SET status = ?, acao_andamento = ?, atualizado_em = ? WHERE id = ?",
            (novo_status, acao, agora, registro_id),
        )
    db.commit()
    return redirect(request.referrer or url_for("pendencias"))


@app.route("/registros/<int:registro_id>/acao", methods=["POST"])
def atualizar_acao(registro_id):
    """Atualiza o texto de 'o que está sendo feito para resolver'."""
    db = get_db()
    agora = datetime.now().isoformat(timespec="seconds")
    db.execute(
        "UPDATE registros SET acao_andamento = ?, atualizado_em = ? WHERE id = ?",
        (request.form.get("acao_andamento", "").strip(), agora, registro_id),
    )
    db.commit()
    return redirect(request.referrer or url_for("pendencias"))


if __name__ == "__main__":
    init_db()
    app.run(debug=True, host="0.0.0.0", port=5000)
else:
    init_db()
