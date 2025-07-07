from flask import Flask, render_template, request, redirect, url_for
from flask_login import login_user, logout_user, login_required, current_user
from dash import Dash, dcc, html, Input, Output
import dash_bootstrap_components as dbc
import plotly.express as px
import pandas as pd
import datetime # Importado para lidar com objetos de data
from auth import User, validate_login, configure_login # Assumindo que auth.py está configurado corretamente

# Flask app
server = Flask(__name__)
server.secret_key = "segredo-super-seguro"
configure_login(server)

# Dash app com Bootstrap
app = Dash(
    __name__,
    server=server,
    url_base_pathname="/dashboard/",
    external_stylesheets=[dbc.themes.FLATLY],
    suppress_callback_exceptions=True # Manter para desenvolvimento, mas cuidado em produção
)

# Carregar dados
df = pd.read_csv("dados_restaurante.csv", parse_dates=['DataHora'])
# Garante que 'Data' seja um objeto datetime.date para comparação consistente
df['Data'] = df['DataHora'].dt.date
df['Hora'] = df['DataHora'].dt.hour
# df['Dia'] foi removido pois era redundante com df['Data']

# Layout
app.layout = dbc.Container([
    dbc.NavbarSimple(
        brand="Dashboard Restaurante",
        brand_href="#",
        color="primary",
        dark=True,
        children=[
            dbc.NavItem(dbc.NavLink("Logout", href="/logout"))
        ]
    ),

    dbc.Row([
        dbc.Col([
            html.Label("📅 Intervalo de datas:"),
            dcc.DatePickerRange(
                id='filtro-data',
                # min_date_allowed e max_date_allowed já são objetos datetime.date
                min_date_allowed=df['Data'].min(),
                max_date_allowed=df['Data'].max(),
                start_date=df['Data'].min(),
                end_date=df['Data'].max()
            )
        ], width=6),

        dbc.Col([
            html.Label("🍽️ Categoria:"),
            dcc.Dropdown(
                id='filtro-categoria',
                options=[{'label': cat, 'value': cat} for cat in df['Categoria'].unique()] + [{'label': 'Todas', 'value': 'Todas'}],
                value='Todas',
                clearable=False
            )
        ], width=6)
    ], className="my-3"),

    dbc.Row(id='kpis', className="mb-4"),

    dbc.Row([
        dbc.Col(dcc.Graph(id='faturamento-diario'), width=6),
        dbc.Col(dcc.Graph(id='pedidos-categoria'), width=6)
    ]),
    dbc.Row([
        dbc.Col(dcc.Graph(id='ticket-categoria'), width=6),
        dbc.Col(dcc.Graph(id='heatmap-horario'), width=6)
    ]),
    dbc.Row([
        dbc.Col(dcc.Graph(id='ranking-pratos'), width=12)
    ])
], fluid=True)

# Callback para atualizar o dashboard
@app.callback(
    Output('kpis', 'children'),
    Output('faturamento-diario', 'figure'),
    Output('pedidos-categoria', 'figure'),
    Output('ticket-categoria', 'figure'),
    Output('heatmap-horario', 'figure'),
    Output('ranking-pratos', 'figure'),
    Input('filtro-data', 'start_date'),
    Input('filtro-data', 'end_date'),
    Input('filtro-categoria', 'value')
)
def atualizar_dashboard(start_date, end_date, categoria):
    # Converte as strings de data do DatePickerRange para objetos datetime.date
    # para garantir uma comparação correta com df['Data']
    start_date_obj = datetime.datetime.strptime(start_date, '%Y-%m-%d').date()
    end_date_obj = datetime.datetime.strptime(end_date, '%Y-%m-%d').date()

    df_filtrado = df[(df['Data'] >= start_date_obj) & (df['Data'] <= end_date_obj)]
    if categoria != 'Todas':
        df_filtrado = df_filtrado[df_filtrado['Categoria'] == categoria]

    # Cálculo dos KPIs
    kpis = [
        dbc.Col(dbc.Card([
            dbc.CardHeader("Faturamento Total"),
            dbc.CardBody(f"R$ {df_filtrado['Valor'].sum():,.2f}")
        ], color="success", inverse=True), width=2),

        dbc.Col(dbc.Card([
            dbc.CardHeader("Pedidos Totais"),
            dbc.CardBody(f"{df_filtrado.shape[0]}")
        ], color="info", inverse=True), width=2),

        dbc.Col(dbc.Card([
            dbc.CardHeader("Ticket Médio"),
            dbc.CardBody(f"R$ {df_filtrado['Valor'].mean():.2f}")
        ], color="primary", inverse=True), width=2),

        dbc.Col(dbc.Card([
            dbc.CardHeader("Tempo Médio de Preparo"),
            dbc.CardBody(f"{df_filtrado['Tempo_Preparo'].mean():.1f} min")
        ], color="warning", inverse=True), width=3),

        dbc.Col(dbc.Card([
            dbc.CardHeader("Avaliação Média"),
            dbc.CardBody(f"{df_filtrado['Avaliacao'].mean():.2f} ⭐")
        ], color="dark", inverse=True), width=3),
    ]

    # Geração dos gráficos
    # Usando df['Data'] para o eixo X, que já é datetime.date
    fig_faturamento = px.line(df_filtrado.groupby('Data')['Valor'].sum().reset_index(), x='Data', y='Valor', title='Faturamento Diário')
    fig_pedidos = px.histogram(df_filtrado, x='Categoria', title='Pedidos por Categoria')
    fig_ticket = px.box(df_filtrado, x='Categoria', y='Valor', title='Distribuição do Ticket por Categoria')

    heatmap_data = df_filtrado.groupby(['Hora', 'Data']).size().reset_index(name='Pedidos')
    fig_heatmap = px.density_heatmap(
        heatmap_data, x='Data', y='Hora', z='Pedidos', nbinsx=30, nbinsy=12,
        color_continuous_scale='Viridis', title='⏰ Volume de Pedidos por Horário'
    )

    ranking = df_filtrado['Prato'].value_counts().nlargest(10).reset_index()
    ranking.columns = ['Prato', 'Pedidos']
    fig_ranking = px.bar(ranking, x='Pedidos', y='Prato', orientation='h', title='🥇 Top 10 Pratos Mais Vendidos')

    return kpis, fig_faturamento, fig_pedidos, fig_ticket, fig_heatmap, fig_ranking

# Rotas Flask
@server.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        if validate_login(username, password):
            user = User(username)
            login_user(user)
            return redirect("/dashboard/")
        else:
            return render_template("login.html", error="Usuário ou senha inválidos")
    return render_template("login.html")

@server.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect("/")

@app.server.before_request
def proteger_dashboard():
    # Protege o dashboard, redirecionando para o login se o usuário não estiver autenticado
    if request.path.startswith("/dashboard") and not current_user.is_authenticated:
        return redirect(url_for("login"))

if __name__ == "__main__":
    # Certifique-se de que 'dados_restaurante.csv' e 'login.html' existam
    # e que o módulo 'auth.py' esteja no mesmo diretório ou acessível.
    server.run(debug=True)