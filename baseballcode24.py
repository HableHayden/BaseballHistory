import streamlit as st
import pandas as pd
import plotly.express as px
from pybaseball import batting_stats, cache

# Enable caching to speed up repeated runs
cache.enable()

# Fetch data function with error handling
@st.cache_data(ttl=3600)  # Cache for 1 hour
def fetch_data(year):
    try:
        return batting_stats(year, qual=10)  # Lower qualifier for older seasons
    except Exception as e:
        st.error(f"Error fetching data for {year}: {str(e)}")
        return pd.DataFrame()

# Clean data function
def clean_data(df):
    if not df.empty:
        df["OPS"] = df["OBP"] + df["SLG"]
        # Handle potential missing columns in older data
        cols = ["Name", "WAR", "OPS", "HR", "AVG", "Team"]
        available_cols = [c for c in cols if c in df.columns]
        return df[available_cols]
    return df

# Streamlit UI
st.title("⚾ Historical Baseball Dashboard (1900-Present)")

# Year range selector
current_year = pd.Timestamp.now().year
selected_year = st.sidebar.selectbox(
    "Season Year",
    options=range(current_year, 1899, -1),  # 2024 to 1900
    index=0  # Defaults to current year
)

# Minimum plate appearances filter
min_pa = st.sidebar.slider(
    "Minimum Plate Appearances",
    min_value=1,
    max_value=174,
    value=100
)

# Fetch and clean data
df = fetch_data(selected_year)
if not df.empty:
    df = df[df["PA"] >= min_pa]  # Apply PA filter
    df = clean_data(df)

# Show data
if not df.empty:
    st.header(f"{selected_year} Season Leaders")
    
    # Add team filter
    teams = ["All"] + sorted(df["Team"].dropna().unique().tolist())
    selected_team = st.sidebar.selectbox("Filter by Team", teams)
    
    if selected_team != "All":
        df = df[df["Team"] == selected_team]
    
    # Display metrics
    col1, col2, col3 = st.columns(3)
    col1.metric("Players Found", len(df))
    col2.metric("Top WAR", f"{df['WAR'].max():.1f}")
    col3.metric("Best OPS", f"{df['OPS'].max():.3f}")
    
    # Show dataframe
    st.dataframe(
        df.sort_values("WAR", ascending=False)
        .head(25)
        .style.format({"AVG": "{:.3f}", "OPS": "{:.3f}", "WAR": "{:.1f}"}),
        height=600
    )
    
    # Interactive plot
    st.header("Performance Visualization")
    plot_type = st.radio(
        "Plot Type",
        ["WAR vs OPS", "HR vs AVG"]
    )
    
    if plot_type == "WAR vs OPS":
        fig = px.scatter(
            df,
            x="OPS",
            y="WAR",
            color="Team",
            hover_name="Name",
            size="HR",
            title=f"{selected_year} WAR vs OPS"
        )
    else:
        fig = px.scatter(
            df,
            x="AVG",
            y="HR",
            color="Team",
            hover_name="Name",
            size="WAR",
            title=f"{selected_year} HR vs AVG"
        )
    st.plotly_chart(fig, use_container_width=True)
    
else:
    st.warning("No data available for the selected season.")
