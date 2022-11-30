from typing import Dict, Any

import pandas as pd
import os
import openpyxl
from Tools.scripts.dutree import display

"""
/// TRATAMENTO DE DADOS ///
"""
# Criando dicionários com cada empresa

empresas = ["ABEV3", "AZUL4", "BTOW3", "B3SA3", "BBSE3", "BRML3", "BBDC4", "BRAP4", "BBAS3", "BRKM5", "BRFS3", "BPAC11", "CRFB3", "CCRO3", "CMIG4", "HGTX3", "CIEL3", "COGN3", "CPLE6", "CSAN3", "CPFE3", "CVCB3", "CYRE3", "ECOR3", "ELET6", "EMBR3", "ENBR3", "ENGI11", "ENEV3", "EGIE3", "EQTL3", "EZTC3", "FLRY3", "GGBR4", "GOAU4", "GOLL4", "NTCO3", "HAPV3", "HYPE3", "IGTA3", "GNDI3", "ITSA4", "ITUB4", "JBSS3", "JHSF3", "KLBN11", "RENT3", "LCAM3", "LAME4", "LREN3", "MGLU3", "MRFG3", "BEEF3", "MRVE3", "MULT3", "PCAR3", "PETR4", "BRDT3", "PRIO3", "QUAL3", "RADL3", "RAIL3", "SBSP3", "SANB11", "CSNA3", "SULA11", "SUZB3", "TAEE11", "VIVT3", "TIMS3", "TOTS3", "UGPA3", "USIM5", "VALE3", "VVAR3", "WEGE3", "YDUQ3"]
# fundamentos ={
    #  "ABEV": balanco_dre_abev3,
    # "MGLU3": balanco_dre_mglu3
# }
fundamentos = {}
arquivos = os.listdir("balancos")
for arquivo in arquivos:
    nome = arquivo[-9:-4]
    if "11" in nome:
        nome = arquivo[-10:-4]
        # pegar o balanço das empresas listadas
    if nome in empresas:
        print(nome)
        balanco = pd.read_excel(f'balancos/{arquivo}', sheet_name=0)
        # pegar o balanco daquela empresa
        balanco = pd.read_excel(f'balancos/{arquivo}', sheet_name=0)
        # na primeira coluna colocar o título com o nome da empresa
        balanco.iloc[0, 0] = nome
        # pegar 1ª linha e tornar um cabeçalho
        balanco.columns = balanco.iloc[0]
        balanco = balanco[1:]
        # tornar a 1ª coluna (que agora tem o nome da emrpesa)
        balanco = balanco.set_index(nome)
        dre = pd.read_excel(f'balancos/{arquivo}', sheet_name=1)
        # na primeira coluna colocar o título com o nome da empresa
        dre.iloc[0, 0] = nome
        # pegar 1ª linha e tornar um cabeçalho
        dre.columns = dre.iloc[0]
        dre = dre[1:]
        # tornar a 1ª coluna (que agora tem o nome da emrpesa)
        dre = dre.set_index(nome)
        fundamentos[nome] = balanco.append(dre)

# Pegar preços das ações nas datas correspondentes
cotacoes_df = pd.read_excel("Cotacoes.xlsx")
cotacoes: dict[Any, Any] = {}
for empresa in cotacoes_df["Empresa"].unique():
    cotacoes[empresa] = cotacoes_df.loc[cotacoes_df['Empresa']==empresa, :]


# Foram excluídos as empresas que possuiam cotações vazias
for empresa in empresas:
    if cotacoes[empresa].isnull().values.any():
        cotacoes.pop(empresa)
        fundamentos.pop(empresa)
empresas = list(cotacoes.keys())
print(len(empresas))

# Juntando fudamentos e preços das ações

"""
/// Ajustes necessários ///

- Nas cotações: jogar as datas para indice
- No fundamentos: 
    > Trocar linhas por colunas
    >  Tratar as datas para formato de data python
Por fim, juntas os fundamentos com a coluna Adj Close das cotações.
"""
for empresa in fundamentos:
    tabela = fundamentos[empresa].T
    tabela.index = pd.to_datetime(tabela.index, format="%d/%m/%Y")
    tabela_cotacao = cotacoes[empresa].set_index("Date")
    tabela_cotacao = tabela_cotacao[["Adj Close"]]
    tabela = tabela.merge(tabela_cotacao, right_index=True, left_index=True)
    tabela.index.name = empresa
    fundamentos[empresa] = tabela

# Remover a analise das tabelas que têm colunas diferentes
colunas = list(fundamentos["ABEV3"].columns)

for empresa in empresas:
    if set(colunas) != set(fundamentos[empresa].columns):
        fundamentos.pop(empresa)
print(len(fundamentos))

# Ajeitando coluna com o mesmo nome
texto_colunas = ";".join(colunas)

colunas_modificadas = []
for coluna in colunas:
    if colunas.count(coluna) == 2 and coluna not in colunas_modificadas:
        texto_colunas = texto_colunas.replace(";" + coluna + ";",";" + coluna + "_1;", 1)
        colunas_modificadas.append(coluna)
colunas = texto_colunas.split(';')
print(colunas)

# Para acresccentar as colunas nas tabelas
for empresa in fundamentos:
    fundamentos[empresa].columns = colunas

# Analisando valores vazios na coluna
# valores_vazios = {
#     "Ativo Total": 0,
#     "Passivo Total": 0,
# }
valores_vazios = dict.fromkeys(colunas, 0)
total_linhas = 0
for empresa in fundamentos:
    tabela = fundamentos[empresa]
    total_linhas += tabela.shape[0]
    for coluna in colunas:
        qtde_vazios = pd.isnull(tabela[coluna]).sum()
        valores_vazios[coluna] += qtde_vazios
print(valores_vazios)
print(total_linhas)

remover_colunas = []
for coluna in valores_vazios:
    if valores_vazios[coluna] > 50:
        remover_colunas.append(coluna)

for empresa in fundamentos:
    fundamentos[empresa] = fundamentos[empresa].drop(remover_colunas, axis=1)
    fundamentos[empresa] = fundamentos[empresa].ffill()
fundamentos["ABEV3"].shape

"""
/// Analise Exploratória /// 
"""
# Comprar, Não comprar ou Vender?
"""
Regra:
Subiu mais do que o Ibovespa (ou caiu menos) -> Comprar (valor = 3)
Subiu menos do que o Ibovespa até Ibovespa - 2% (Ou caiu mais do que o Ibovespa até -2%) -> Não comprar (Valor = 1)
Suviu menos do que o Ibovespa - 2% (ou caiu mas do que o Ibovespa -2%) -> Vender (Valor =0)

"""
data_inicial = "12/20/2012"
data_final = "04/20/2021"

from pandas_datareader import data as web
df_ibov = web.DataReader('^BVSP', data_source='yahoo', start=data_inicial, end=data_final)

import numpy as np

datas = fundamentos["ABEV3"].index
for data in datas:
    if data not in df_ibov.index:
        df_ibov.loc[data] = np.nan
df_ibov = df_ibov.sort_index()
df_ibov = df_ibov.ffill()
df_ibov = df_ibov.rename(columns={"Adj Close": "IBOV"})
for empresa in fundamentos:
    fundamentos[empresa] = fundamentos[empresa].merge(df_ibov[["IBOV"]], left_index=True, right_index=True)
display(fundamentos["ABEV3"])

# tornar os nossos indicadores em percentuais
# fundamento%tri = fundamento tr / fundamento tri anterior
# cotacao%tri = cotacao tri seguinte / cotacao tri
for empresa in fundamentos:
    fundamento = fundamentos[empresa]
    fundamento = fundamento.sort_index()
    for coluna in fundamento:
        if "Adj Close" in coluna or "IBOV" in coluna:
            pass
        else:
            # pegar a cotação anterior
            condicoes = [
                (fundamento[coluna].shift(1) > 0) & (fundamento[coluna] < 0),
                (fundamento[coluna].shift(1) < 0) & (fundamento[coluna] > 0),
                (fundamento[coluna].shift(1) < 0) & (fundamento[coluna] < 0),
                (fundamento[coluna].shift(1) == 0) & (fundamento[coluna] > 0),
                (fundamento[coluna].shift(1) == 0) & (fundamento[coluna] < 0),
                (fundamento[coluna].shift(1) < 0) & (fundamento[coluna] == 0),
            ]
            valores = [
                -1,
                1,
                (abs(fundamento[coluna].shift(1)) - abs(fundamento[coluna])) / abs(fundamento[coluna].shift(1)),
                1,
                -1,
                1,
            ]
            fundamento[coluna] = np.select(condicoes, valores,
                                           default=fundamento[coluna] / fundamento[coluna].shift(1) - 1)
    # pegar cotação seguinte
    fundamento["Adj Close"] = fundamento["Adj Close"].shift(-1) / fundamento["Adj Close"] - 1
    fundamento["IBOV"] = fundamento["IBOV"].shift(-1) / fundamento["IBOV"] - 1
    fundamento["Resultado"] = fundamento["Adj Close"] - fundamento["IBOV"]
    condicoes = [
        (fundamento["Resultado"] > 0),
        (fundamento["Resultado"] < 0) & (fundamento["Resultado"] >= -0.02),
        (fundamento["Resultado"] < -0.02)
    ]
    valores = [2, 1, 0]
    fundamento["Decisao"] = np.select(condicoes, valores)

    fundamentos[empresa] = fundamento
display(fundamentos["ABEV3"])

# remover valores vazios
colunas = list(fundamentos["ABEV3"].columns)
valores_vazios = dict.fromkeys(colunas, 0)
total_linhas = 0
for empresa in fundamentos:
    tabela = fundamentos[empresa]
    total_linhas += tabela.shape[0]
    for coluna in colunas:
        qtde_vazios = pd.isnull(tabela[coluna]).sum()
        valores_vazios[coluna] += qtde_vazios
print(valores_vazios)
print(total_linhas)

remover_colunas = []
for coluna in valores_vazios:
    if valores_vazios[coluna] > (total_linhas / 3):
        remover_colunas.append(coluna)

for empresa in fundamentos:
    fundamentos[empresa] = fundamentos[empresa].drop(remover_colunas, axis=1)
    fundamentos[empresa] = fundamentos[empresa].fillna(0)

for empresa in fundamentos:
    fundamentos[empresa] = fundamentos[empresa].drop(["Adj Close", "IBOV", "Resultado"], axis=1)
print(fundamentos["ABEV3"].shape)

# Tornar tudo um só
copia_fundamentos = fundamentos.copy()
base_dados = pd.DataFrame()
for empresa in copia_fundamentos:
    copia_fundamentos[empresa] = copia_fundamentos[empresa][1:-1]
    copia_fundamentos[empresa] = copia_fundamentos[empresa].reset_index(drop=True)
    base_dados = base_dados.append(copia_fundamentos[empresa])
display(base_dados)

"""
/// Analise Explotória ///

"""
# Quantidade de respostas em cada tipo de decisão

import plotly.express as px
import matplotlib.pyplot as plt
import seaborn as sns

display(base_dados['Decisao'].value_counts(normalize=True).map("{:.1%}".format))
fig = px.histogram(base_dados, x="Decisao", color="Decisao")
fig.show()

# vou tirar a categoria 1 e transformar em 0
base_dados.loc[base_dados["Decisao"]==1, "Decisao"] = 0
display(base_dados['Decisao'].value_counts(normalize=True).map("{:.1%}".format))
fig = px.histogram(base_dados, x="Decisao", color="Decisao")
fig.show()

correlacoes = base_dados.corr()

fig, ax = plt.subplots(figsize=(15, 10))
sns.heatmap(correlacoes, cmap="Wistia", ax=ax)
plt.show()
display(correlacoes)

# Remover colunas já explicadas pelo Ativo Total
correlacoes_encontradas = []
for coluna in correlacoes:
    for linha in correlacoes.index:
        if linha != coluna:
            valor = abs(correlacoes.loc[linha, coluna])
            if valor > 0.8 and (coluna, linha, valor) not in correlacoes_encontradas:
                correlacoes_encontradas.append((linha, coluna, valor))
                print(f"Correlação Encontrada: {linha} e {coluna}. Valor: {valor}")

remover = ['Ativo Circulante', 'Contas a Receber_1', 'Tributos a Recuperar', 'Passivo Total', 'Passivo Circulante', 'Patrimônio Líquido', 'Capital Social Realizado', 'Receita Líquida de Vendas e/ou Serviços', 'Resultado Bruto', 'Despesas Gerais e Administrativas']
base_dados = base_dados.drop(remover, axis=1)
print(base_dados.shape)

# treinar uma arvore de decisao e pegar as caracteristicas mais importantes dela

from sklearn.ensemble import ExtraTreesClassifier

modelo = ExtraTreesClassifier(random_state=1)
x = base_dados.drop("Decisao", axis=1)
y = base_dados["Decisao"]
modelo.fit(x, y)

caracteristicas_importantes = pd.DataFrame(modelo.feature_importances_, x.columns).sort_values(by=0, ascending=False)
display(caracteristicas_importantes)
top10 = list(caracteristicas_importantes.index)[:10]
print(top10)

from sklearn.preprocessing import StandardScaler


def ajustar_scaler(tabela_original):
    scaler = StandardScaler()
    tabela_auxiliar = tabela_original.drop("Decisao", axis=1)

    tabela_auxiliar = pd.DataFrame(scaler.fit_transform(tabela_auxiliar), tabela_auxiliar.index,
                                   tabela_auxiliar.columns)
    tabela_auxiliar["Decisao"] = tabela_original["Decisao"]
    return tabela_auxiliar


nova_base_dados = ajustar_scaler(base_dados)
top10.append("Decisao")

nova_base_dados = nova_base_dados[top10].reset_index(drop=True)
display(nova_base_dados)

# Separação dos dados em treino e teste
from sklearn.model_selection import train_test_split

x = nova_base_dados.drop("Decisao", axis=1)
y = nova_base_dados["Decisao"]

x_treino, x_teste, y_treino, y_teste = train_test_split(x, y, random_state=1)
from sklearn.dummy import DummyClassifier
from sklearn.metrics import classification_report, confusion_matrix

dummy = DummyClassifier(strategy="stratified", random_state=2)
dummy.fit(x_treino, y_treino)
previsao_dummy = dummy.predict(x_teste)

# Métricas de avaliação
def avaliar(y_teste, previsoes, nome_modelo):
    print(nome_modelo)
    report = classification_report(y_teste, previsoes)
    print(report)
    cf_matrix = pd.DataFrame(confusion_matrix(y_teste, previsoes), index=["Vender", "Comprar"],
                             columns=["Vender", "Comprar"])
    sns.heatmap(cf_matrix, annot=True, cmap="Blues", fmt=',')
    plt.show()
    print("#" * 50)


avaliar(y_teste, previsao_dummy, "Dummy")

# Testando modelos
from sklearn.ensemble import AdaBoostClassifier, GradientBoostingClassifier, RandomForestClassifier, ExtraTreesClassifier
from sklearn.tree import DecisionTreeClassifier
from sklearn.neighbors import KNeighborsClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.naive_bayes import GaussianNB
from sklearn.svm import SVC
from sklearn.neural_network import MLPClassifier

modelos = {
    "AdaBoost": AdaBoostClassifier(random_state=1),
    "DecisionTree": DecisionTreeClassifier(random_state=1),
    "RandomForest": RandomForestClassifier(random_state=1),
    "ExtraTree": ExtraTreesClassifier(random_state=1),
    "GradientBoost": GradientBoostingClassifier(random_state=1),
    "KNN": KNeighborsClassifier(),
    "LogisticRegression": LogisticRegression(random_state=1),
    "NaiveBayes": GaussianNB(),
    "SVM": SVC(random_state=1),
    "RedeNeural": MLPClassifier(random_state=1, max_iter=400),
}

for nome_modelo in modelos:
    modelo = modelos[nome_modelo]
    modelo.fit(x_treino, y_treino)
    previsoes = modelo.predict(x_teste)
    avaliar(y_teste, previsoes, nome_modelo)
    modelos[nome_modelo] = modelo

# Tunning do modelo
from sklearn.model_selection import GridSearchCV
from sklearn.metrics import make_scorer, precision_score

modelo_final = modelos["RandomForest"]

n_estimators = range(10, 251, 30)
max_features = list(range(2, 11, 2))
max_features.append('auto')
min_samples_split = range(2, 11, 2)

precision2_score = make_scorer(precision_score, labels=[2], average='macro')

grid = GridSearchCV(
        estimator=RandomForestClassifier(),
        param_grid={
            'n_estimators': n_estimators,
            'max_features': max_features,
            'min_samples_split': min_samples_split,
            'random_state': [1],
        },
        scoring=precision2_score,
)

resultado_grid = grid.fit(x_treino, y_treino)
print("Ajuste feito")

modelo_tunado = resultado_grid.best_estimator_
previsoes = modelo_tunado.predict(x_teste)
avaliar(y_teste, previsoes, "RandomForest Tunado")

# Modelo RandomForest
ult_tri_fundamentos = fundamentos.copy()
ult_tri_base_dados = pd.DataFrame()
lista_empresas = []
for empresa in ult_tri_fundamentos:
    ult_tri_fundamentos[empresa] = ult_tri_fundamentos[empresa][-1:]
    ult_tri_fundamentos[empresa] = ult_tri_fundamentos[empresa].reset_index(drop=True)
    ult_tri_base_dados = ult_tri_base_dados.append(ult_tri_fundamentos[empresa])
    lista_empresas.append(empresa)
display(ult_tri_base_dados)
print(lista_empresas)

ult_tri_base_dados = ult_tri_base_dados.reset_index(drop=True)
ult_tri_base_dados = ult_tri_base_dados[top10]
ult_tri_base_dados = ajustar_scaler(ult_tri_base_dados)
ult_tri_base_dados = ult_tri_base_dados.drop("Decisao", axis=1)
display(ult_tri_base_dados)

previsoes_ult_tri = modelo_tunado.predict(ult_tri_base_dados)
print(previsoes_ult_tri)

carteira = []
carteira_inicial = []

for i, empresa in enumerate(lista_empresas):
    if previsoes_ult_tri[i] == 2:
        print(empresa)
        carteira_inicial.append(1000)
        cotacao = cotacoes[empresa]
        cotacao = cotacao.set_index("Date")
        cotacao_inicial = cotacao.loc["2020-12-31", "Adj Close"]
        cotacao_final = cotacao.loc["2021-03-31", "Adj Close"]
        percentual = cotacao_final / cotacao_inicial
        carteira.append(1000 * percentual)

saldo_inicial = sum(carteira_inicial)
saldo_final = sum(carteira)
print(saldo_inicial, saldo_final)
print(saldo_final / saldo_inicial)

# Comparar prevosão de decisões com o IBOV
variacao_ibov = df_ibov.loc["2021-03-31", "IBOV"] / df_ibov.loc["2020-12-31", "IBOV"]
print(variacao_ibov)







