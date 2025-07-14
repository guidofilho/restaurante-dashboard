import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime

# Configuração da página
st.set_page_config(
    page_title="Dashboard Restaurante",
    page_icon="🍽️",
    layout="wide"
)

@st.cache_data
def carregar_dados():
    df = pd.read_csv("data/dados_ficticios.csv", parse_dates=["data"])
    
    # Processamento dos dados
    df["receita"] = df["quantidade"] * df["preco_unitario"]
    df["custo"] = df["quantidade"] * df["custo_unitario"]
    df["lucro"] = df["receita"] - df["custo"]
    df["margem_lucro"] = (df["lucro"] / df["receita"]) * 100
    
    # Converter dias para português
    dias_portugues = {
        'Monday': 'Segunda',
        'Tuesday': 'Terça',
        'Wednesday': 'Quarta',
        'Thursday': 'Quinta',
        'Friday': 'Sexta',
        'Saturday': 'Sábado',
        'Sunday': 'Domingo'
    }
    df["dia_semana"] = df["data"].dt.day_name().map(dias_portugues)
    df["mes"] = df["data"].dt.month_name()
    
    return df

# ========== PÁGINA PRINCIPAL ==========
def pagina_principal():
    st.title("📊 Dashboard Restaurante")
    
    def criar_filtros(df):
        st.sidebar.header("Filtros")
        
        # Filtro de data
        data_min = df["data"].min().date()
        data_max = df["data"].max().date()
        datas = st.sidebar.date_input(
            "Selecione o período",
            [data_min, data_max],
            min_value=data_min,
            max_value=data_max
        )
        
        # Filtro de categorias
        categorias = st.sidebar.multiselect(
            "Categorias",
            options=df["categoria"].unique(),
            default=df["categoria"].unique()
        )
        
        # Filtro de dias da semana
        dias = st.sidebar.multiselect(
            "Dias da semana",
            options=df["dia_semana"].unique(),
            default=df["dia_semana"].unique()
        )
        
        return datas, categorias, dias

    def filtrar_dados(df, datas, categorias, dias):
        df_filtrado = df[
            (df["data"].dt.date >= datas[0]) & 
            (df["data"].dt.date <= datas[1])
        ]
        
        if categorias:
            df_filtrado = df_filtrado[df_filtrado["categoria"].isin(categorias)]
        
        if dias:
            df_filtrado = df_filtrado[df_filtrado["dia_semana"].isin(dias)]
        
        return df_filtrado

    def mostrar_metricas(df):
        receita_total = df["receita"].sum()
        lucro_total = df["lucro"].sum()
        margem_media = (lucro_total / receita_total) * 100 if receita_total > 0 else 0
        
        col1, col2, col3 = st.columns(3)
        col1.metric("Receita Total", f"R$ {receita_total:,.2f}")
        col2.metric("Lucro Total", f"R$ {lucro_total:,.2f}")
        col3.metric("Margem Média", f"{margem_media:.1f}%")

    def criar_graficos(df):
        # Gráfico de Receita Diária
        fig_receita = px.line(
            df.groupby("data")["receita"].sum().reset_index(),
            x="data",
            y="receita",
            title="Receita Diária"
        )
        
        # Gráfico de Lucro por Categoria
        fig_lucro_cat = px.bar(
            df.groupby("categoria")["lucro"].sum().reset_index().sort_values("lucro", ascending=False),
            x="categoria",
            y="lucro",
            title="Lucro por Categoria"
        )
        
        # Exibir gráficos
        st.plotly_chart(fig_receita, use_container_width=True)
        st.plotly_chart(fig_lucro_cat, use_container_width=True)

    df = carregar_dados()
    datas, categorias, dias = criar_filtros(df)
    df_filtrado = filtrar_dados(df, datas, categorias, dias)
    
    mostrar_metricas(df_filtrado)
    criar_graficos(df_filtrado)
    
    # Mostrar dados brutos
    if st.checkbox("Mostrar dados brutos"):
        st.dataframe(df_filtrado)

# ========== ANÁLISE DETALHADA ==========
def analise_detalhada():
    st.title("🔍 Análise Detalhada")
    
    def mostrar_filtros_avancados(df):
        col1, col2, col3 = st.columns(3)
        with col1:
            data_inicio = st.date_input(
                "Data inicial",
                value=df["data"].min(),
                min_value=df["data"].min(),
                max_value=df["data"].max()
            )
        with col2:
            data_fim = st.date_input(
                "Data final",
                value=df["data"].max(),
                min_value=df["data"].min(),
                max_value=df["data"].max()
            )
        with col3:
            limite_lucro = st.slider(
                "Filtrar por lucro mínimo (R$)",
                min_value=0,
                max_value=int(df["lucro"].max()),
                value=0
            )
        return data_inicio, data_fim, limite_lucro

    def analise_produtos(df_filtrado):
        st.header("📈 Análise por Produto")
        
        tab1, tab2, tab3 = st.tabs(["Top Performers", "Piores Performers", "Margens"])
        
        with tab1:
            top_produtos = df_filtrado.groupby("produto")["lucro"].sum().nlargest(5)
            st.plotly_chart(
                px.bar(top_produtos, title="Top 5 Produtos (Lucro Total)")
            )
        
        with tab2:
            piores_produtos = df_filtrado.groupby("produto")["margem_lucro"].mean().nsmallest(5)
            st.plotly_chart(
                px.bar(piores_produtos, title="Produtos com Menor Margem (%)")
            )
        
        with tab3:
            st.plotly_chart(
                px.scatter(
                    df_filtrado,
                    x="preco_unitario",
                    y="custo_unitario",
                    color="produto",
                    size="quantidade",
                    title="Relação Preço vs Custo"
                )
            )

    def analise_temporal(df_filtrado):
        st.header("⏳ Análise Temporal")
        
        df_temporal = df_filtrado.groupby([pd.Grouper(key="data", freq="W"), "dia_semana"])["lucro"].sum().reset_index()
        
        col1, col2 = st.columns(2)
        with col1:
            st.plotly_chart(
                px.line(
                    df_temporal,
                    x="data",
                    y="lucro",
                    color="dia_semana",
                    title="Lucro Semanal por Dia"
                )
            )
        with col2:
            st.plotly_chart(
                px.box(
                    df_filtrado,
                    x="dia_semana",
                    y="lucro",
                    title="Distribuição de Lucro por Dia"
                )
            )

    def recomendar_acoes(df_filtrado):
        st.header("🚀 Recomendações Estratégicas")
        
        # Análise para recomendações
        margem_media = df_filtrado["margem_lucro"].mean()
        produto_alvo = df_filtrado.groupby("produto")["margem_lucro"].mean().idxmax()
        dia_fraco = df_filtrado.groupby("dia_semana")["lucro"].mean().idxmin()
        
        with st.expander("Ver insights"):
            st.write(f"**Margem média atual:** {margem_media:.1f}%")
            st.write(f"**Produto mais rentável:** {produto_alvo}")
            st.write(f"**Dia com menor performance:** {dia_fraco}")
            
            st.markdown(f"""
            ### Ações sugeridas:
            - 📢 Promover **{produto_alvo}** no cardápio
            - 🎯 Criar promoções nas **{dia_fraco}s**
            - 🔍 Revisar custos dos produtos com margem < 15%
            """)

    df = carregar_dados()
    data_inicio, data_fim, limite_lucro = mostrar_filtros_avancados(df)
    
    # Aplicar filtros
    df_filtrado = df[
        (df["data"].dt.date >= data_inicio) & 
        (df["data"].dt.date <= data_fim) &
        (df["lucro"] >= limite_lucro)
    ]
    
    analise_produtos(df_filtrado)
    analise_temporal(df_filtrado)
    recomendar_acoes(df_filtrado)
    
    # Exportar dados
    if st.button("📤 Exportar dados filtrados"):
        st.download_button(
            label="Baixar como CSV",
            data=df_filtrado.to_csv(index=False).encode("utf-8"),
            file_name=f"analise_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv"
        )

# ========== MENU DE NAVEGAÇÃO ==========
def main():
    st.sidebar.title("Navegação")
    pagina = st.sidebar.radio(
        "Selecione a página:",
        ["Dashboard Principal", "Análise Detalhada"]
    )
    
    if pagina == "Dashboard Principal":
        pagina_principal()
    elif pagina == "Análise Detalhada":
        analise_detalhada()

if __name__ == "__main__":
    main()