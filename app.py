import streamlit as st 
import pandas as pd 
import matplotlib.pyplot as plt 
import seaborn as sns 
from streamlit_option_menu import option_menu
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(layout="wide")

# <importação dos dados>

@st.cache_data
def get_data(): 
    
    customers_df = pd.read_csv("./data/raw/olist_customers_dataset.csv")
    geo_df = pd.read_csv("./data/raw/olist_geolocation_dataset.csv")
    orderitem_df = pd.read_csv("./data/raw/olist_order_items_dataset.csv")
    orderpay_df = pd.read_csv("./data/raw/olist_order_payments_dataset.csv")
    orderreviews_df = pd.read_csv("./data/raw/olist_order_reviews_dataset.csv")
    orders_df = pd.read_csv("./data/raw/olist_orders_dataset.csv")
    products_df = pd.read_csv("./data/raw/olist_products_dataset.csv")
    sellers_df = pd.read_csv("./data/raw/olist_sellers_dataset.csv")
    categname_df = pd.read_csv("./data/raw/product_category_name_translation.csv")
    
    customers_df = customers_df.rename(columns={"customer_zip_code_prefix": "zip_code"})
    geo_df = geo_df.rename(columns={"geolocation_zip_code_prefix": "zip_code"}) 
    
    data = orders_df.merge(customers_df, on="customer_id").merge(orderitem_df, on="order_id").merge(products_df, on="product_id").merge(categname_df, on="product_category_name").merge(orderpay_df, on="order_id").merge(sellers_df, on="seller_id").merge(orderreviews_df, on="order_id")
    
    datesCols = ["order_purchase_timestamp", "order_approved_at", "order_delivered_carrier_date", 
            "order_delivered_customer_date", "order_estimated_delivery_date", "shipping_limit_date", 
            "review_creation_date", "review_answer_timestamp"]

    for col in datesCols:
        data[col] = pd.to_datetime(data[col])
        
    data["TimeToDeliveryinHours"] = (data["order_delivered_customer_date"] - data["order_purchase_timestamp"])
    data["TimeToDeliveryinHours"] = data["TimeToDeliveryinHours"].apply(lambda x: x.total_seconds())
    data["TimeToDeliveryinHours"] = round((data["TimeToDeliveryinHours"] / 3600) / 24, 2)
    data.rename(columns={"TimeToDeliveryinHours" : "TimeToDeliveryinDays"}, inplace=True)
    
    
    return data


data = get_data()

@st.cache_data
def get_top_customers():
    top_customers = data.groupby("customer_unique_id")["payment_value"].sum().reset_index().sort_values("payment_value", ascending=False)
    top_customers.rename(columns={"payment_value":"total_paid"}, inplace=True)
    top_customers["% of Total Sales"] = (top_customers["total_paid"] / top_customers["total_paid"].sum()) * 100
    top_customers['Cum % of Total Sales'] = top_customers['% of Total Sales'].cumsum()

    return top_customers

@st.cache_data
def get_top_ordersbyvalue_cities():
    top_ordersbyvalue_cities = data.groupby("customer_city")["payment_value"].sum().reset_index().sort_values("payment_value", ascending=False)
    top_ordersbyvalue_cities["% of Total Payments"] = (top_ordersbyvalue_cities["payment_value"] / top_ordersbyvalue_cities["payment_value"].sum()) * 100
    top_ordersbyvalue_cities["Cum % of Total Payments"] = top_ordersbyvalue_cities["% of Total Payments"].cumsum() 
    
    return top_ordersbyvalue_cities

@st.cache_data
def get_orderbyhour():
    orders_df = pd.read_csv("./data/raw/olist_orders_dataset.csv")
    orders_df["order_purchase_timestamp"] = pd.to_datetime(orders_df["order_purchase_timestamp"])
    orderbyhour = orders_df.groupby(orders_df["order_purchase_timestamp"].dt.hour)["order_id"].count().reset_index().sort_values(by="order_purchase_timestamp", ascending=False)
    orderbyhour.rename(columns={"order_id":"Total Orders", "order_purchase_timestamp": "Hour of Day"}, inplace=True)

    return orderbyhour

@st.cache_data
def get_orderbydow():
    orderbydow = data.groupby(data["order_purchase_timestamp"].dt.day_name())["order_id"].count().reset_index()
    orderbydow.rename(columns={"order_id":"Total Orders", "order_purchase_timestamp": "Weekday Name"}, inplace=True)
    orderbydow = orderbydow.sort_values(by="Total Orders", ascending=False)
    
    return orderbydow


@st.cache_data
def get_reviewscores():
    reviewsocres = data.groupby("product_category_name")["review_score"].agg(["mean", "count"]).sort_values(by="mean",ascending=False)
    return reviewsocres


reviewsocres = get_reviewscores()

@st.cache_data
def get_bestrated():
    bestrated = reviewsocres[reviewsocres["count"]>=30][:10]
    return bestrated

bestrated = get_bestrated()

@st.cache_data
def get_cashvscancel():
    cashvscancel = pd.crosstab(data["payment_type"], data["order_status"])
    cashvscancel = cashvscancel[["canceled", "delivered"]]
    cashvscancel["% Canceled"] = (cashvscancel["canceled"] / cashvscancel["delivered"] ) * 100
    return cashvscancel

@st.cache_data
def get_highestTTDstates():
    highestTTDstates = data.groupby("customer_state")["TimeToDeliveryinDays"].mean().dropna().sort_values(ascending=False).reset_index()
    highestTTDstates = highestTTDstates[:10]
    return highestTTDstates


@st.cache_data
def get_lowestTTDstates():
    lowestTTDstates = data.groupby("customer_state")["TimeToDeliveryinDays"].mean().dropna().sort_values(ascending=True).reset_index()
    lowestTTDstates = lowestTTDstates[:10]
    return lowestTTDstates
    


top_customers = get_top_customers()
top_ordersbyvalue_cities = get_top_ordersbyvalue_cities()
orderbyhour = get_orderbyhour()
orderbydow = get_orderbydow()
cashvscancel = get_cashvscancel()
highestTTDstates = get_highestTTDstates()
lowestTTDstates = get_lowestTTDstates()


# </ importação dos dados>


# <main>

with st.sidebar:
    selected = option_menu('EDA',
                           ['Home',
                            'Qtde. de clientes que geram 80% da receita',
                            'Clientes que mais gastam',
                            'Estados que mais tem números de pedido',
                            'Cidades com maior geração de receita',
                            'Qtde. de cidades que geram 80% da receita',
                            'Frequência de pedidos no dia',
                            'Frequência de pedidos na semana','Como os produtos são avaliados',
                            'Método de pagamento x Cancelamento',
                            'Estados x Tempo de entrega'],
                           icons = ['activity'],
                           default_index=0)



if selected == 'Home':
    
    st.title('Visualização de dados da loja Olist')
    
    st.write('Olist é uma plataforma de comércio eletrônico brasileira que conecta pequenas empresas a canais de vendas online, permitindo que vendam seus produtos em vários marketplaces do Brasil. A empresa também oferece serviços de logística e gerenciamento de pedidos para seus clientes.')
    
    st.info('Há apenas parte dos insights aqui.')
    
    st.text('Para ver todos os insights retirados acesse o link abaixo:')
    
    link = '[Notebook](https://nbviewer.org/github/math3usvalenca/olist-data-analysis/blob/main/Projeto_Ana%CC%81lise_Explorato%CC%81ria_de_Dados_da_loja_Olist.ipynb)'
    st.markdown(link, unsafe_allow_html=True)

    col1, col2 = st.columns(2)

    with col1:
        st.subheader('Números de parcelas mais recorrentes')
        sns.set(style='darkgrid')
        fig, ax = plt.subplots(figsize=(10, 6))
        sns.countplot(x='payment_installments',data=data,palette='Set1')
        ax.set(ylabel='quantidade',title='Números de parcelas mais presentes')
        st.write(fig)

    with col1:
        st.info('A maioria das vendas são parceladas uma única vez.')
        
    with col2:
        st.subheader('Quais as categorias mais vendidas?')
        fig, ax = plt.subplots()

        ax = sns.countplot(y="product_category_name", data=data, palette="Set2", order=data['product_category_name'].value_counts().index[0:10])
        ax.set(xlabel='quantidade',
        ylabel='categorias',
        title='Top 10 categorias mais vendidas')

        st.write(fig)
        st.info('A cateogoria mais vendida é cama, mesa e banho.')
        
        
        
    st.subheader('Como estão distribuídas as avaliações/notas?')
        
    percentage = data["review_score"].value_counts(normalize=True) * 100

    fig = px.bar(percentage, x=percentage.index, y=percentage.values, text=percentage.values, width=900, color=percentage.index, 
                labels={"index":"Nota","y": "Porcentagem"})
    fig.update_traces(texttemplate='%{text:.2f}%', textposition='outside')
    fig.update_layout(title="Percentual de notas")
    st.write(fig)


    st.info('Mais de 75% dos clientes deram uma pontuação igual ou maior que 4.')
    st.info('12,5% deram uma pontuação de 1 e cerca de 12% deram uma pontuação de 3 ou 2.')



elif selected == 'Qtde. de clientes que geram 80% da receita':
    

    st.subheader('Proporção de clientes gerando a maior parte da receita.')

    st.text('Queremos saber qual a quantidade de clientes que representa 80% dos valores das vendas.')
    
    # criar um gráfico de linhas do Plotly
    fig = px.line(top_customers, x=range(1, len(top_customers) + 1), y="Cum % of Total Sales", width=900)

    # definir as etiquetas do eixo x e y e o título do gráfico
    fig.update_layout(
        xaxis_title="Número de Clientes",
        yaxis_title="Total Vendas Cumulativo %",
        title="Contribuição % para as vendas por número de clientes"
    )

    # adicionar uma linha de preenchimento abaixo do gráfico
    fig.add_shape(
        type="rect",
        xref="x",
        yref="paper",
        x0=0,
        y0=0,
        x1=40000,
        y1=1,
        fillcolor="green",
        opacity=0.2,
        layer="below"
    )

    # atualizar o layout da forma para ajustar a altura do preenchimento
    fig.update_shapes(dict(xref='x', yref='paper'))

    # adicionar um texto explicativo na figura
    fig.add_annotation(
        x=55000,
        y=75,
        text="40 mil clientes (+-42% do total)<br> representam 80% das vendas",
        font=dict(
            size=14,
            color="white"
        ),
        showarrow=False,
    )


    st.write(fig)


elif selected == 'Clientes que mais gastam':
    
    st.subheader('Quem são os clientes que mais gastam?')

    top_customers.rename(columns={"payment_value" : "total_paid"}, inplace=True)

    # criar um gráfico de barras do Plotly
    fig = px.bar(top_customers[:10], x="total_paid", y="customer_unique_id", orientation="h", color="total_paid", width=900)

    # atualizar as configurações de layout do gráfico
    fig.update_layout(
        title="Top 10 Clientes por Valor Total Pago",
        xaxis_title="Valor Total Pago",
        yaxis_title="ID do Cliente"
    )

    st.write(fig)


elif selected == 'Estados que mais tem números de pedido':

    st.subheader('Vamos verificar quais são os estados que mais tem números de pedido')

    top_orders_cities = data.groupby("customer_state")["order_id"].count().reset_index().sort_values("order_id", ascending=False)

    # renomear a coluna "order_id" para "count"
    top_orders_cities.rename(columns={"order_id":"count"}, inplace=True)

    # criar um gráfico de barras do Plotly
    fig = px.bar(top_orders_cities[:10], x="count", y="customer_state", orientation="h", color="customer_state", width=900)

    # atualizar as configurações de layout do gráfico
    fig.update_layout(
        title="TOP 10 Estados por Número de Pedidos",
        xaxis_title="Número de Pedidos",
        yaxis_title="Estado"
    )

    st.write(fig)


elif selected == 'Cidades com maior geração de receita':

    st.subheader('Cidades com maior geração de receita')

    fig = px.bar(top_ordersbyvalue_cities[:10], x="% of Total Payments", y="customer_city", orientation="h", color="customer_city",width=900)

    # atualizar as configurações de layout do gráfico
    fig.update_layout(
        title="TOP 10 Cidades por Geração de Receita",
        xaxis_title="Porcentagem do Total de Pagamentos",
        yaxis_title="Cidade do Cliente"
    )

    st.write(fig)

    st.info('São paulo corresponde a 14% das receitas entre as cidades')
    st.info('Rio de janeiro corresponde a quase 8% das receitas entre as cidades')


elif selected == 'Qtde. de cidades que geram 80% da receita':
    
    st.subheader('Quantidade de cidades que geram 80% da receita')

    fig = px.line(top_ordersbyvalue_cities, x=range(1, len(top_ordersbyvalue_cities)+1), y="Cum % of Total Payments",width=900)

    # atualizar as configurações de layout do gráfico
    fig.update_layout(
        title="% de Contribuição das Vendas por Número de Cidades",
        xaxis_title="Número de Cidades",
        yaxis_title="% de Contribuição para as Vendas"
    )

    # preencher a área abaixo da curva
    fig.add_shape(
        type="rect",
        xref="x",
        yref="y",
        x0=0,
        y0=0,
        x1=358,
        y1=top_ordersbyvalue_cities["Cum % of Total Payments"][357],
        fillcolor="green",
        opacity=0.3,
        layer="below",
        line_width=0
    )

    # adicionar um texto ao gráfico
    fig.add_annotation(
        x=1000,
        y=70,
        text="358 cidades (+-8,7% do total) <br>contribuem para 80% das vendas.",
        font=dict(
            size=14,
            color="white"
        ),
        showarrow=False
    )

    st.write(fig)
    

elif selected == 'Frequência de pedidos no dia':
    

    st.subheader('Como se dá a frequência de pedidos ao longo do dia?')

    fig = px.bar(orderbyhour, x='Hour of Day', y='Total Orders', title='Número de pedidos por hora do dia', color='Total Orders', width=800)
    fig.update_xaxes(title='Hora do dia')
    fig.update_yaxes(title='Número total de pedidos')
    st.write(fig)

    st.info('Os pedidos começam a aumentar por volta das 6h da manhã e atingem o pico às 4h da tarde.')
   
elif selected == 'Frequência de pedidos na semana':  

    st.subheader('Como se dá a frequência de pedidos durante a semana?')
    fig = px.bar(orderbydow, x='Weekday Name', y='Total Orders', title='Número de pedidos por dia da semana',width=800)
    fig.update_xaxes(title='Dia da semana')
    fig.update_yaxes(title='Número total de pedidos')
    st.write(fig)
    st.info('Os pedidos atingem o pico no início da semana (segunda e terça-feira) e começam a declinar um pouco depois. Durante o final de semana, observa-se uma diminuição acentuada dos pedidos.')

elif selected == 'Como os produtos são avaliados':
    
    st.subheader('Produtos mais bem avaliados')
    
    fig = go.Figure(go.Bar(
            x=bestrated['mean'], # jogando a média no x
            y=bestrated.index, # jogando os nomes das categorias no y
            orientation='h',text=bestrated['mean'].values))

    fig.update_layout(
    title='Produtos com as melhores avaliações',
    xaxis_title='Avaliação média',
    yaxis_title='Categoria do produto',
    height=600,
    width=800,
    margin=dict(l=100, r=20, t=50, b=50),
    )
    
    fig.update_traces(texttemplate='%{text:.2f}')
    
    st.write(fig)
    
    worstrated = reviewsocres[reviewsocres["count"]>=30].sort_values(by='mean')[:10]

    st.subheader('Produtos com piores avaliações')

    fig = go.Figure(go.Bar(
            x=worstrated['mean'],
            y=worstrated.index,
            orientation='h',text=worstrated['mean'].values))

    fig.update_layout(
    title='Produtos com as piores avaliações',
    xaxis_title='Avaliação média',
    yaxis_title='Categoria do produto',
    height=600,
    width=800,
    margin=dict(l=100, r=20, t=50, b=50),
    )
    
    fig.update_traces(texttemplate='%{text:.2f}')

    st.write(fig)
    
elif selected == 'Método de pagamento x Cancelamento':
    
    st.subheader('O método de pagamento afeta o status do pedido?')
    
    fig = px.bar(cashvscancel.reset_index(), x="payment_type", y='% Canceled', color="payment_type", text=cashvscancel['% Canceled'].values,
           labels={"% Canceled": "Percentagem"} )

    
    fig.update_traces(texttemplate='%{text:.2f}%', textposition='outside')
    fig.update_layout(title="Percentual de cancelamento para cada tipo de pedido")
    st.write(fig)
    
    st.info('Podemos ver que a taxa de cancelamento é praticamente a mesma em todos os métodos de pagamento. Mas notamos uma leve desvio acima da média para o cartão de crédito.')
    

else:
      
    st.subheader('Estados com pior tempo de entrega')
    
    fig = px.bar(highestTTDstates, x='TimeToDeliveryinDays', y='customer_state',
                orientation='h', title='Top 10 estados com o maior tempo médio de entrega', color='customer_state',text='TimeToDeliveryinDays')

    fig.update_traces(texttemplate='%{text:.2f}',textfont_size=14)
    
    fig.update_yaxes(title='Estado')
    fig.update_xaxes(title='Tempo médio de entrega (dias)')
    st.write(fig)
    
    st.subheader('Estados com melhor tempo de entrega')
    
    fig = px.bar(lowestTTDstates, x='TimeToDeliveryinDays', y='customer_state',
             orientation='h', title='Top 10 estados com o menor tempo médio de entrega',color='customer_state',text='TimeToDeliveryinDays')

    fig.update_traces(texttemplate='%{text:.2f}',textfont_size=14)
    
    fig.update_yaxes(title='Estado')
    fig.update_xaxes(title='Tempo médio de entrega (dias)')
    st.write(fig)

# </main>