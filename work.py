
from plotly.graph_objs import Figure
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os
import re
import ssl
import certifi
import json
from urllib.error import URLError, HTTPError
from urllib.request import urlopen

st.set_page_config(page_title="PhonePe Summary", layout="wide")
st.markdown("<style>h2, h3, h4, h5, h6 { color: #d62728 !important; }</style>", unsafe_allow_html=True)
st.title("PHONE PE BUSINESS ANALYSIS SUMMARY")
st.sidebar.title("Navigation")
page = st.sidebar.radio("Go to:", ["Home", "Analysis", "Recommendation"])

# Total Scenarios
folder_path = os.path.expanduser("~/Downloads")
files = {
    "df1": "scenario_1a_data.csv",
    "df2": "scenario_1b_data.csv",
    "df3": "scenario_1c_data.csv",
    "df4": "scenario_1d_data.csv",
    "df5": "scenario_1e_data.csv",
    "df6": "scenario_1f_data.csv",
    "df7": "scenario_2a_data.csv",
    "df8": "scenario_2b_data.csv",
    "df9": "scenario_2c_data.csv",
    "df10": "scenario_2d_data.csv",
    "df11": "scenario_2e_data.csv",
    "df12": "scenario_3a_data.csv",
    "df13": "scenario_3b_data.csv",
    "df14": "scenario_3c_data.csv",
}

def load_data(key):
    if key not in files:
        raise KeyError(f"Unknown data key: {key}")

    filename = files[key]
    candidate_paths = [os.path.join(folder_path, filename)]

    if filename.lower().endswith('.csv'):
        base_name = os.path.splitext(filename)[0]
        candidate_paths.append(os.path.join(folder_path, f"{base_name}.csv"))

    for path in candidate_paths:
        if os.path.exists(path):
            df = pd.read_csv(path)
            df.columns = df.columns.str.strip()
            return df

    base_name = os.path.splitext(filename)[0].lower()
    matches = [
        f for f in os.listdir(folder_path)
        if f.lower().endswith('.csv') and base_name in f.lower()
    ]
    if matches:
        path = os.path.join(folder_path, matches[0])
        df = pd.read_csv(path)
        df.columns = df.columns.str.strip()
        return df

    return None


def get_column(df, *options):
    normalized = {col.strip().lower(): col for col in df.columns}
    for option in options:
        key = option.strip().lower()
        if key in normalized:
            return normalized[key]
    raise KeyError(f"None of the expected columns {options} were found. Available columns: {list(df.columns)}")


def normalize_state_name(value):
    if pd.isna(value):
        return ""
    text = str(value).strip().lower()
    text = text.replace('&', ' and ')
    text = re.sub(r"[^a-z0-9]+", "", text)
    return text





def load_india_map_data():
    ssl_context = ssl.create_default_context(cafile=certifi.where())
    geojson_url = "https://gist.githubusercontent.com/jbrobst/56c13bbbf9d97d187fea01ca62ea5112/raw/e388c4cae20aa53cb5090210a42ebb9b765c0a36/india_states.geojson"

    try:
        

        with urlopen(geojson_url, context=ssl_context, timeout=10) as geojson_resp:
            india_geojson = json.load(geojson_resp)
        return None, india_geojson
    except (URLError, HTTPError, TimeoutError, ValueError, ssl.SSLError, OSError) as exc:
        st.warning(f"India map data could not be loaded ({exc}). Showing a fallback view instead.")
        fallback_df = pd.DataFrame({
            "state": [
                "Andhra Pradesh", "Arunachal Pradesh", "Assam", "Bihar", "Chhattisgarh",
                "Goa", "Gujarat", "Haryana", "Himachal Pradesh", "Jharkhand",
                "Karnataka", "Kerala", "Madhya Pradesh", "Maharashtra", "Manipur",
                "Meghalaya", "Mizoram", "Nagaland", "Odisha", "Punjab",
                "Rajasthan", "Sikkim", "Tamil Nadu", "Telangana", "Tripura",
                "Uttar Pradesh", "Uttarakhand", "West Bengal"
            ],
            "Year": [2021] * 28,
            "total_transacion_amount": [0] * 28
        })
        return fallback_df, {"type": "FeatureCollection", "features": []}

def render_india_map(map_df, india_geojson, highlight_state: str | None = None, color_column: str = 'Year', title_text: str = 'India Map'):
    """
    Renders an interactive Plotly choropleth map of India, matching normalized
    state names to GeoJSON geometries. Handles distinct highlighting overlays.
    """
    map_df = map_df.copy()
    if 'state' not in map_df.columns and 'State' in map_df.columns:
        map_df = map_df.rename(columns={'State': 'state'})
        
    map_df['state'] = map_df['state'].astype(str).str.strip()
    map_df['state_normalized'] = map_df['state'].str.lower()

    # If GeoJSON failed to stream, return a clean empty fallback chart
    if not isinstance(india_geojson, dict) or not india_geojson.get("features"):
        fig = go.Figure()
        fig.add_annotation(
            text="Map boundary geometry is unavailable.",
            x=0.5, y=0.5, xref="paper", yref="paper", showarrow=False, font=dict(size=16)
        )
        fig.update_layout(
            title_text="India Map - Unavailable",
            paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
            margin=dict(t=40, b=0, l=0, r=0), height=720
        )
        return fig

    # Deep copy and match keys strictly in lowercase to avoid case mismatches
    import copy
    india_geojson = copy.deepcopy(india_geojson)
    for feature in india_geojson['features']:
        geo_state = feature['properties'].get('ST_NM', '')
        feature['id'] = str(geo_state).strip().lower()

    if highlight_state is not None:
        selected_col = 'selected_state'
        normalized_state = highlight_state.strip().lower() if isinstance(highlight_state, str) else ''
        map_df[selected_col] = map_df['state_normalized'] == normalized_state
        
        fig = px.choropleth(
            map_df,
            geojson=india_geojson,
            locations='state_normalized',
            color=selected_col,
            color_discrete_map={True: '#F7CAC9', False: '#E8EAF6'},
            category_orders={selected_col: [True, False]},
            labels={selected_col: 'Selected state'},
            hover_name='state'
        )
        fig.update_layout(
            title_text=f"{title_text} - Highlighting {highlight_state}",
            paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
            font_color='#333333', title_font_color='#2A4D69',
            margin=dict(t=40, b=0, l=0, r=0), height=720
        )
    else:
        fig = px.choropleth(
            map_df,
            geojson=india_geojson,
            locations='state_normalized',
            color=color_column,
            color_continuous_scale=['#F6D6AD', '#F7E2C8', '#D6E7C7', '#B9D6E8', '#EAD4F8'],
            labels={color_column: 'Transaction Volume'},
            hover_name='state'
        )
        fig.update_layout(
            title_text=title_text,
            paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
            font_color='#333333', title_font_color='#2A4D69',
            margin=dict(t=40, b=0, l=0, r=0), height=720
        )

    fig.update_geos(fitbounds="locations", visible=False)
    return fig

def render_india_map(map_df, india_geojson, highlight_state: str | None = None, color_column: str = 'Year', title_text: str = 'India Map'):
    map_df = map_df.copy()
    if 'state' not in map_df.columns and 'State' in map_df.columns:
        map_df = map_df.rename(columns={'State': 'state'})
        
    map_df['state'] = map_df['state'].astype(str).str.strip()

    # --- CRITICAL MAP UNIFICATION LAYER ---
    # Standardizes spelling deviations common across various Indian public datasets
    def standard_clean(name):
        text = str(name).strip().lower()
        text = text.replace('&', ' and ')
        text = text.replace('islands', '').replace('island', '')
        text = text.replace('nct of ', '').replace('and nicobar', ' & nicobar')
        text = re.sub(r'[^a-z0-9\s]+', '', text)  # Keep alpha-numeric formatting characters
        text = ' '.join(text.split())
        
        # Explicit spelling corrections mapping matrix
        corrections = {
            "orissa": "odisha",
            "pondicherry": "puducherry",
            "delhi": "nct of delhi",
            "andaman and nicobar": "andaman & nicobar",
            "dadra and nagar haveli and daman and diu": "dadra and nagar haveli & daman and diu",
            "daman and diu": "dadra and nagar haveli & daman and diu"
        }
        return corrections.get(text, text)

    # Standardize data framework states
    map_df['state_normalized'] = map_df['state'].apply(standard_clean)

    if not isinstance(india_geojson, dict) or not india_geojson.get("features"):
        fig = go.Figure()
        fig.add_annotation(text="Map boundary geometry is unavailable.", x=0.5, y=0.5, xref="paper", yref="paper", showarrow=False, font=dict(size=16))
        fig.update_layout(title_text="India Map - Unavailable", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', margin=dict(t=40, b=0, l=0, r=0), height=720)
        return fig

    # Deep copy and standardize GeoJSON properties identifiers
    import copy
    india_geojson = copy.deepcopy(india_geojson)
    for feature in india_geojson['features']:
        geo_state = feature['properties'].get('ST_NM', feature['properties'].get('NAME_1', ''))
        feature['id'] = standard_clean(geo_state)

    if highlight_state is not None:
        selected_col = 'selected_state'
        normalized_state = standard_clean(highlight_state)
        map_df[selected_col] = map_df['state_normalized'] == normalized_state
        
        fig = px.choropleth(
            map_df,
            geojson=india_geojson,
            locations='state_normalized',  # Joins cleanly on lowercase keys
            color=selected_col,
            color_discrete_map={True: '#d62728', False: '#E8EAF6'},
            category_orders={selected_col: [True, False]},
            labels={selected_col: 'Selected state'},
            hover_name='state'
        )
    else:
        fig = px.choropleth(
            map_df,
            geojson=india_geojson,
            locations='state_normalized',  # Joins cleanly on lowercase keys
            color=color_column,
            color_continuous_scale='Plasma',  # Changed to higher-contrast heat colors
            labels={color_column: 'Transaction Amount'},
            hover_name='state'
        )
        
    fig.update_layout(
        title_text=title_text,
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font_color='#333333',
        margin=dict(t=50, b=10, l=10, r=10),
        height=750  # Increased layout envelope size
    )

    # Automatically clips out empty peripheral whitespace globally
    fig.update_geos(fitbounds="locations", visible=False)
    return fig


if page == "Home":
    st.subheader("India Overview")

    st.markdown("---")
    _, india_geojson = load_india_map_data()
    raw_map_df =load_data('df1')
    if raw_map_df is not None:
        # CRITICAL FIX: Dynamically find the real State column name and rename it to 'state'
        # This prevents any KeyError: 'state' from crashing your app down below
        try:
            actual_state_col = get_column(raw_map_df, 'State', 'state', 'STATE')
            raw_map_df = raw_map_df.rename(columns={actual_state_col: 'state'})
        except KeyError:
            st.error("Could not find a valid State column in your CSV file. Please verify headers.")
            st.stop()
    year_col = get_column(raw_map_df, 'Year', 'year')
    amount_col = get_column(raw_map_df, 'total_transacion_amount', 'Transaction Amount')
        # Check if multiple years exist to prevent empty filter controls
    available_years = sorted(raw_map_df[year_col].dropna().unique())
    selected_year = st.selectbox("Select Year for Transaction Map:", available_years, key='home_year_select')
    map_df = raw_map_df[raw_map_df[year_col] == selected_year].copy()
    title_text = f"State-wise Transaction Amount ({selected_year})"
    state_options = sorted(map_df['state'].dropna().unique())
    selected_state_home = st.selectbox("Highlight state on map:", ["None"] + state_options, key='home_state_highlight')
    highlight_state_value = selected_state_home if selected_state_home != "None" else None    
        # Target transaction metrics as the main choropleth heat layer variable
    color_column = amount_col
        



    # 6. Render the finalized interactive map matrix chart
    fig = render_india_map(
    map_df=map_df, 
    india_geojson=india_geojson, 
    highlight_state=highlight_state_value, 
    color_column=amount_col, 
    title_text=title_text
)
    st.plotly_chart(fig, key='home_india_map', use_container_width=True)
    

    st.markdown("---")
    st.subheader("Annual Totals")
    df_yearly = load_data('df1')
    df_registered = load_data('df7')

    col_left, col_right = st.columns([3, 1])
    with col_left:
        if df_yearly is not None:
            year_summary = df_yearly.groupby('Year', as_index=False)['total_transacion_amount'].sum()
            fig_year = px.bar(
                year_summary,
                x='Year',
                y='total_transacion_amount',
                title='Total Transaction Amount by Year',
                color='total_transacion_amount',
                color_continuous_scale=px.colors.sequential.Teal
            )
            fig_year.update_layout(yaxis_title='Transaction Amount', xaxis_title='Year', margin=dict(t=40, b=20, l=20, r=20))
            st.plotly_chart(fig_year, key='home_transaction_amount_by_year', width='content')

        else:
            st.warning('Yearly transaction data is not available.')

    with col_right:
        if df_registered is not None and 'Total_Registered_Users' in df_registered.columns:
            total_registered = df_registered['Total_Registered_Users'].sum()
            st.metric(label='Total Registered Users', value=f"{int(total_registered):,}")
        else:
            st.warning('Registered user dataset is not available or missing expected columns.')

        df_active_users = load_data('df8')
        if df_active_users is not None and 'Total_Active_Users' in df_active_users.columns:
            total_active = df_active_users['Total_Active_Users'].sum()
            st.metric(label='Total Active Users', value=f"{int(total_active):,}")
        else:
            st.warning('Active user dataset is not available or missing expected columns.')

    st.markdown("---")
    st.markdown("### Top Performing State")
    df_yearly = load_data('df1')
    df_active_users = load_data('df7')
    if df_yearly is not None:
        state_col_yearly = get_column(df_yearly, 'State', 'state')
        yearly_summary = df_yearly.groupby(state_col_yearly, as_index=False)['total_transacion_amount'].sum()
        top_state_row = yearly_summary.sort_values('total_transacion_amount', ascending=False).head(1)
        if not top_state_row.empty:
            top_state_name = top_state_row.iloc[0][state_col_yearly]
            top_state_txn = int(top_state_row.iloc[0]['total_transacion_amount'])
            top_state_active = 0
            if df_active_users is not None:
                state_col_active = get_column(df_active_users, 'State', 'state')
                active_summary = df_active_users.groupby(state_col_active, as_index=False)['Total_Registered_Users'].sum()
                matched = active_summary[active_summary[state_col_active].str.strip().str.lower() == str(top_state_name).strip().lower()]
                if not matched.empty:
                    top_state_active = int(matched.iloc[0]['Total_Registered_Users'])
            colA, colB = st.columns([2, 1])
            colA.metric('Top State', str(top_state_name).title())
            colB.metric('Top State Txn', f'₹{top_state_txn:,}')
            st.metric('Active Users in Top State', f'{top_state_active:,}')
        else:
            st.info('Unable to determine top performing state from transaction data.')
    else:
        st.warning('Yearly transaction data is not available.')

elif page == "Analysis":
    scenario_options = {
        "Scenario_1: Decoding Transaction Dynamics on PhonePe": "Scenario_1",
        "Scenario_2: Device Dominance and User Engagement Analysis": "Scenario_2",
        "Scenario_3: Transaction Analysis for Market Expansion": "Scenario_3",
        "Scenario_4: User Engagement and Retention Strategies": "Scenario_4",
        "Scenario_5:Insurance Transactions Analysis": "Scenario_5"
    }
    selected_scenario = st.selectbox(
        label="Choose a scenario:",
        options=list(scenario_options.keys())
    )
    scenario_key = scenario_options[selected_scenario]

    if scenario_key == "Scenario_1":
        st.markdown("**1. Decoding Transaction Dynamics on PhonePe**\n\n**Scenario**\n\nPhonePe, a leading digital payments platform, has recently identified significant variations in transaction behavior across states, quarters, and payment categories. While some regions and transaction types demonstrate consistent growth, others show stagnation or decline. The leadership team seeks a deeper understanding of these patterns to drive targeted business strategies.")
        st.subheader("State-Wise Transaction Data - Yearly")
        df_scenario1a = load_data('df1')
        state_col = get_column(df_scenario1a, "State", "state")
        unique_states = sorted(df_scenario1a[state_col].dropna().unique())
        selected_state = st.selectbox("Select State:", unique_states, key='scenario1a_select_state')
        filtered_df = df_scenario1a[df_scenario1a[state_col] == selected_state]

        chart_data = filtered_df.groupby('Year')['total_transacion_amount'].sum().reset_index()
        chart_data['Year'] = chart_data['Year'].astype(str)
        fig = px.line(
            chart_data,
            x='Year',
            y='total_transacion_amount',
            title=f"Year vs Total Transaction Amount ({selected_state})",
            markers=True
        )
        fig.update_traces(line_width=8, mode="lines+markers+text", textposition="top center", cliponaxis=False)
        st.plotly_chart(fig, width='stretch', key='scenario1a_transaction_trend')

        st.subheader("Transaction Data - Quarterly each Year")
        df_scenario1b = load_data('df2')
        unique_years = sorted(df_scenario1b['Year'].dropna().unique())
        selected_year = st.selectbox("Select Year:", unique_years, key='scenario1b_select_year')
        filtered_df = df_scenario1b[df_scenario1b['Year'] == selected_year]
        chart_data = filtered_df.groupby(['Quater'])['total_transacion_amount'].sum().reset_index()
        chart_data['Quater'] = chart_data['Quater'].astype(str)
        fig = px.area(
            chart_data,
            x='Quater',
            y='total_transacion_amount',
            title=f"Year vs Total Transaction Amount ({selected_year})",
            color_discrete_sequence=["#08894f"],
            markers=True
        )
        st.plotly_chart(fig, width='stretch', key='scenario1b_quarterly_area')

        st.subheader("Payment Type Analysis")
        df_scenario1d = load_data('df4')
        chart_data = df_scenario1d.groupby(['Year', 'Transacion_type'])['total_transacion_amount'].sum().reset_index()
        fig_donut = px.sunburst(
            chart_data,
            path=['Year', 'Transacion_type'],
            values='total_transacion_amount',
            color='Year',
            color_continuous_scale=px.colors.sequential.Cividis
        )
        fig_donut.update_layout(margin=dict(t=30, l=10, r=10, b=10), height=500)
        st.plotly_chart(fig_donut, width='stretch', key='scenario1d_payment_type')

    elif scenario_key == "Scenario_2":
        st.markdown("**2. Device Dominance and User Engagement Analysis**\n\n**Scenario**\n\nPhonePe aims to enhance user engagement and improve app performance by understanding user preferences across different device brands. The data reveals the number of registered users and app opens, segmented by device brands, regions, and time periods. However, trends in device usage vary significantly across regions, and some devices are disproportionately underutilized despite high registration numbers.")
        st.subheader("User Registration Analysis")

        df_scenario2a = load_data('df7')
        state_col = get_column(df_scenario2a, "State", "state")

        fig_pie = px.pie(
            df_scenario2a,
            values="Total_Registered_Users",
            names=state_col,
            title="Total User Registration Share by State"
        )
        fig_pie.update_traces(textinfo="percent+label", textposition="inside")
        fig_pie.update_layout(height=450, showlegend=True)
        st.plotly_chart(fig_pie, key='scenario2a_registration_pie', width='content')

        st.subheader("Total Registered Users Vs Active Users Analysis")
        df_scenario2c = load_data('df9')
        if df_scenario2c is None:
            st.info("The optional scenario dataset for this chart is not available in Downloads yet.")
        else:
            fig = go.Figure()
            state_col = get_column(df_scenario2c, 'State', 'state')
            registered_col = get_column(df_scenario2c, 'total_registered_users', 'Total_Registered_Users', 'Registered Users')
            app_opens_col = get_column(df_scenario2c, 'total_app_opens', 'Total_App_Opens', 'App Opens')
            fig.add_trace(
                go.Bar(
                    x=df_scenario2c[state_col],
                    y=df_scenario2c[registered_col],
                    name='Registered Users',
                    marker_color='#1f77b4',
                    yaxis='y1'
                )
            )
            fig.add_trace(
                go.Scatter(
                    x=df_scenario2c[state_col],
                    y=df_scenario2c[app_opens_col],
                    name='App Opens',
                    mode='lines+markers',
                    line=dict(color='#ff7f0e', width=3),
                    marker=dict(size=8),
                    yaxis='y2'
                )
            )
            fig.update_layout(
                xaxis=dict(title='State'),
                yaxis=dict(
                    title=dict(text='Registered Users', font=dict(color='#1f77b4')),
                    tickfont=dict(color='#1f77b4')
                ),
                yaxis2=dict(
                    title=dict(text='App Opens', font=dict(color='#ff7f0e')),
                    tickfont=dict(color='#ff7f0e'),
                    anchor='x',
                    overlaying='y',
                    side='right'
                ),
                legend=dict(x=0.8, y=1.1, orientation='h'),
                hovermode="x unified",
                margin=dict(l=70, r=70, t=70, b=70),
                height=750,
                width=3200
            )
            st.plotly_chart(fig, key='scenario2_registered_vs_app_opens', width='content')

        st.subheader("Device Dominance Analysis")
        df_scenario2b = load_data('df8')
        fig = px.pie(
            df_scenario2b,
            values="Total_Active_Users",
            names="Brand",
            color_discrete_sequence=px.colors.qualitative.Set3,
            hole=0.5,
            title="Distribution of Total Active Users"
        )
        st.plotly_chart(fig, key='scenario2b_device_donut', width='content')


    elif scenario_key == "Scenario_3":
        st.subheader("Overall Performance Index of States and Districts")
        st.subheader("Top 5 Declining Transactions by Region over the Years")
        df_scenario1c = load_data('df3')
        df_sorted = df_scenario1c.sort_values(by="Total_Transaction_amount", ascending=False).head(5)
        fig = px.bar(
            df_sorted,
            x='Region_name',
            y='Total_Transaction_amount',
            text="Year",
            title="Top 5 Declining Transactions by Region over the Years",
            color_discrete_sequence=["#ff9999"]
        )
        st.plotly_chart(fig, width='stretch', key='scenario1c_declining_transactions')

        df_scenario1e = load_data('df5')
        df_scenario1f = load_data('df6')
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("Top overall performing state")
            df_combined = df_scenario1e.groupby(["top_state_name", "year"], as_index=False)["most_transaction_amount"].sum()
            df_top_sorted_state = df_combined.sort_values(by=["year", "most_transaction_amount"], ascending=False)
            fig_topstate = px.scatter(
                df_top_sorted_state,
                x='top_state_name',
                y='most_transaction_amount',
                text="year",
                orientation='h',
                color_discrete_sequence=["#7400CC"],
                title='Top Overall Performing States'
            )
            fig_topstate.update_layout(yaxis={'categoryorder':'total ascending'}, margin=dict(t=30, l=100, r=10, b=30))
            st.plotly_chart(fig_topstate, width='stretch', key='scenario1e_top_state')
        with col2:
            st.subheader("Top overall performing district")
            df_combined2 = df_scenario1f.groupby(["district_name", "year"], as_index=False)["most_transaction_amount"].sum()
            df_top_sorted_district = df_combined2.sort_values(by=["year", "most_transaction_amount"], ascending=False)
            fig_topdistrict = px.scatter(
                df_top_sorted_district,
                x='district_name',
                y='most_transaction_amount',
                text="year",
                orientation='h',
                color_discrete_sequence=["#ff6b6b"],
                title='Top Overall Performing Districts'
            )
            fig_topdistrict.update_layout(yaxis={'categoryorder':'total ascending'}, margin=dict(t=30, l=100, r=10, b=30))
            st.plotly_chart(fig_topdistrict, width='stretch', key='scenario1f_top_district')

    elif scenario_key == "Scenario_4":
        st.subheader("Total Registered Users Vs Active Users Analysis")
        df_scenario2c = load_data('df9')
        if df_scenario2c is None:
            st.info("The optional scenario dataset for this chart is not available in Downloads yet.")
        else:
            fig = go.Figure()
            state_col = get_column(df_scenario2c, 'State', 'state')
            registered_col = get_column(df_scenario2c, 'total_registered_users', 'Total_Registered_Users', 'Registered Users')
            app_opens_col = get_column(df_scenario2c, 'total_app_opens', 'Total_App_Opens', 'App Opens')
            fig.add_trace(
                go.Bar(
                    x=df_scenario2c[state_col],
                    y=df_scenario2c[registered_col],
                    name='Registered Users',
                    marker_color='#1f77b4',
                    yaxis='y1'
                )
            )
            fig.add_trace(
                go.Scatter(
                    x=df_scenario2c[state_col],
                    y=df_scenario2c[app_opens_col],
                    name='App Opens',
                    mode='lines+markers',
                    line=dict(color='#ff7f0e', width=3),
                    marker=dict(size=8),
                    yaxis='y2'
                )
            )
            fig.update_layout(
                xaxis=dict(title='State'),
                yaxis=dict(
                    title=dict(text='Registered Users', font=dict(color='#1f77b4')),
                    tickfont=dict(color='#1f77b4')
                ),
                yaxis2=dict(
                    title=dict(text='App Opens', font=dict(color='#ff7f0e')),
                    tickfont=dict(color='#ff7f0e'),
                    anchor='x',
                    overlaying='y',
                    side='right'
                ),
                legend=dict(x=0.8, y=1.1, orientation='h'),
                hovermode="x unified",
                margin=dict(l=70, r=70, t=70, b=70),
                height=750,
                width=3200
            )
            col_chart, _ = st.columns([1.8, 0.2])
            with col_chart:
                st.plotly_chart(fig, key='scenario2c_registered_vs_app_opens', width='content')


        st.subheader("States with Highest and Lowest Active Users")
        df_scenario2d = load_data('df10')
        df_scenario2e = load_data('df11')
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("Top states with highest active users")
            fig = px.bar(
                df_scenario2d,
                x='state',
                y='total_app_opens_for_top_5_users',
                text="state",
                title="Top states with highest active users",
                color_discrete_sequence=["#36df4f"]
            )
            st.plotly_chart(fig, width='stretch', key='scenario2d_highest_active_states')
        with col2:
            st.subheader("Top states with lowest active users")
            fig = px.bar(
                df_scenario2e,
                x='state',
                y='total_app_opens_for_bottom_users',
                text="state",
                title="Top states with lowest active users",
                color_discrete_sequence=["#d9215b"]
            )
            st.plotly_chart(fig, width='stretch', key='scenario2e_lowest_active_states')

    elif scenario_key == "Scenario_5":
        st.markdown("**5. Insurance Transactions Analysis**\n\n**Scenario**\n\nThe insurance business wants to understand where high-value transactions are concentrated across states, quarters, and pincodes so that growth and retention strategies can be targeted more effectively.")

        st.subheader("Insurance Amount Trend by State")
        df_scenario5a = load_data('df12')
        if df_scenario5a is not None:
            state_col = get_column(df_scenario5a, 'State_Name', 'state_name', 'State', 'state')
            year_col = get_column(df_scenario5a, 'Year', 'year')
            amount_col = get_column(df_scenario5a, 'top_insurance_amount', 'Top_Insurance_Amount', 'Insurance_Amount', 'total_insurance_amount')
            chart_df = df_scenario5a[[state_col, year_col, amount_col]].copy()
            chart_df[year_col] = pd.to_numeric(chart_df[year_col], errors='coerce').fillna(0).astype(int)
            chart_df = chart_df.groupby([state_col, year_col], as_index=False)[amount_col].sum()
            fig = px.bar(
                chart_df,
                x=amount_col,
                y=state_col,
                color=state_col,
                orientation='h',
                title='Insurance amount by state'
            )
            fig.update_layout(
                height=450,
                margin=dict(t=40, b=20, l=20, r=20),
                xaxis_title='Transaction Amount',
                yaxis_title='State Name'
            )
            st.plotly_chart(fig, key='scenario5_state_trend', width='content')
        else:
            st.info('Insurance state-level data is not available.')

        st.subheader("Quarterly Insurance Amount Distribution")
        df_scenario5b = load_data('df13')
        if df_scenario5b is not None:
            year_col = get_column(df_scenario5b, 'Year', 'year')
            quarter_col = get_column(df_scenario5b, 'Quarter', 'quarter')
            amount_col = get_column(df_scenario5b, 'top_insurance_amount', 'Top_Insurance_Amount', 'Insurance_Amount', 'total_insurance_amount')
            chart_df = df_scenario5b[[year_col, quarter_col, amount_col]].copy()
            chart_df[year_col] = pd.to_numeric(chart_df[year_col], errors='coerce').fillna(0).astype(int)
            chart_df = chart_df.groupby([year_col, quarter_col], as_index=False)[amount_col].sum()
            chart_df[year_col] = chart_df[year_col].astype(int).astype(str)
            fig = px.bar(
                chart_df,
                x=quarter_col,
                y=amount_col,
                color=year_col,
                barmode='group',
                title='Quarterly insurance amount by year'
            )
            fig.update_layout(height=450, margin=dict(t=40, b=20, l=20, r=20))
            fig.for_each_trace(lambda t: t.update(name=str(int(float(t.name))) if str(t.name).replace('.', '', 1).isdigit() else str(t.name)))
            st.plotly_chart(fig, key='scenario5_quarterly_distribution', width='content')
        else:
            st.info('Insurance quarterly data is not available.')


elif page == "Recommendation":
    st.subheader("Scenario-Based Recommendations")
    st.markdown("### Insights and recommendations tailored to each scenario")

    scenario_options = {
        "Scenario_1: Decoding Transaction Dynamics on PhonePe": "Scenario_1",
        "Scenario_2: Device Dominance and User Engagement Analysis": "Scenario_2",
        "Scenario_3: Transaction Analysis for Market Expansion": "Scenario_3",
        "Scenario_4: User Engagement and Retention Strategies": "Scenario_4",
        "Scenario_5: Insurance Transactions Analysis": "Scenario_5"
    }
    selected_scenario = st.selectbox(
        label="Choose a scenario for recommendations:",
        options=list(scenario_options.keys()),
        key='recommendation_scenario_select'
    )
    scenario_key = scenario_options[selected_scenario]

    def render_scenario_recommendations(title, insights, recommendations):
        st.markdown(f"#### {title}")
        st.markdown("**Key insights**")
        if insights:
            for item in insights:
                st.write(f"- {item}")
        else:
            st.info("No insight data available for this scenario yet.")

        st.markdown("**Recommendations**")
        if recommendations:
            for item in recommendations:
                st.write(f"- {item}")
        else:
            st.info("No recommendation data available for this scenario yet.")

    if scenario_key == "Scenario_1":
        df_yearly = load_data('df1')
        df_quarterly = load_data('df2')
        df_payment = load_data('df4')
        insights = []
        recommendations = []

        if df_yearly is not None:
            state_col = get_column(df_yearly, 'State', 'state')
            transaction_summary = df_yearly.groupby(state_col, as_index=False)['total_transacion_amount'].sum()
            top_state_row = transaction_summary.sort_values('total_transacion_amount', ascending=False).head(1)
            if not top_state_row.empty:
                top_state_name = str(top_state_row.iloc[0][state_col]).title()
                top_state_txn = int(top_state_row.iloc[0]['total_transacion_amount'])
                insights.append(f"{top_state_name} has the highest transaction volume at ₹{top_state_txn:,}.")
                recommendations.append(f"Prioritize {top_state_name} for targeted promotions, retention offers, and expansion plans.")

        if df_quarterly is not None and 'Quater' in df_quarterly.columns and 'total_transacion_amount' in df_quarterly.columns:
            quarter_summary = df_quarterly.groupby('Quater', as_index=False)['total_transacion_amount'].sum()
            if len(quarter_summary) >= 2:
                quarter_summary = quarter_summary.sort_values('total_transacion_amount', ascending=False)
                best = quarter_summary.iloc[0]
                worst = quarter_summary.iloc[-1]
                insights.append(f"{best['Quater']} records the strongest transaction activity at ₹{int(best['total_transacion_amount']):,}, while {worst['Quater']} shows the weakest.")
                recommendations.append(f"Double down on campaigns during {best['Quater']} and investigate the underperformance of {worst['Quater']}.")

        if df_payment is not None:
            payment_col = get_column(df_payment, 'Transacion_type', 'transaction_type', 'payment_type')
            amount_col = get_column(df_payment, 'total_transacion_amount', 'Transaction_Amount', 'amount')
            payment_summary = df_payment.groupby(payment_col, as_index=False)[amount_col].sum()
            top_payment_row = payment_summary.sort_values(amount_col, ascending=False).head(1)
            if not top_payment_row.empty:
                top_payment_name = str(top_payment_row.iloc[0][payment_col]).title()
                top_payment_value = int(top_payment_row.iloc[0][amount_col])
                insights.append(f"{top_payment_name} is the dominant payment type with ₹{top_payment_value:,} in transaction volume.")
                recommendations.append(f"Focus product and service improvements around {top_payment_name} to maximize customer value.")

        render_scenario_recommendations("Scenario 1: Transaction Dynamics", insights, recommendations)

    elif scenario_key == "Scenario_2":
        df_registered = load_data('df7')
        df_device = load_data('df8')
        df_engagement = load_data('df9')
        insights = []
        recommendations = []

        if df_registered is not None:
            state_col = get_column(df_registered, 'State', 'state')
            state_summary = df_registered.groupby(state_col, as_index=False)['Total_Registered_Users'].sum()
            top_state_row = state_summary.sort_values('Total_Registered_Users', ascending=False).head(1)
            if not top_state_row.empty:
                top_state_name = str(top_state_row.iloc[0][state_col]).title()
                top_state_users = int(top_state_row.iloc[0]['Total_Registered_Users'])
                insights.append(f"{top_state_name} has the highest registered user base with {top_state_users:,} users.")
                recommendations.append(f"Invest more in onboarding and retention efforts for {top_state_name} to convert registrations into sustained engagement.")

        if df_device is not None and 'Brand' in df_device.columns and 'Total_Active_Users' in df_device.columns:
            brand_summary = df_device.groupby('Brand', as_index=False)['Total_Active_Users'].sum()
            top_brand_row = brand_summary.sort_values('Total_Active_Users', ascending=False).head(1)
            if not top_brand_row.empty:
                top_brand_name = str(top_brand_row.iloc[0]['Brand'])
                top_brand_active = int(top_brand_row.iloc[0]['Total_Active_Users'])
                insights.append(f"{top_brand_name} dominates active-user share with {top_brand_active:,} users.")
                recommendations.append(f"Optimize app experience and partner support for {top_brand_name} to strengthen device-level engagement.")

        if df_engagement is not None:
            state_col = get_column(df_engagement, 'State', 'state')
            registered_col = get_column(df_engagement, 'total_registered_users', 'Total_Registered_Users', 'Registered Users')
            app_opens_col = get_column(df_engagement, 'total_app_opens', 'Total_App_Opens', 'App Opens')
            engagement_df = df_engagement.groupby(state_col, as_index=False).agg({registered_col: 'sum', app_opens_col: 'sum'})
            engagement_df['open_per_user'] = engagement_df[app_opens_col] / (engagement_df[registered_col] + 1)
            best_state = engagement_df.sort_values('open_per_user', ascending=False).head(1)
            if not best_state.empty:
                best_state_name = str(best_state.iloc[0][state_col]).title()
                best_ratio = round(best_state.iloc[0]['open_per_user'], 2)
                insights.append(f"{best_state_name} shows the strongest engagement ratio at {best_ratio} app opens per registered user.")
                recommendations.append(f"Use {best_state_name} as a benchmark for successful engagement strategies and replicate its playbook in other states.")

        render_scenario_recommendations("Scenario 2: Device and Engagement", insights, recommendations)

    elif scenario_key == "Scenario_3":
        df_region = load_data('df3')
        df_state = load_data('df5')
        df_district = load_data('df6')
        insights = []
        recommendations = []

        if df_region is not None:
            region_col = get_column(df_region, 'Region_name', 'region_name', 'Region', 'region')
            amount_col = get_column(df_region, 'Total_Transaction_amount', 'total_transaction_amount', 'transaction_amount')
            region_summary = df_region.groupby(region_col, as_index=False)[amount_col].sum()
            top_region_row = region_summary.sort_values(amount_col, ascending=False).head(1)
            if not top_region_row.empty:
                top_region_name = str(top_region_row.iloc[0][region_col]).title()
                top_region_value = int(top_region_row.iloc[0][amount_col])
                insights.append(f"{top_region_name} contributes the highest transaction value in the market expansion data at ₹{top_region_value:,}.")
                recommendations.append(f"Expand market development efforts around {top_region_name} while tracking similar regions for replication.")

        if df_state is not None:
            state_col = get_column(df_state, 'top_state_name', 'state_name', 'state', 'top_state')
            amount_col = get_column(df_state, 'most_transaction_amount', 'transaction_amount', 'amount')
            state_summary = df_state.groupby(state_col, as_index=False)[amount_col].sum()
            top_state_row = state_summary.sort_values(amount_col, ascending=False).head(1)
            if not top_state_row.empty:
                top_state_name = str(top_state_row.iloc[0][state_col]).title()
                top_state_value = int(top_state_row.iloc[0][amount_col])
                insights.append(f"{top_state_name} is the strongest performing state with ₹{top_state_value:,} in transaction activity.")
                recommendations.append(f"Use {top_state_name} as an expansion benchmark and deepen partnerships there.")

        if df_district is not None:
            district_col = get_column(df_district, 'district_name', 'district', 'District')
            amount_col = get_column(df_district, 'most_transaction_amount', 'transaction_amount', 'amount')
            district_summary = df_district.groupby(district_col, as_index=False)[amount_col].sum()
            top_district_row = district_summary.sort_values(amount_col, ascending=False).head(1)
            if not top_district_row.empty:
                top_district_name = str(top_district_row.iloc[0][district_col]).title()
                top_district_value = int(top_district_row.iloc[0][amount_col])
                insights.append(f"{top_district_name} shows the strongest district-level performance with ₹{top_district_value:,}.")
                recommendations.append(f"Prioritize district-level operational support and local outreach for {top_district_name}.")

        render_scenario_recommendations("Scenario 3: Market Expansion", insights, recommendations)

    elif scenario_key == "Scenario_4":
        df_engagement = load_data('df9')
        df_high = load_data('df10')
        df_low = load_data('df11')
        insights = []
        recommendations = []

        if df_engagement is not None:
            state_col = get_column(df_engagement, 'State', 'state')
            registered_col = get_column(df_engagement, 'total_registered_users', 'Total_Registered_Users', 'Registered Users')
            app_opens_col = get_column(df_engagement, 'total_app_opens', 'Total_App_Opens', 'App Opens')
            engagement_df = df_engagement.groupby(state_col, as_index=False).agg({registered_col: 'sum', app_opens_col: 'sum'})
            engagement_df['open_per_user'] = engagement_df[app_opens_col] / (engagement_df[registered_col] + 1)
            best_engagement = engagement_df.sort_values('open_per_user', ascending=False).head(1)
            if not best_engagement.empty:
                best_state_name = str(best_engagement.iloc[0][state_col]).title()
                best_ratio = round(best_engagement.iloc[0]['open_per_user'], 2)
                insights.append(f"{best_state_name} has the best engagement ratio, reaching {best_ratio} app opens per registered user.")
                recommendations.append(f"Use {best_state_name} as a benchmark and replicate its engagement tactics across other states.")

        if df_high is not None:
            highest_state = str(df_high.iloc[0]['state']).title() if not df_high.empty else None
            if highest_state:
                insights.append(f"{highest_state} appears among the states with the highest active user activity.")
                recommendations.append(f"Increase retention and push marketing campaigns in {highest_state} to sustain momentum.")

        if df_low is not None:
            lowest_state = str(df_low.iloc[0]['state']).title() if not df_low.empty else None
            if lowest_state:
                insights.append(f"{lowest_state} appears among the states with the lowest active user activity.")
                recommendations.append(f"Design targeted reactivation and awareness campaigns for {lowest_state} to improve participation.")

        render_scenario_recommendations("Scenario 4: Retention Strategy", insights, recommendations)

    elif scenario_key == "Scenario_5":
        df_state = load_data('df12')
        df_quarter = load_data('df13')
        df_pincode = load_data('df14')
        insights = []
        recommendations = []

        if df_state is not None:
            state_col = get_column(df_state, 'State_Name', 'state_name', 'State', 'state')
            amount_col = get_column(df_state, 'top_insurance_amount', 'Top_Insurance_Amount', 'Insurance_Amount', 'total_insurance_amount')
            state_summary = df_state.groupby(state_col, as_index=False)[amount_col].sum()
            top_state_row = state_summary.sort_values(amount_col, ascending=False).head(1)
            if not top_state_row.empty:
                top_state_name = str(top_state_row.iloc[0][state_col]).title()
                top_state_value = int(top_state_row.iloc[0][amount_col])
                insights.append(f"{top_state_name} has the highest insurance transaction value at ₹{top_state_value:,}.")
                recommendations.append(f"Prioritize policy and partnership growth in {top_state_name} to capture high-value opportunities.")

        if df_quarter is not None:
            quarter_col = get_column(df_quarter, 'Quarter', 'quarter')
            amount_col = get_column(df_quarter, 'top_insurance_amount', 'Top_Insurance_Amount', 'Insurance_Amount', 'total_insurance_amount')
            quarter_summary = df_quarter.groupby(quarter_col, as_index=False)[amount_col].sum()
            top_quarter_row = quarter_summary.sort_values(amount_col, ascending=False).head(1)
            if not top_quarter_row.empty:
                top_quarter_name = str(top_quarter_row.iloc[0][quarter_col])
                top_quarter_value = int(top_quarter_row.iloc[0][amount_col])
                insights.append(f"{top_quarter_name} contributes the largest insurance amount at ₹{top_quarter_value:,}.")
                recommendations.append(f"Align campaigns and customer outreach around {top_quarter_name} to capitalize on peak demand.")

        if df_pincode is not None:
            pincode_col = get_column(df_pincode, 'Pincode', 'pincode')
            amount_col = get_column(df_pincode, 'top_insurance_amount', 'Top_Insurance_Amount', 'Insurance_Amount', 'total_insurance_amount')
            pincode_summary = df_pincode.groupby(pincode_col, as_index=False)[amount_col].sum()
            top_pincode_row = pincode_summary.sort_values(amount_col, ascending=False).head(1)
            if not top_pincode_row.empty:
                top_pincode_name = str(top_pincode_row.iloc[0][pincode_col])
                top_pincode_value = int(top_pincode_row.iloc[0][amount_col])
                insights.append(f"Pincode {top_pincode_name} is the strongest insurance hotspot with ₹{top_pincode_value:,} in value.")
                recommendations.append(f"Focus local sales and servicing efforts around pincode {top_pincode_name}.")

        render_scenario_recommendations("Scenario 5: Insurance Transactions", insights, recommendations)

    else:
        st.info("No matching scenario was selected.")

