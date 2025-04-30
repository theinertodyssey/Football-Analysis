import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path

st.set_page_config(page_title="Football League Analysis",layout="wide", page_icon="⚽")

st.markdown("""
    <style>
    .main {
        background-color: #f9f9f9;
    }
    .block-container {
        padding-top: 1rem;
        padding-bottom: 1rem;
        padding-left: 2rem;
        padding-right: 2rem;
    }
    h1, h2, h3 {
        color: #003366;
    }
    </style>
""", unsafe_allow_html=True)

st.title("⚽ Football League Analysis Dashboard")

DEFAULT_DATA_PATH = "pl-tables-1993-2024.csv"

@st.cache_data
def load_data(file_path):
    try:
        if file_path.endswith('.csv'):
            df = pd.read_csv(file_path)
        elif file_path.endswith(('.xlsx', '.xls')):
            df = pd.read_excel(file_path)
        elif file_path.endswith('.txt'):
            df = pd.read_csv(file_path, delimiter='\t')
        else:
            st.error("Unsupported file format. Please upload a CSV, Excel, or TXT file.")
            return None
        df.columns = df.columns.str.strip().str.lower()
        if 'season_end_year' in df.columns:
            df['season_end_year'] = df['season_end_year'].astype(int)
        return df
    except Exception as e:
        st.error(f"Error loading file: {e}")
        return None

uploaded_file = st.file_uploader("📁 Upload your Football League data file", type=['csv', 'xlsx', 'xls', 'txt'])

if uploaded_file:
    df = load_data(uploaded_file)
else:
    try:
        df = load_data(DEFAULT_DATA_PATH)
    except Exception as e:
        st.error(f"Could not load default data. Please upload your file.")
        st.stop()

if df is None:
    st.stop()


with st.expander("📦 Show Raw Data"):
    st.dataframe(df)

required_columns = ['season_end_year', 'team', 'position', 'played', 'won', 'drawn', 'lost', 'gf', 'ga', 'gd', 'points']
missing_cols = [col for col in required_columns if col not in df.columns]
if missing_cols:
    st.error(f"The data is missing required columns: {', '.join(missing_cols)}")
    st.stop()


st.sidebar.header("🔍 Filters")

seasons = sorted(df['season_end_year'].unique())
start_season = st.sidebar.selectbox("Start Season", seasons, index=len(seasons) - 3 )
end_season = st.sidebar.selectbox("End Season", seasons, index=len(seasons) - 1)

if start_season > end_season:
    st.sidebar.error("End season must be after start season")
    st.stop()

teams = sorted(df['team'].unique())
unique_seasons = df['season_end_year'].unique()
max_year = df['season_end_year'].max()

latest_season = 2024 if 2024 in unique_seasons else max_year
clubs_2024 = sorted(df[df['season_end_year'] == latest_season]['team'].unique())
all_clubs = sorted(df['team'].unique())

selected_clubs = st.sidebar.multiselect(
    "Filter by Club(s)",
    all_clubs,
    default=clubs_2024 if clubs_2024 else all_clubs[:5]
)



filtered_df = df[(df['season_end_year'] >= start_season) & (df['season_end_year'] <= end_season)]
if selected_clubs:
    filtered_df = filtered_df[filtered_df['team'].isin(selected_clubs)]


st.subheader("📊 Overview")
col1, col2, col3, col4 = st.columns(4)
col1.metric("🗓️ Seasons", f"{start_season-1}-{start_season} to {end_season-1}-{end_season}")
col2.metric("🏟️ Clubs Analyzed", filtered_df['team'].nunique())
col3.metric("🎮 Total Matches", filtered_df['played'].sum())
col4.metric("⚖️ Avg Points", round(filtered_df['points'].mean(), 1))

tab1, tab2, tab3, tab4 = st.tabs(["📈 Trends", "🎯 Performance", "🥅 Goals", "🏆 Top Performers"])

with tab1:
    st.subheader("📌 Team Positions Over Time")
    fig = px.line(filtered_df, x='season_end_year', y='position', color='team',
                  labels={'season_end_year': 'Season', 'position': 'Position'},
                  title="Team Positions Over Seasons")
    fig.update_yaxes(autorange="reversed", title="League Position")
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("𝄜 Points Distribution")
    fig = px.box(filtered_df, x='team', y='points', color='team',
                 title="Points Distribution by Team")
    st.plotly_chart(fig, use_container_width=True)

with tab2:
    st.subheader("🚀 Average Win Percentage")
    filtered_df['win_pct'] = (filtered_df['won'] / filtered_df['played']) * 100
    win_pct_df = filtered_df.groupby('team')['win_pct'].mean().sort_values(ascending=True).reset_index()

    fig = px.bar(win_pct_df,
                 x='win_pct',
                 y='team',
                 orientation='h',
                 text=win_pct_df['win_pct'].round(1),
                 title="🏆 Win Percentage by Team",
                 color='win_pct',
                 color_continuous_scale='Blues')
    fig.update_layout(yaxis=dict(title=''), xaxis_title='Win %',
                      plot_bgcolor='rgba(0,0,0,0)', height=500)
    fig.update_traces(textposition='outside')
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("🛡️ Goals Against Per Game")
    filtered_df['ga_per_game'] = filtered_df['ga'] / filtered_df['played']
    ga_df = filtered_df.groupby('team')['ga_per_game'].mean().sort_values().reset_index()

    fig = px.bar(ga_df,
                 x='ga_per_game',
                 y='team',
                 orientation='h',
                 text=ga_df['ga_per_game'].round(2),
                 title="🧱 Defensive Solidity: GA per Game",
                 color='ga_per_game',
                 color_continuous_scale='Reds_r')  # Reversed scale: red = worse
    fig.update_layout(yaxis=dict(title=''), xaxis_title='Goals Against/Game',
                      plot_bgcolor='rgba(0,0,0,0)', height=500)
    fig.update_traces(textposition='outside')
    st.plotly_chart(fig, use_container_width=True)


with tab3:
    st.subheader("🥅 Goals For vs Goals Against")
    goals_df = filtered_df.groupby('team').agg({'gf': 'sum', 'ga': 'sum'}).reset_index()
    goals_df['gd'] = goals_df['gf'] - goals_df['ga']

    fig = go.Figure()
    fig.add_trace(go.Bar(x=goals_df['team'], y=goals_df['gf'], name='Goals For', marker_color='green'))
    fig.add_trace(go.Bar(x=goals_df['team'], y=goals_df['ga'], name='Goals Against', marker_color='red'))
    fig.update_layout(barmode='group', title='Goals Comparison')
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("⚖️ Goal Difference")
    fig = px.bar(goals_df, x='team', y='gd', color='gd', title="Goal Difference",
                 color_continuous_scale='RdYlGn')
    st.plotly_chart(fig, use_container_width=True)

with tab4:
    st.subheader("🏅 Best Average League Position")
    avg_pos = filtered_df.groupby('team')['position'].mean().sort_values().head(10).reset_index()

    fig = px.bar(avg_pos,
                 x='position',
                 y='team',
                 orientation='h',
                 text=avg_pos['position'].round(1),
                 title="🎖️ Top 10: Best Average League Position",
                 color='position',
                 color_continuous_scale='Teal')
    fig.update_layout(yaxis=dict(title=''), xaxis_title='Average Position (Lower is Better)',
                      plot_bgcolor='rgba(0,0,0,0)', height=500)
    fig.update_traces(textposition='outside')
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("🔥 Highest Average Points")
    avg_pts = filtered_df.groupby('team')['points'].mean().sort_values(ascending=False).head(10).reset_index()

    fig = px.bar(avg_pts,
                 x='points',
                 y='team',
                 orientation='h',
                 text=avg_pts['points'].round(1),
                 title="💪 Top 10: Highest Average Points",
                 color='points',
                 color_continuous_scale='Viridis')
    fig.update_layout(yaxis=dict(title=''), xaxis_title='Avg Points',
                      plot_bgcolor='rgba(0,0,0,0)', height=500)
    fig.update_traces(textposition='outside')
    st.plotly_chart(fig, use_container_width=True)
