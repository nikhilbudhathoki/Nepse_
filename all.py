import streamlit as st
import pandas as pd
import plotly.express as px
import os

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
    weekly_avg['Week_Label'] = weekly_avg['Year'].astype(str) + '-W' + weekly_avg['Week'].astype(str)
    monthly_avg = df.groupby(['Year', 'Month'])[column_name].mean().reset_index()
    monthly_avg['Month_Label'] = monthly_avg['Year'].astype(str) + '-M' + monthly_avg['Month'].astype(int).apply(lambda x: f'{x:02d}')
    yearly_avg = df.groupby('Year')[column_name].mean().reset_index()

    return {
        'daily': daily_avg,
        'weekly': weekly_avg,
        'monthly': monthly_avg,
        'yearly': yearly_avg
    }

# Main app function
def main():
    st.set_page_config(page_title="NEPSE Sector Analysis", layout="wide")
    st.title("📊 NEPSE Sector Analysis")

    # Load data
    if os.path.exists(PERSISTENT_FILE):
        raw_data = pd.read_csv(PERSISTENT_FILE)
    else:
        uploaded_file = st.file_uploader("📁 Upload NEPSE CSV file", type=['csv'])
        if uploaded_file is not None:
            raw_data = pd.read_csv(uploaded_file)
        else:
            st.warning("Please upload a CSV file to proceed.")
            return

    if 'raw_data' not in st.session_state:
        st.session_state.raw_data = raw_data

    data = st.session_state.raw_data
    edited_data = st.data_editor(data, num_rows="dynamic", key="data_editor")

    if st.button("💾 Save Changes", type="primary"):
        st.session_state.raw_data = edited_data
        edited_data.to_csv(PERSISTENT_FILE, index=False)
        st.success(f"Changes saved to {PERSISTENT_FILE}!")

    # Define sectors
    sectors = {
        "Nepse": edited_data[['Date', 'Nepse']],
        "Commercial Banking": edited_data[['Date', 'C Banking']],
        "Development Banking": edited_data[['Date', 'Dev Banking']],
        "Finance": edited_data[['Date', 'Finance']],
        "Micro-Finance": edited_data[['Date', 'Micro- Finance']],
        "Investment": edited_data[['Date', 'Investment']],
        "Life Insurance": edited_data[['Date', 'Life- Insurance']],
        "Non-life Insurance": edited_data[['Date', 'Non-life insurance']],
        "Hotels": edited_data[['Date', 'Hotels']],
        "Others": edited_data[['Date', 'Others']],
        "Trading": edited_data[['Date', 'Trading']],
        "Manufacture": edited_data[['Date', 'Manufacture']],
        "Hydropower": edited_data[['Date', 'Hydropower']]
    }

    tabs = st.tabs(["📈 Sector Analysis", "📊 Comparison"])

    # Sector Analysis Tab
    with tabs[0]:
        selected_sector = st.selectbox("🏢 Select Sector", list(sectors.keys()), index=0)
        sector_data = sectors[selected_sector]
        averages = calculate_nepse_averages(sector_data, sector_data.columns[1])
        chart_type = st.selectbox("📊 Select Chart Type", ["Daily", "Weekly", "Monthly", "Yearly"], index=2)

        if chart_type == "Daily":
            line_data = averages['daily']
            x_axis = 'Date'
        elif chart_type == "Weekly":
            line_data = averages['weekly']
            x_axis = 'Week_Label'
        elif chart_type == "Monthly":
            line_data = averages['monthly']
            x_axis = 'Month_Label'
        else:
            line_data = averages['yearly']
            x_axis = 'Year'

        fig = px.line(line_data, x=x_axis, y=sector_data.columns[1], title=f"{chart_type} Line Chart")
        fig.update_layout(
            xaxis=dict(rangeslider=dict(visible=True)),  # Enable range slider for zoom
            yaxis=dict(title=sector_data.columns[1]),
            title=dict(x=0.5),  # Center-align title
            dragmode="zoom",  # Enable drag zoom functionality
            xaxis_title="Date",
            yaxis_title="Price"
        )
        st.plotly_chart(fig)

    # Comparison Tab
    with tabs[1]:
        st.write("## 📊 Sector Comparison")
        average_type = st.selectbox("Select Average Type", ["Daily", "Weekly", "Monthly"], index=0)
        sector_options = list(sectors.keys()) + ["All Sectors"]
        selected_sectors = st.multiselect("Select Sectors for Comparison", options=sector_options, default=["Nepse"])

        comparison_data = pd.DataFrame()

        if "All Sectors" in selected_sectors:
            for sector_name, sector_data in sectors.items():
                averages = calculate_nepse_averages(sector_data, sector_data.columns[1])
                avg_data = averages[average_type.lower()]
                key_column = 'Date' if average_type == "Daily" else f"{average_type.lower()}_Label"
                avg_data.rename(columns={sector_data.columns[1]: sector_name, key_column: 'Merge_Key'}, inplace=True)
                if comparison_data.empty:
                    comparison_data = avg_data[['Merge_Key', sector_name]]
                else:
                    comparison_data = comparison_data.merge(avg_data[['Merge_Key', sector_name]], on='Merge_Key', how='outer')
        else:
            for sector in selected_sectors:
                sector_data = sectors[sector]
                averages = calculate_nepse_averages(sector_data, sector_data.columns[1])
                avg_data = averages[average_type.lower()]
                key_column = 'Date' if average_type == "Daily" else f"{average_type.lower()}_Label"
                avg_data.rename(columns={sector_data.columns[1]: sector, key_column: 'Merge_Key'}, inplace=True)
                if comparison_data.empty:
                    comparison_data = avg_data[['Merge_Key', sector]]
                else:
                    comparison_data = comparison_data.merge(avg_data[['Merge_Key', sector]], on='Merge_Key', how='outer')

        if not comparison_data.empty:
            melted_data = comparison_data.melt(id_vars=['Merge_Key'], var_name="Sector", value_name="Average")
            fig = px.line(melted_data, x="Merge_Key", y="Average", color="Sector", title="Sector Comparison")
            fig.update_layout(
                xaxis=dict(rangeslider=dict(visible=True)),  # Enable range slider for zoom
                yaxis=dict(title="Average"),
                title=dict(x=0.5),  # Center-align title
                dragmode="zoom"  # Enable drag zoom functionality
            )
            st.plotly_chart(fig)

if __name__ == "__main__":
    main()
