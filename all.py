import streamlit as st
import pandas as pd
import plotly.express as px
import os

# File to persist data
PERSISTENT_FILE = "nepse_data.csv"

# Function to calculate daily, weekly, monthly, and yearly averages
def calculate_nepse_averages(df, column_name):
    df['Date'] = pd.to_datetime(df['Date'])
    df['Week'] = df['Date'].dt.isocalendar().week
    df['Year'] = df['Date'].dt.isocalendar().year
    df['Month'] = df['Date'].dt.month

    # Daily averages
    daily_avg = df.groupby('Date')[column_name].mean().reset_index()

    # Weekly averages
    weekly_avg = df.groupby(['Year', 'Week'])[column_name].mean().reset_index()
    weekly_avg['Week_Label'] = weekly_avg['Year'].astype(str) + '-W' + weekly_avg['Week'].astype(str)

    # Monthly averages
    monthly_avg = df.groupby(['Year', 'Month'])[column_name].mean().reset_index()
    monthly_avg['Month_Label'] = (
        monthly_avg['Year'].astype(str) + '-M' + monthly_avg['Month'].astype(int).apply(lambda x: f'{x:02d}')
    )

    # Yearly averages
    yearly_avg = df.groupby('Year')[column_name].mean().reset_index()

    return {
        'daily': daily_avg,
        'weekly': weekly_avg,
        'monthly': monthly_avg,
        'yearly': yearly_avg
    }

# Streamlit app
def main():
    st.set_page_config(page_title="NEPSE Sector Analysis", layout="wide")
    st.title("📊 NEPSE Sector Analysis")

    # Check if the persistent file exists
    if os.path.exists(PERSISTENT_FILE):
        st.write("### Loading saved data...")
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
    st.write("### Editable Raw Data")
    edited_data = st.data_editor(
        data,
        num_rows="dynamic",  # Allows adding new rows
        key="data_editor"
    )

    # Save Changes button
    if st.button("💾 Save Changes", type="primary"):
        st.session_state.raw_data = edited_data
        edited_data.to_csv(PERSISTENT_FILE, index=False)  # Save to file
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

    # Select sector
    selected_sector = st.selectbox("🏢 Select Sector", list(sectors.keys()), index=0)
    sector_data = sectors[selected_sector]

    # Calculate averages
    averages = calculate_nepse_averages(sector_data, sector_data.columns[1])

    # Selector for bar chart type
    chart_type = st.selectbox(
        "📊 Select Chart Type for Bar Graph",
        options=["Daily", "Weekly", "Monthly", "Yearly"],
        index=2  # Default to Monthly
    )

    if chart_type == "Daily":
        bar_data = averages['daily']
        x_axis = 'Date'
        title = f'Daily Distribution for {selected_sector}'
    elif chart_type == "Weekly":
        bar_data = averages['weekly']
        x_axis = 'Week_Label'
        title = f'Weekly Distribution for {selected_sector}'
    elif chart_type == "Monthly":
        bar_data = averages['monthly']
        x_axis = 'Month_Label'
        title = f'Monthly Distribution for {selected_sector}'
    else:
        bar_data = averages['yearly']
        x_axis = 'Year'
        title = f'Yearly Distribution for {selected_sector}'

    # Display Bar Chart
    st.write(f"### 📊 {chart_type} Bar Chart for {selected_sector}")
    bar_chart = px.bar(bar_data, x=x_axis, y=sector_data.columns[1],
                       title=title,
                       labels={x_axis: chart_type, sector_data.columns[1]: 'Percentage Change'})
    st.plotly_chart(bar_chart)

    # Display Line Charts
    st.write(f"### 📅 Daily Averages for {selected_sector}")
    st.write(averages['daily'])
    daily_chart = px.line(averages['daily'], x='Date', y=sector_data.columns[1],
                          title=f'Daily Averages for {selected_sector}',
                          labels={'Date': 'Date', sector_data.columns[1]: 'Percentage Change'})
    st.plotly_chart(daily_chart)

    st.write(f"### 📅 Weekly Averages for {selected_sector}")
    st.write(averages['weekly'])
    weekly_chart = px.line(averages['weekly'], x='Week_Label', y=sector_data.columns[1],
                           title=f'Weekly Averages for {selected_sector}',
                           labels={'Week_Label': 'Week', sector_data.columns[1]: 'Percentage Change'})
    st.plotly_chart(weekly_chart)

    st.write(f"### 📅 Monthly Averages for {selected_sector}")
    st.write(averages['monthly'])
    monthly_chart = px.line(averages['monthly'], x='Month_Label', y=sector_data.columns[1],
                             title=f'Monthly Averages for {selected_sector}',
                             labels={'Month_Label': 'Month', sector_data.columns[1]: 'Percentage Change'})
    st.plotly_chart(monthly_chart)

    st.write(f"### 📅 Yearly Averages for {selected_sector}")
    st.write(averages['yearly'])
    yearly_chart = px.line(averages['yearly'], x='Year', y=sector_data.columns[1],
                            title=f'Yearly Averages for {selected_sector}',
                            labels={'Year': 'Year', sector_data.columns[1]: 'Percentage Change'})
    st.plotly_chart(yearly_chart)

if __name__ == "__main__":
    main()
