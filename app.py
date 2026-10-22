import streamlit as st
import pandas as pd
import sqlite3
from datetime import date
from io import BytesIO
from database import (
    init_db, listar_obras, criar_obra, obter_obra, listar_gastos,
    adicionar_gasto, excluir_gasto, listar_orcamentos, salvar_orcamento,
    resumo_obra, atualizar_obra
)

st.set_page_config(page_title="Gerenciador de Obras", page_icon="🏗️", layout="wide")
init_db()

CATEGORIAS = [
    "Material", "Mão de obra", "Elétrica", "Hidráulica", "Estrutura",
    "Pintura", "Acabamento", "Equipamentos", "Transporte", "Documentação", "Outros"
]
STATUS = ["Pago", "Pendente", "Parcelado"]
PAGAMENTOS = ["Pix", "Dinheiro", "Cartão de crédito", "Cartão de débito", "Transferência", "Boleto", "Outro"]

def dinheiro(valor):
    return "R$ " + f"{float(valor or 0):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

def df_para_excel(df):
    buffer = BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Dados")
    return buffer.getvalue()

st.title("🏗️ Gerenciador Financeiro de Obras")
st.caption("Controle de orçamento, despesas comuns e gastos extraordinários — os dados ficam salvos localmente no computador.")

obras = listar_obras()
with st.sidebar:
    st.header("Navegação")
    pagina = st.radio("Escolha uma seção", [
        "Dashboard", "Obras", "Orçamento por categoria", "Lançar gasto",
        "Consultar gastos", "Relatórios e exportação"
    ])
    st.divider()
    if obras:
        opcoes = {f'{o["nome"]} (#{o["id"]})': o["id"] for o in obras}
        escolha = st.selectbox("Obra selecionada", list(opcoes.keys()))
        obra_id = opcoes[escolha]
    else:
        obra_id = None
        st.info("Cadastre uma obra na seção Obras para começar.")

if pagina == "Obras":
    st.subheader("Cadastrar uma obra")
    with st.form("nova_obra", clear_on_submit=True):
        nome = st.text_input("Nome da obra*", placeholder="Ex.: Reforma apartamento Centro")
        cliente = st.text_input("Cliente")
        local = st.text_input("Endereço/local")
        c1, c2 = st.columns(2)
        inicio = c1.date_input("Data de início", value=date.today())
        termino = c2.date_input("Previsão de término", value=None)
        orcamento = st.number_input("Orçamento total inicial (R$)", min_value=0.0, value=0.0, step=500.0)
        observacoes = st.text_area("Observações")
        enviar = st.form_submit_button("Cadastrar obra", type="primary")
        if enviar:
            if not nome.strip():
                st.error("Informe o nome da obra.")
            else:
                novo_id = criar_obra(nome.strip(), cliente.strip(), local.strip(), str(inicio),
                                     str(termino) if termino else None, orcamento, observacoes.strip())
                st.success(f"Obra cadastrada com sucesso! Código: {novo_id}")
                st.rerun()

    st.divider()
    st.subheader("Obras cadastradas")
    if obras:
        tabela = pd.DataFrame(obras)
        tabela = tabela.rename(columns={"id":"Código", "nome":"Obra", "cliente":"Cliente", "local":"Local",
                                        "data_inicio":"Início", "data_fim":"Previsão de término",
                                        "orcamento_total":"Orçamento inicial", "observacoes":"Observações"})
        st.dataframe(tabela, use_container_width=True, hide_index=True)
        if obra_id:
            obra = obter_obra(obra_id)
            st.markdown("#### Atualizar dados da obra selecionada")
            with st.form("editar_obra"):
                n = st.text_input("Nome", value=obra["nome"])
                c = st.text_input("Cliente", value=obra["cliente"] or "")
                l = st.text_input("Local", value=obra["local"] or "")
                o = st.number_input("Orçamento total inicial (R$)", min_value=0.0, value=float(obra["orcamento_total"] or 0), step=500.0)
                obs = st.text_area("Observações", value=obra["observacoes"] or "")
                if st.form_submit_button("Salvar alterações"):
                    if n.strip():
                        atualizar_obra(obra_id, n.strip(), c.strip(), l.strip(), o, obs.strip())
                        st.success("Dados atualizados.")
                        st.rerun()
                    else:
                        st.error("O nome da obra é obrigatório.")
    else:
        st.info("Nenhuma obra cadastrada ainda.")

elif pagina == "Dashboard":
    if not obra_id:
        st.warning("Cadastre uma obra primeiro na seção Obras.")
    else:
        obra = obter_obra(obra_id)
        resumo = resumo_obra(obra_id)
        st.subheader(obra["nome"])
        st.caption(f'Cliente: {obra["cliente"] or "Não informado"} · Local: {obra["local"] or "Não informado"}')
        total_orc = float(obra["orcamento_total"] or 0)
        comprometido = resumo["total_registrado"]
        pago = resumo["total_pago"]
        saldo = total_orc - comprometido
        percentual = (comprometido / total_orc * 100) if total_orc > 0 else 0
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Orçamento total", dinheiro(total_orc))
        c2.metric("Total registrado", dinheiro(comprometido))
        c3.metric("Total pago", dinheiro(pago))
        c4.metric("Saldo do orçamento", dinheiro(saldo), delta=dinheiro(saldo), delta_color="normal")
        st.progress(min(max(percentual / 100, 0.0), 1.0), text=f"{percentual:.1f}% do orçamento registrado".replace(".", ","))
        if saldo < 0:
            st.error(f"Atenção: os gastos registrados ultrapassaram o orçamento em {dinheiro(abs(saldo))}.")
        elif percentual >= 80:
            st.warning("Atenção: 80% ou mais do orçamento já está comprometido.")
        st.divider()
        a, b = st.columns(2)
        a.subheader("Gastos por categoria")
        por_cat = resumo["por_categoria"]
        if not por_cat.empty:
            a.bar_chart(por_cat.set_index("categoria")[["total"]])
        else:
            a.info("Ainda não há gastos registrados.")
        b.subheader("Status dos gastos")
        gastos = listar_gastos(obra_id)
        if gastos:
            df = pd.DataFrame(gastos)
            status_df = df.groupby("status", as_index=False)["valor"].sum().rename(columns={"status":"Status", "valor":"Valor"})
            b.dataframe(status_df, use_container_width=True, hide_index=True)
            extras = df[df["extraordinario"] == 1]["valor"].sum()
            st.metric("Gastos extraordinários registrados", dinheiro(extras))
        else:
            b.info("Os status aparecerão após o primeiro lançamento.")
        st.caption("Nota: 'Total registrado' considera gastos pagos, pendentes e parcelados. 'Total pago' considera somente os marcados como Pago.")

elif pagina == "Orçamento por categoria":
    if not obra_id:
        st.warning("Cadastre uma obra primeiro.")
    else:
        st.subheader("Orçamento planejado por categoria")
        st.write("Informe quanto foi reservado para cada categoria. Esses valores são um detalhamento do orçamento total da obra.")
        orcs = {x["categoria"]: float(x["valor_orcado"]) for x in listar_orcamentos(obra_id)}
        with st.form("form_orcamento"):
            valores = {}
            cols = st.columns(2)
            for i, cat in enumerate(CATEGORIAS):
                valores[cat] = cols[i % 2].number_input(f"{cat} (R$)", min_value=0.0,
                    value=orcs.get(cat, 0.0), step=100.0, key=f"orc_{obra_id}_{cat}")
            if st.form_submit_button("Salvar orçamento por categoria", type="primary"):
                for cat, valor in valores.items():
                    salvar_orcamento(obra_id, cat, valor)
                st.success("Orçamento por categoria salvo.")
                st.rerun()
        gastos = listar_gastos(obra_id)
        df_gastos = pd.DataFrame(gastos) if gastos else pd.DataFrame(columns=["categoria","valor"])
        gasto_cat = df_gastos.groupby("categoria")["valor"].sum().to_dict() if not df_gastos.empty else {}
        linhas = []
        for cat in CATEGORIAS:
            previsto = orcs.get(cat, 0.0)
            realizado = float(gasto_cat.get(cat, 0.0))
            linhas.append({"Categoria":cat, "Orçado":previsto, "Registrado":realizado, "Saldo":previsto-realizado})
        tabela = pd.DataFrame(linhas)
        st.dataframe(tabela.style.format({"Orçado": "R$ {:,.2f}", "Registrado": "R$ {:,.2f}", "Saldo": "R$ {:,.2f}"}),
                     use_container_width=True, hide_index=True)
        st.caption("Gastos extraordinários usam a categoria escolhida no lançamento e também são identificados separadamente.")

elif pagina == "Lançar gasto":
    if not obra_id:
        st.warning("Cadastre uma obra primeiro.")
    else:
        st.subheader("Registrar novo gasto")
        with st.form("form_gasto", clear_on_submit=True):
            descricao = st.text_input("Descrição do gasto*", placeholder="Ex.: Compra de cimento")
            c1, c2 = st.columns(2)
            data_gasto = c1.date_input("Data", value=date.today())
            categoria = c2.selectbox("Categoria", CATEGORIAS)
            c3, c4 = st.columns(2)
            valor = c3.number_input("Valor total (R$)*", min_value=0.01, value=100.0, step=10.0)
            status = c4.selectbox("Status", STATUS)
            fornecedor = st.text_input("Fornecedor / prestador")
            c5, c6 = st.columns(2)
            pagamento = c5.selectbox("Forma de pagamento", PAGAMENTOS)
            parcelas = c6.number_input("Número de parcelas", min_value=1, max_value=120, value=1, step=1)
            extraordinario = st.checkbox("Este gasto é extraordinário (não previsto no orçamento original)")
            justificativa = st.text_area("Justificativa / observações", placeholder="Obrigatória para gastos extraordinários")
            comprovante = st.text_input("Referência do comprovante (opcional)", placeholder="Nome do arquivo, número da nota etc.")
            salvar = st.form_submit_button("Salvar gasto", type="primary")
            if salvar:
                if not descricao.strip():
                    st.error("Informe a descrição do gasto.")
                elif extraordinario and not justificativa.strip():
                    st.error("Informe a justificativa para o gasto extraordinário.")
                else:
                    adicionar_gasto(obra_id, str(data_gasto), descricao.strip(), categoria, fornecedor.strip(),
                                    valor, status, pagamento, int(parcelas), int(extraordinario),
                                    justificativa.strip(), comprovante.strip())
                    st.success("Gasto registrado com sucesso.")
                    st.rerun()

elif pagina == "Consultar gastos":
    if not obra_id:
        st.warning("Cadastre uma obra primeiro.")
    else:
        st.subheader("Consultar e excluir gastos")
        gastos = listar_gastos(obra_id)
        if not gastos:
            st.info("Nenhum gasto registrado para esta obra.")
        else:
            df = pd.DataFrame(gastos)
            df["tipo"] = df["extraordinario"].map({0:"Normal", 1:"Extraordinário"})
            df_view = df.rename(columns={"id":"ID", "data":"Data", "descricao":"Descrição", "categoria":"Categoria",
                "fornecedor":"Fornecedor", "valor":"Valor (R$)", "status":"Status", "forma_pagamento":"Pagamento",
                "parcelas":"Parcelas", "tipo":"Tipo", "justificativa":"Justificativa", "comprovante":"Comprovante"})
            busca = st.text_input("Buscar por descrição, categoria ou fornecedor")
            if busca:
                mask = df_view.astype(str).apply(lambda col: col.str.contains(busca, case=False, na=False)).any(axis=1)
                df_view = df_view[mask]
            st.dataframe(df_view[["ID","Data","Descrição","Categoria","Fornecedor","Valor (R$)","Status","Pagamento","Parcelas","tipo","Justificativa","Comprovante"]],
                         use_container_width=True, hide_index=True)
            st.download_button("Baixar gastos em CSV", data=df_view.to_csv(index=False).encode("utf-8-sig"),
                               file_name="gastos_obra.csv", mime="text/csv")
            ids = [int(x) for x in df_view["ID"].tolist()]
            if ids:
                st.warning("Excluir um lançamento é permanente. Exporte os dados antes, se precisar guardar um registro.")
                alvo = st.selectbox("Selecione o ID do gasto para excluir", ids)
                confirmar = st.checkbox("Confirmo que desejo excluir este gasto")
                if st.button("Excluir gasto selecionado", disabled=not confirmar):
                    excluir_gasto(alvo)
                    st.success("Gasto excluído.")
                    st.rerun()

elif pagina == "Relatórios e exportação":
    if not obra_id:
        st.warning("Cadastre uma obra primeiro.")
    else:
        obra = obter_obra(obra_id)
        gastos = listar_gastos(obra_id)
        st.subheader(f'Relatórios — {obra["nome"]}')
        if not gastos:
            st.info("Registre gastos para gerar relatórios.")
        else:
            df = pd.DataFrame(gastos)
            df["Tipo"] = df["extraordinario"].map({0:"Normal",1:"Extraordinário"})
            df["Valor (R$)"] = df["valor"]
            st.metric("Total registrado", dinheiro(df["valor"].sum()))
            st.metric("Total extraordinário", dinheiro(df.loc[df["extraordinario"] == 1, "valor"].sum()))
            resumo_cat = df.groupby(["categoria","Tipo"], as_index=False)["valor"].sum()
            resumo_cat = resumo_cat.rename(columns={"categoria":"Categoria","valor":"Total (R$)"})
            st.markdown("#### Resumo por categoria e tipo")
            st.dataframe(resumo_cat, use_container_width=True, hide_index=True)
            st.download_button("Exportar todos os gastos em CSV", data=df.to_csv(index=False).encode("utf-8-sig"),
                               file_name="relatorio_gastos_obra.csv", mime="text/csv")
            st.download_button("Exportar todos os gastos em Excel", data=df_para_excel(df),
                               file_name="relatorio_gastos_obra.xlsx",
                               mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
