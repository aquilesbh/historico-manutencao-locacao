# Histórico de Manutenção — Locação

Aplicativo simples para o ambiente de locação: toda vez que um **inquilino**
ou **proprietário** liga relatando um problema, o atendente registra a
ocorrência aqui. Fica salva no histórico do imóvel e visível para toda a
equipe, com uma tela de **pendências** para acompanhar o que ainda está em
aberto.

## Funcionalidades

- **Novo registro**: data, código do contrato, imóvel, quem ligou (tipo,
  nome e telefone), descrição do problema, quem está atendendo e a
  situação (Resolvido / Não resolvido).
- Quando marcado como **Não resolvido**, um campo extra guarda o que está
  sendo feito para resolver.
- **Pendências**: painel com todas as ocorrências em aberto, de todos os
  imóveis, com destaque para as que estão há mais de 7 dias sem solução.
- **Histórico completo**: busca por contrato, imóvel ou descrição, com
  filtro por status.
- Botão para alternar o status (Resolvido ⇄ Não resolvido) e atualizar a
  ação em andamento a qualquer momento.

## Equipe

Os registros são atribuídos a quem atendeu a ligação. A lista de pessoas
fica em `EQUIPE` no topo do `app.py`:

```python
EQUIPE = ["Aquiles", "Durval", "Gisela", "Ingrid", "Elizete"]
```

Para adicionar ou remover alguém, edite essa lista.

## Como rodar

Pré-requisito: Python 3.9+.

```bash
python3 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

Depois abra **http://localhost:5000** no navegador. Os dados ficam salvos
em `instance/historico.db` (SQLite), criado automaticamente na primeira
execução.

Para vários computadores da equipe acessarem o mesmo histórico, rode o
`app.py` em um computador/servidor central e acesse pelo endereço de rede
dele (ex.: `http://192.168.0.10:5000`), ou publique em um serviço de
hospedagem (Render, Railway, PythonAnywhere etc.).

## Estrutura

```
app.py               # backend Flask + banco SQLite
templates/           # páginas (pendências, histórico, novo registro)
static/style.css     # estilo visual
requirements.txt
```

## Versão

**v0.1.0** — primeira versão funcional: cadastro de ocorrências, painel de
pendências e histórico com busca/filtro.
