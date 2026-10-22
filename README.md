# Gerenciador Financeiro de Obras

Aplicação local em Python para acompanhar orçamento, gastos normais e extraordinários por obra.

## Recursos
- Cadastro de várias obras
- Orçamento total e orçamento planejado por categoria
- Lançamento de despesas com data, fornecedor, categoria, forma de pagamento e status
- Identificação de gastos extraordinários com justificativa obrigatória
- Dashboard com orçamento, total registrado, total pago e saldo
- Consulta, busca e exclusão de lançamentos
- Exportação CSV e Excel
- Banco de dados SQLite criado automaticamente

## Requisitos
- Python 3.10 ou superior recomendado
- Internet apenas para instalar as bibliotecas na primeira execução

## Instalação no Windows
1. Extraia o ZIP em uma pasta, por exemplo `C:\GerenciadorObra`.
2. Abra essa pasta no Explorador de Arquivos.
3. Clique na barra de endereço, digite `cmd` e pressione Enter.
4. Execute:

```bat
py -m venv .venv
.venv\Scripts\activate
py -m pip install -r requirements.txt
py -m streamlit run app.py
```

Se o comando `py` não funcionar, tente trocar `py` por `python`.

O navegador abrirá o sistema. Se não abrir, copie o endereço local mostrado no terminal, geralmente `http://localhost:8501`.

## Uso
1. Entre em **Obras** e cadastre a obra com o orçamento total.
2. Em **Orçamento por categoria**, distribua o orçamento planejado entre as categorias.
3. Em **Lançar gasto**, registre despesas. Para uma despesa fora do orçamento original, marque **gasto extraordinário** e preencha a justificativa.
4. Acompanhe o resumo em **Dashboard**.
5. Use **Consultar gastos** para pesquisar e excluir lançamentos.
6. Em **Relatórios e exportação**, baixe CSV ou Excel.

## Regras importantes
- O total registrado inclui gastos pagos, pendentes e parcelados, pois todos comprometem o orçamento informado.
- O total pago inclui somente os gastos com status `Pago`.
- O campo parcelas registra o número de parcelas, mas esta versão não gera automaticamente vencimentos mensais ou calcula parcelas individuais.
- O orçamento por categoria é um detalhamento do orçamento total e não é somado novamente ao total da obra.
- O banco fica em `database/obra.db`. Faça cópias de segurança desse arquivo regularmente.
- Esta versão é local e não tem login, sincronização entre computadores ou armazenamento em nuvem.
