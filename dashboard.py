import streamlit as st
import pandas as pd
import time
from dotenv import load_dotenv
import os
from sqlalchemy import create_engine, text
from urllib.parse import quote
from datetime import datetime, timedelta
import plotly.graph_objs as go

# Carregar as variáveis de ambiente do arquivo .env
load_dotenv()

# Função para criar a conexão com o banco de dados PostgreSQL usando SQLAlchemy
def get_engine():
    db_host = os.getenv("DB_HOST")
    db_name = os.getenv("DB_NAME")
    db_user = os.getenv("DB_USER")
    db_password = os.getenv("DB_PASSWORD")
    
    # Codificar a senha para lidar com caracteres especiais
    db_password = quote(db_password)
    
    # Verifique se as variáveis de ambiente foram carregadas corretamente
    if not all([db_host, db_name, db_user, db_password]):
        raise ValueError("Certifique-se de que todas as variáveis de ambiente estão definidas no arquivo .env")
    
    return create_engine(f'postgresql://{db_user}:{db_password}@{db_host}/{db_name}')

# Função para buscar dados consolidados do banco de dados
def fetch_consolidated_data(engine, start_date, end_date):
    query = text(f"""
    SELECT 
        date_trunc('hour', 
            CASE 
                WHEN status = 'joined' THEN date_joined 
                WHEN status = 'left' THEN date_left 
            END) as hour, 
        status, 
        COUNT(*) as count 
    FROM events_telegram_tylty 
    WHERE 
        (status = 'joined' AND date_joined BETWEEN :start_date AND :end_date)
        OR (status = 'left' AND date_left BETWEEN :start_date AND :end_date)
    GROUP BY hour, status
    ORDER BY hour;
    """)
    df = pd.read_sql(query, engine, params={"start_date": start_date, "end_date": end_date})
    return df

def fetch_monthly_data(engine, start_date, end_date):
    query = text(f"""
    SELECT 
        date_trunc('day', 
            CASE 
                WHEN status = 'joined' THEN date_joined 
                WHEN status = 'left' THEN date_left 
            END) as day, 
        status, 
        COUNT(*) as count 
    FROM events_telegram_tylty 
    WHERE 
        (status = 'joined' AND date_joined BETWEEN :start_date AND :end_date)
        OR (status = 'left' AND date_left BETWEEN :start_date AND :end_date)
    GROUP BY day, status
    ORDER BY day;
    """)
    df = pd.read_sql(query, engine, params={"start_date": start_date, "end_date": end_date})
    return df

# Função para criar um título estilizado
def styled_metric(col, title, value):
    col.markdown(f"""
    <div style="background-color: #262730; padding: 20px; border-radius: 10px; text-align: center;">
        <h2 style="color: #ffffff; font-size: 40px; margin-bottom: 10px;">{title}</h2>
        <h1 style="color: #00c0f0; font-size: 65px; margin: 0;">{value}</h1>
    </div>
    """, unsafe_allow_html=True)

# Função para criar gráficos estilizados com plotly
def create_plotly_chart(data, x, y, title, color, x_title, y_title, name):
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=data[x],
        y=data[y],
        mode='lines+markers+text',
        marker=dict(color=color),
        line=dict(color=color),
        name=name,
        text=data[y],
        textposition='top center'
    ))

    fig.update_layout(
        title=title,
        title_x=0.5,
        plot_bgcolor='#262730',
        paper_bgcolor='#262730',
        font=dict(color='white'),
        xaxis=dict(
            title=x_title,
            gridcolor='gray',
            showgrid=True,
            zeroline=False,
            showline=False,
            tickmode='linear',
            dtick=1
        ),
        yaxis=dict(
            title=y_title,
            gridcolor='gray',
            showgrid=True,
            zeroline=False,
            showline=False
        ),
        margin=dict(l=0, r=0, t=30, b=0),
        height=800,
        showlegend=True,
        legend=dict(
            x=0,
            y=1,
            xanchor='left',
            yanchor='top',
            bgcolor='rgba(0,0,0,0)'
        )
    )
    return fig

# Configuração do Streamlit
st.set_page_config(layout="wide")
st.title("Fluxo de Membros do Grupo Grátis")

# Cria o engine de conexão
engine = get_engine()

# Criar colunas para os cartões em uma única linha
col1, col2, col3, col4 = st.columns(4)

# Espaços reservados para os cartões
joined_today_placeholder = col1.empty()
left_today_placeholder = col2.empty()
joined_month_placeholder = col3.empty()
left_month_placeholder = col4.empty()

# Adicionar espaçamento entre os cartões e os gráficos
st.write("\n\n\n")

# Criar colunas para os gráficos
graph_col1, graph_col2 = st.columns([1, 1])

# Espaços reservados para os gráficos
today_graph_placeholder = graph_col1.empty()
month_graph_placeholder = graph_col2.empty()

# Loop para atualização em tempo real
while True:
    today = datetime.today().date()
    start_of_today = datetime.combine(today, datetime.min.time())
    end_of_today = start_of_today + timedelta(days=1)

    current_month = datetime.today().month
    current_year = datetime.today().year
    start_of_month = datetime(current_year, current_month, 1)
    end_of_month = start_of_month + timedelta(days=31)  # Ajuste conforme necessário para o último dia do mês

    try:
        # Dados consolidados para hoje
        today_data = fetch_consolidated_data(engine, start_of_today, end_of_today)
        st.write("Today Data:", today_data)  # Log dos dados de hoje
        joined_today_count = today_data[today_data['status'] == 'joined']['count'].sum()
        left_today_count = today_data[today_data['status'] == 'left']['count'].sum()

        # Dados consolidados para o mês atual
        month_data = fetch_monthly_data(engine, start_of_month, end_of_month)
        st.write("Month Data:", month_data)  # Log dos dados do mês
        joined_month_count = month_data[month_data['status'] == 'joined']['count'].sum()
        left_month_count = month_data[month_data['status'] == 'left']['count'].sum()
    
        # Atualizar os cartões no Streamlit com estilo personalizado
        styled_metric(joined_today_placeholder, "Entraram Hoje", joined_today_count)
        styled_metric(left_today_placeholder, "Saíram Hoje", left_today_count)
        styled_metric(joined_month_placeholder, "Entraram Esse Mês", joined_month_count)
        styled_metric(left_month_placeholder, "Saíram Esse Mês", left_month_count)
    
        # Preparar dados para gráficos
        today_data['hour'] = pd.to_datetime(today_data['hour']).dt.hour
        month_data['day'] = pd.to_datetime(month_data['day']).dt.day
    
        joined_today_hourly = today_data[today_data['status'] == 'joined']
        left_today_hourly = today_data[today_data['status'] == 'left']

        joined_monthly = month_data[month_data['status'] == 'joined']
        left_monthly = month_data[month_data['status'] == 'left']
    
        # Criar gráficos
        today_joined_chart = create_plotly_chart(joined_today_hourly, 'hour', 'count', 'Entraram no grupo Hoje', '#00c0f0', 'Hour of Day', 'Count', 'Entraram no grupo')
        today_left_chart = create_plotly_chart(left_today_hourly, 'hour', 'count', 'Saíram do grupo Hoje', '#FFA500', 'Hour of Day', 'Count', 'Saíram do grupo')
    
        month_joined_chart = create_plotly_chart(joined_monthly, 'day', 'count', 'Entraram no grupo Este Mês', '#00c0f0', 'Day of Month', 'Count', 'Entraram no grupo')
        month_left_chart = create_plotly_chart(left_monthly, 'day', 'count', 'Saíram do grupo Este Mês', '#FFA500', 'Day of Month', 'Count', 'Saíram do grupo')
    
        # Combinar gráficos de hoje
        fig_today_combined = go.Figure(data=today_joined_chart.data + today_left_chart.data)
        fig_today_combined.update_layout(
            title='Métricas de Hoje',
            title_x=0.4,
            xaxis=dict(
                title='Hour of Day',
                gridcolor='gray',
                showgrid=False,
                zeroline=False,
                showline=False,
                tickmode='linear',
                dtick=1
            ),
            legend=dict(
                orientation='h',
                yanchor='bottom',
                y=1.1,
                xanchor='left',
                x=0
            )
        )
    
        # Combinar gráficos do mês
        fig_month_combined = go.Figure(data=month_joined_chart.data + month_left_chart.data)
        fig_month_combined.update_layout(
            title='Métricas Desse Mês',
            title_x=0.4,
            xaxis=dict(
                title='Day of Month',
                gridcolor='gray',
                showgrid=False,
                zeroline=False,
                showline=False,
                tickmode='linear',
                dtick=1
            ),
            legend=dict(
                orientation='h',
                yanchor='bottom',
                y=1.1,
                xanchor='left',
                x=0
            )
        )

        # Atualizar os gráficos nos placeholders
        today_graph_placeholder.plotly_chart(fig_today_combined, use_container_width=True)
        month_graph_placeholder.plotly_chart(fig_month_combined, use_container_width=True)
    
    except Exception as e:
        st.error(f"Erro ao buscar ou processar dados: {e}")
        st.write("Error details:", str(e))

    time.sleep(300)