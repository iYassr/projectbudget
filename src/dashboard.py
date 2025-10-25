"""
Dashboard - Interactive Streamlit dashboard for expense visualization
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from database import ExpenseDatabase
from analyzer import ExpenseAnalyzer
import calendar


# Currency symbol mapping
CURRENCY_SYMBOLS = {
    'SAR': 'SAR',
    'USD': '$',
    'EUR': '€',
    'GBP': '£',
    'INR': '₹'
}


def format_amount(row):
    """Format amount with appropriate currency symbol"""
    amount = row['amount']
    currency = row.get('currency', 'SAR')
    symbol = CURRENCY_SYMBOLS.get(currency, currency)

    if currency == 'SAR':
        return f"{symbol} {amount:,.2f}"
    else:
        return f"{symbol}{amount:,.2f}"


# Page configuration
st.set_page_config(
    page_title="Expense Tracker Dashboard",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize database and analyzer
@st.cache_resource
def get_database():
    return ExpenseDatabase("data/expenses.db")

db = get_database()
analyzer = ExpenseAnalyzer(db)


def main():
    """Main dashboard application"""

    # Sidebar
    st.sidebar.title("💰 Expense Tracker")
    st.sidebar.markdown("---")

    # Date range selector
    st.sidebar.subheader("📅 Date Range")

    date_option = st.sidebar.selectbox(
        "Select Period",
        ["All Time", "This Month", "Last Month", "Last 3 Months", "Last 6 Months", "Custom Range"]
    )

    if date_option == "All Time":
        # Get all expenses from database
        start_date = datetime(2020, 1, 1)  # Far back enough
        end_date = datetime.now()
    elif date_option == "This Month":
        now = datetime.now()
        start_date = datetime(now.year, now.month, 1)
        end_date = now
    elif date_option == "Last Month":
        now = datetime.now()
        first_day = datetime(now.year, now.month, 1)
        start_date = (first_day - timedelta(days=1)).replace(day=1)
        end_date = first_day - timedelta(days=1)
    elif date_option == "Last 3 Months":
        end_date = datetime.now()
        start_date = end_date - timedelta(days=90)
    elif date_option == "Last 6 Months":
        end_date = datetime.now()
        start_date = end_date - timedelta(days=180)
    else:  # Custom Range
        col1, col2 = st.sidebar.columns(2)
        with col1:
            start_date = st.date_input("Start Date", datetime.now() - timedelta(days=30))
        with col2:
            end_date = st.date_input("End Date", datetime.now())

    # Get expenses for selected period
    df = db.get_expenses(
        start_date=start_date.strftime("%Y-%m-%d"),
        end_date=end_date.strftime("%Y-%m-%d")
    )

    # Main content
    st.title("📊 Expense Dashboard")

    if df.empty:
        st.warning("No expenses found for the selected period. Please add some expenses first!")
        st.info("""
        To add expenses:
        1. Extract SMS messages: `python src/sms_extractor.py --start-date YYYY-MM-DD --end-date YYYY-MM-DD`
        2. The expenses will be automatically parsed and added to the database
        """)
        return

    # Summary cards
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        # Group by currency for total spent
        if 'currency' in df.columns:
            currency_totals = df.groupby('currency')['amount'].sum()
            if len(currency_totals) == 1:
                currency = currency_totals.index[0]
                symbol = CURRENCY_SYMBOLS.get(currency, currency)
                total_spent = currency_totals.values[0]
                if currency == 'SAR':
                    st.metric("Total Spent", f"{symbol} {total_spent:,.2f}")
                else:
                    st.metric("Total Spent", f"{symbol}{total_spent:,.2f}")
            else:
                # Multiple currencies - show all
                st.metric("Total Spent", "Mixed")
                for currency, total in currency_totals.items():
                    symbol = CURRENCY_SYMBOLS.get(currency, currency)
                    if currency == 'SAR':
                        st.caption(f"{symbol} {total:,.2f}")
                    else:
                        st.caption(f"{symbol}{total:,.2f}")
        else:
            total_spent = df['amount'].sum()
            st.metric("Total Spent", f"${total_spent:,.2f}")

    with col2:
        transaction_count = len(df)
        st.metric("Transactions", f"{transaction_count:,}")

    with col3:
        avg_transaction = df['amount'].mean()
        st.metric("Avg Transaction", f"${avg_transaction:.2f}")

    with col4:
        days = (end_date - start_date).days + 1
        total_spent_num = df['amount'].sum()
        avg_per_day = total_spent_num / days if days > 0 else 0
        st.metric("Avg per Day", f"${avg_per_day:.2f}")

    st.markdown("---")

    # Two column layout
    col_left, col_right = st.columns([2, 1])

    with col_left:
        # Spending over time
        st.subheader("📈 Spending Over Time")

        daily_spending = df.groupby(df['date'].dt.date)['amount'].sum().reset_index()
        daily_spending.columns = ['Date', 'Amount']

        fig_timeline = px.line(
            daily_spending,
            x='Date',
            y='Amount',
            title="Daily Spending",
            markers=True
        )
        fig_timeline.update_layout(height=400)
        st.plotly_chart(fig_timeline, use_container_width=True)

    with col_right:
        # Category pie chart
        st.subheader("🥧 Spending by Category")

        if 'category' in df.columns:
            category_data = df.groupby('category')['amount'].sum().reset_index()
            category_data = category_data.sort_values('amount', ascending=False)

            fig_pie = px.pie(
                category_data,
                values='amount',
                names='category',
                hole=0.4
            )
            fig_pie.update_layout(height=400)
            st.plotly_chart(fig_pie, use_container_width=True)

    st.markdown("---")

    # Category breakdown
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("📊 Top Categories")

        if 'category' in df.columns:
            category_summary = df.groupby('category').agg({
                'amount': ['sum', 'count', 'mean']
            }).round(2)
            category_summary.columns = ['Total', 'Count', 'Average']
            category_summary = category_summary.sort_values('Total', ascending=False)

            # Add percentage
            category_summary['Percentage'] = (category_summary['Total'] / category_summary['Total'].sum() * 100).round(1)

            st.dataframe(
                category_summary.style.format({
                    'Total': '${:,.2f}',
                    'Average': '${:,.2f}',
                    'Percentage': '{:.1f}%'
                }),
                use_container_width=True
            )

    with col2:
        st.subheader("🏪 Top Merchants")

        merchant_summary = df.groupby('merchant')['amount'].sum().sort_values(ascending=False).head(10)

        fig_merchants = px.bar(
            x=merchant_summary.values,
            y=merchant_summary.index,
            orientation='h',
            labels={'x': 'Amount ($)', 'y': 'Merchant'}
        )
        fig_merchants.update_layout(height=400, showlegend=False)
        st.plotly_chart(fig_merchants, use_container_width=True)

    st.markdown("---")

    # Category trends (if enough data)
    if (end_date - start_date).days > 30:
        st.subheader("📉 Category Trends")

        df['month'] = pd.to_datetime(df['date']).dt.to_period('M').astype(str)

        if 'category' in df.columns:
            monthly_category = df.groupby(['month', 'category'])['amount'].sum().reset_index()

            fig_trends = px.line(
                monthly_category,
                x='month',
                y='amount',
                color='category',
                title="Monthly Spending by Category",
                markers=True
            )
            fig_trends.update_layout(height=400)
            st.plotly_chart(fig_trends, use_container_width=True)

    st.markdown("---")

    # Recent transactions
    st.subheader("📝 Recent Transactions")

    # Add filters
    col1, col2, col3 = st.columns(3)

    with col1:
        category_filter = st.multiselect(
            "Filter by Category",
            options=df['category'].unique().tolist() if 'category' in df.columns else [],
            default=[]
        )

    with col2:
        merchant_filter = st.multiselect(
            "Filter by Merchant",
            options=df['merchant'].unique().tolist(),
            default=[]
        )

    with col3:
        min_amount = st.number_input("Min Amount", value=0.0, step=10.0)

    # Apply filters
    filtered_df = df.copy()

    if category_filter:
        filtered_df = filtered_df[filtered_df['category'].isin(category_filter)]

    if merchant_filter:
        filtered_df = filtered_df[filtered_df['merchant'].isin(merchant_filter)]

    if min_amount > 0:
        filtered_df = filtered_df[filtered_df['amount'] >= min_amount]

    # Display table
    display_cols = ['date', 'merchant', 'amount', 'category']
    if 'category' not in filtered_df.columns:
        display_cols = ['date', 'merchant', 'amount']
    if 'currency' in filtered_df.columns and 'currency' not in display_cols:
        display_cols.insert(3, 'currency')

    # Format the display
    display_df = filtered_df[display_cols].sort_values('date', ascending=False).head(50).copy()

    # Add formatted amount column
    if 'currency' in display_df.columns:
        display_df['formatted_amount'] = display_df.apply(format_amount, axis=1)
        # Rearrange columns to show formatted_amount instead of amount
        cols_to_show = [col for col in display_cols if col != 'amount' and col != 'currency']
        cols_to_show.insert(2, 'formatted_amount')
        display_df = display_df[cols_to_show]
        display_df.columns = [col.replace('formatted_amount', 'Amount').title() for col in display_df.columns]

        st.dataframe(
            display_df.style.format({
                'Date': lambda x: x.strftime('%Y-%m-%d %H:%M') if pd.notnull(x) else ''
            }),
            use_container_width=True,
            height=400
        )
    else:
        st.dataframe(
            display_df.style.format({
                'amount': '${:,.2f}',
                'date': lambda x: x.strftime('%Y-%m-%d %H:%M') if pd.notnull(x) else ''
            }),
            use_container_width=True,
            height=400
        )

    # Export button
    st.markdown("---")

    if st.button("📥 Export to CSV"):
        csv = filtered_df.to_csv(index=False)
        st.download_button(
            label="Download CSV",
            data=csv,
            file_name=f"expenses_{start_date.strftime('%Y%m%d')}_{end_date.strftime('%Y%m%d')}.csv",
            mime="text/csv"
        )

    # Sidebar statistics
    st.sidebar.markdown("---")
    st.sidebar.subheader("📊 Quick Stats")

    if not df.empty:
        top_category = df.groupby('category')['amount'].sum().idxmax() if 'category' in df.columns else 'N/A'
        top_merchant = df.groupby('merchant')['amount'].sum().idxmax()

        st.sidebar.metric("Top Category", top_category)
        st.sidebar.metric("Top Merchant", top_merchant)

        # Anomalies
        anomalies = analyzer.detect_anomalies()
        if anomalies:
            st.sidebar.warning(f"⚠️ {len(anomalies)} unusual transactions detected")


if __name__ == "__main__":
    main()
