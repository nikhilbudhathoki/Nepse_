import streamlit as st
import pandas as pd
import plotly.express as px
import os

# Set page configuration
st.set_page_config(page_title="NEPSE Sector Analysis", layout="wide")

# Custom CSS for styling and dynamic button background
st.markdown(
    """
    <style>
    body {
        background-color: #1f1f1f;
        color: #f5f5f5;
        font-family: 'Arial', sans-serif;
    }
    .stButton>button {
        color: white;
        border: none;
        padding: 12px 24px;
        border-radius: 12px;
        box-shadow: 0px 6px 8px #444;
        transition: background-color 0.3s, transform 0.3s ease-in-out;
    }
    .stButton>button:hover {
        transform: translateY(-4px);
    }
    </style>
    """,
    unsafe_allow_html=True
)

# File to persist data
PERSISTENT_FILE = "nepse_data.csv"

# Function to calculate daily, weekly, monthly, and yearly averages
def calculate_nepse_averages(df, column_name):
    df = df.copy()
    df['Date'] = pd.to_datetime(df['Date'])
    df['Week'] = df['Date'].dt.isocalendar().week
    df['Year'] = df['Date'].dt.isocalendar().year
    df['Month'] = df['Date'].dt.month

    daily_avg = df.groupby('Date')[column_name].mean().reset_index()
    weekly_avg = df.groupby(['Year', 'Week'])[column_name].mean().reset_index()
    weekly_avg['Merge_Key'] = weekly_avg['Year'].astype(str) + '-W' + weekly_avg['Week'].astype(str)
    monthly_avg = df.groupby(['Year', 'Month'])[column_name].mean().reset_index()
    monthly_avg['Merge_Key'] = monthly_avg['Year'].astype(str) + '-M' + monthly_avg['Month'].apply(lambda x: f'{x:02d}')
    yearly_avg = df.groupby('Year')[column_name].mean().reset_index()

    return {
        'daily': daily_avg,
        'weekly': weekly_avg,
        'monthly': monthly_avg,
        'yearly': yearly_avg
    }

# Main app function
def main():
    st.markdown("<h1>\ud83d\udcca NEPSE Sector Analysis</h1>", unsafe_allow_html=True)

    # Load data
    if os.path.exists(PERSISTENT_FILE):
        raw_data = pd.read_csv(PERSISTENT_FILE)
    else:
        uploaded_file = st.file_uploader("\ud83d\udcc1 Upload NEPSE CSV file", type=['csv'])
        if uploaded_file is not None:
            raw_data = pd.read_csv(uploaded_file)
        else:
            st.warning("Please upload a CSV file to proceed.")
            return

    if 'raw_data' not in st.session_state:
        st.session_state.raw_data = raw_data

    data = st.session_state.raw_data
    edited_data = st.data_editor(data, num_rows="dynamic", key="data_editor")

    if st.button("\ud83d\udd12 Save Changes", type="primary"):
        st.session_state.raw_data = edited_data
        edited_data.to_csv(PERSISTENT_FILE, index=False)
        st.success(f"Changes saved to {PERSISTENT_FILE}!")

    # Define sectors
    sectors = {
        "Nepse": edited_data[['Date', 'Nepse']].dropna(),
        "Commercial Banking": edited_data[['Date', 'C Banking']].dropna(),
        "Development Banking": edited_data[['Date', 'Dev Banking']].dropna(),
        "Finance": edited_data[['Date', 'Finance']].dropna(),
        "Micro-Finance": edited_data[['Date', 'Micro- Finance']].dropna(),
        "Investment": edited_data[['Date', 'Investment']].dropna(),
        "Life Insurance": edited_data[['Date', 'Life- Insurance']].dropna(),
        "Non-life Insurance": edited_data[['Date', 'Non-life insurance']].dropna(),
        "Hotels": edited_data[['Date', 'Hotels']].dropna(),
        "Others": edited_data[['Date', 'Others']].dropna(),
        "Trading": edited_data[['Date', 'Trading']].dropna(),
        "Manufacture": edited_data[['Date', 'Manufacture']].dropna(),
        "Hydropower": edited_data[['Date', 'Hydropower']].dropna()
    }

    tabs = st.tabs(["\ud83d\udcca Sector Analysis", "\ud83d\udcc8 Comparison"])

    # Sector Analysis Tab
    with tabs[0]:
        selected_sector = st.selectbox("\ud83c\udfe2 Select Sector", list(sectors.keys()), index=0)
        sector_data = sectors[selected_sector]
        averages = calculate_nepse_averages(sector_data, sector_data.columns[1])
        chart_type = st.selectbox("\ud83d\udcca Select Chart Type", ["Daily", "Weekly", "Monthly", "Yearly"], index=2)

        line_data = averages[chart_type.lower()]
        x_axis = 'Date' if chart_type == "Daily" else 'Merge_Key'

        fig = px.line(line_data, x=x_axis, y=sector_data.columns[1], title=f"{chart_type} Line Chart")
        fig.update_layout(
            xaxis=dict(rangeslider=dict(visible=True)),
            yaxis=dict(title=sector_data.columns[1]),
            title=dict(x=0.5),
            dragmode="zoom"
        )
        st.plotly_chart(fig)

    # Comparison Tab
    with tabs[1]:
        st.write("## \ud83d\udcc8 Sector Comparison")
        average_type = st.selectbox("Select Average Type", ["Daily", "Weekly", "Monthly"], index=0)
        sector_options = list(sectors.keys()) + ["All Sectors"]
        selected_sectors = st.multiselect("Select Sectors for Comparison", options=sector_options, default=["Nepse"])

        comparison_data = pd.DataFrame()

        for sector in selected_sectors:
            if sector == "All Sectors":
                for sector_name, sector_data in sectors.items():
                    averages = calculate_nepse_averages(sector_data, sector_data.columns[1])
                    avg_data = averages[average_type.lower()]
                    avg_data.rename(columns={avg_data.columns[1]: sector_name, 'Date': 'Merge_Key'}, inplace=True)
                    comparison_data = avg_data if comparison_data.empty else comparison_data.merge(avg_data, on='Merge_Key', how='outer')
            else:
                sector_data = sectors[sector]
                averages = calculate_nepse_averages(sector_data, sector_data.columns[1])
                avg_data = averages[average_type.lower()]
                avg_data.rename(columns={avg_data.columns[1]: sector, 'Date': 'Merge_Key'}, inplace=True)
                comparison_data = avg_data if comparison_data.empty else comparison_data.merge(avg_data, on='Merge_Key', how='outer')

        if not comparison_data.empty:
            melted_data = comparison_data.melt(id_vars=['Merge_Key'], var_name="Sector", value_name="Average")
            fig = px.line(melted_data, x="Merge_Key", y="Average", color="Sector", title="Sector Comparison")
            fig.update_layout(
                xaxis=dict(rangeslider=dict(visible=True)),
                yaxis=dict(title="Average"),
                title=dict(x=0.5),
                dragmode="zoom"
            )
            st.plotly_chart(fig)

if __name__ == "__main__":
    main()
