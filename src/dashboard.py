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
        # Use primary currency for averages
        if 'currency' in df.columns and not df.empty:
            primary_currency = df['currency'].mode()[0] if len(df['currency'].mode()) > 0 else 'SAR'
            symbol = CURRENCY_SYMBOLS.get(primary_currency, primary_currency)
            if primary_currency == 'SAR':
                st.metric("Avg Transaction", f"{symbol} {avg_transaction:.2f}")
            else:
                st.metric("Avg Transaction", f"{symbol}{avg_transaction:.2f}")
        else:
            st.metric("Avg Transaction", f"${avg_transaction:.2f}")

    with col4:
        days = (end_date - start_date).days + 1
        total_spent_num = df['amount'].sum()
        avg_per_day = total_spent_num / days if days > 0 else 0
        # Use primary currency for daily average
        if 'currency' in df.columns and not df.empty:
            primary_currency = df['currency'].mode()[0] if len(df['currency'].mode()) > 0 else 'SAR'
            symbol = CURRENCY_SYMBOLS.get(primary_currency, primary_currency)
            if primary_currency == 'SAR':
                st.metric("Avg per Day", f"{symbol} {avg_per_day:.2f}")
            else:
                st.metric("Avg per Day", f"{symbol}{avg_per_day:.2f}")
        else:
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

            # Determine primary currency for formatting
            if 'currency' in df.columns:
                primary_currency = df['currency'].mode()[0] if len(df['currency'].mode()) > 0 else 'SAR'
                symbol = CURRENCY_SYMBOLS.get(primary_currency, primary_currency)
                if primary_currency == 'SAR':
                    format_str = f'{symbol} {{:,.2f}}'
                else:
                    format_str = f'{symbol}{{:,.2f}}'
            else:
                format_str = '${:,.2f}'

            st.dataframe(
                category_summary.style.format({
                    'Total': format_str,
                    'Average': format_str,
                    'Percentage': '{:.1f}%'
                }),
                use_container_width=True
            )

    with col2:
        st.subheader("🏪 Top Merchants")

        merchant_summary = df.groupby('merchant')['amount'].sum().sort_values(ascending=False).head(10)

        # Determine currency for axis label
        if 'currency' in df.columns:
            primary_currency = df['currency'].mode()[0] if len(df['currency'].mode()) > 0 else 'SAR'
            currency_label = CURRENCY_SYMBOLS.get(primary_currency, primary_currency)
        else:
            currency_label = '$'

        fig_merchants = px.bar(
            x=merchant_summary.values,
            y=merchant_summary.index,
            orientation='h',
            labels={'x': f'Amount ({currency_label})', 'y': 'Merchant'}
        )
        fig_merchants.update_layout(height=400, showlegend=False)
        st.plotly_chart(fig_merchants, use_container_width=True)

    st.markdown("---")

    # Monthly comparison (if enough data)
    if (end_date - start_date).days > 30:
        st.subheader("📊 Monthly Analysis")

        tab1, tab2, tab3 = st.tabs(["📈 Month-over-Month", "📉 Category Trends", "📅 Monthly Breakdown"])

        with tab1:
            # Month-over-month comparison
            df['month'] = pd.to_datetime(df['date']).dt.to_period('M').astype(str)
            monthly_totals = df.groupby('month')['amount'].sum().reset_index()
            monthly_totals['month_date'] = pd.to_datetime(monthly_totals['month'])
            monthly_totals = monthly_totals.sort_values('month_date')

            # Calculate MoM change
            monthly_totals['prev_month'] = monthly_totals['amount'].shift(1)
            monthly_totals['change'] = monthly_totals['amount'] - monthly_totals['prev_month']
            monthly_totals['change_pct'] = (monthly_totals['change'] / monthly_totals['prev_month'] * 100).round(1)

            # Bar chart with MoM
            fig_mom = go.Figure()

            fig_mom.add_trace(go.Bar(
                x=monthly_totals['month'],
                y=monthly_totals['amount'],
                name='Total Spending',
                marker_color='lightblue',
                text=monthly_totals['amount'].round(2),
                textposition='outside'
            ))

            fig_mom.update_layout(
                title="Monthly Spending Comparison",
                xaxis_title="Month",
                yaxis_title="Amount",
                height=400,
                showlegend=True
            )

            st.plotly_chart(fig_mom, use_container_width=True)

            # Show change table
            if len(monthly_totals) > 1:
                st.subheader("Month-over-Month Changes")
                mom_display = monthly_totals[['month', 'amount', 'change', 'change_pct']].copy()
                mom_display.columns = ['Month', 'Total', 'Change', 'Change %']
                mom_display = mom_display.dropna()

                if 'currency' in df.columns:
                    primary_currency = df['currency'].mode()[0] if len(df['currency'].mode()) > 0 else 'SAR'
                    symbol = CURRENCY_SYMBOLS.get(primary_currency, primary_currency)
                    if primary_currency == 'SAR':
                        format_str = f'{symbol} {{:,.2f}}'
                    else:
                        format_str = f'{symbol}{{:,.2f}}'
                else:
                    format_str = '${:,.2f}'

                st.dataframe(
                    mom_display.style.format({
                        'Total': format_str,
                        'Change': format_str,
                        'Change %': '{:.1f}%'
                    }).applymap(
                        lambda x: 'color: green' if isinstance(x, (int, float)) and x < 0 else ('color: red' if isinstance(x, (int, float)) and x > 0 else ''),
                        subset=['Change', 'Change %']
                    ),
                    use_container_width=True
                )

        with tab2:
            # Category trends over time
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

        with tab3:
            # Detailed monthly breakdown
            if 'category' in df.columns:
                monthly_breakdown = df.groupby(['month', 'category'])['amount'].sum().unstack(fill_value=0)
                monthly_breakdown['Total'] = monthly_breakdown.sum(axis=1)
                monthly_breakdown = monthly_breakdown.sort_index(ascending=False)

                if 'currency' in df.columns:
                    primary_currency = df['currency'].mode()[0] if len(df['currency'].mode()) > 0 else 'SAR'
                    symbol = CURRENCY_SYMBOLS.get(primary_currency, primary_currency)
                    if primary_currency == 'SAR':
                        format_str = f'{symbol} {{:,.2f}}'
                    else:
                        format_str = f'{symbol}{{:,.2f}}'
                else:
                    format_str = '${:,.2f}'

                st.dataframe(
                    monthly_breakdown.style.format(format_str).background_gradient(cmap='YlOrRd', axis=1),
                    use_container_width=True
                )

    st.markdown("---")

    # Time-based analytics
    st.subheader("⏰ Spending Patterns")

    tab1, tab2, tab3, tab4 = st.tabs(["📅 Day of Week", "🕐 Hour of Day", "🗓️ Heatmap", "💳 Payment Methods"])

    with tab1:
        # Day of week analysis
        df['day_of_week'] = pd.to_datetime(df['date']).dt.day_name()
        df['day_num'] = pd.to_datetime(df['date']).dt.dayofweek

        day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        dow_spending = df.groupby('day_of_week')['amount'].agg(['sum', 'count', 'mean']).reindex(day_order)

        col1, col2 = st.columns(2)

        with col1:
            fig_dow = px.bar(
                x=dow_spending.index,
                y=dow_spending['sum'],
                title="Total Spending by Day of Week",
                labels={'x': 'Day', 'y': 'Total Amount'}
            )
            fig_dow.update_layout(height=350, showlegend=False)
            st.plotly_chart(fig_dow, use_container_width=True)

        with col2:
            fig_dow_count = px.bar(
                x=dow_spending.index,
                y=dow_spending['count'],
                title="Transaction Count by Day of Week",
                labels={'x': 'Day', 'y': 'Number of Transactions'},
                color=dow_spending['count'],
                color_continuous_scale='Viridis'
            )
            fig_dow_count.update_layout(height=350, showlegend=False)
            st.plotly_chart(fig_dow_count, use_container_width=True)

    with tab2:
        # Hour of day analysis
        df['hour'] = pd.to_datetime(df['date']).dt.hour
        hourly_spending = df.groupby('hour')['amount'].agg(['sum', 'count', 'mean'])

        col1, col2 = st.columns(2)

        with col1:
            fig_hour = px.line(
                x=hourly_spending.index,
                y=hourly_spending['sum'],
                title="Spending by Hour of Day",
                labels={'x': 'Hour (24h)', 'y': 'Total Amount'},
                markers=True
            )
            fig_hour.update_layout(height=350)
            st.plotly_chart(fig_hour, use_container_width=True)

        with col2:
            fig_hour_count = px.bar(
                x=hourly_spending.index,
                y=hourly_spending['count'],
                title="Transaction Count by Hour",
                labels={'x': 'Hour (24h)', 'y': 'Number of Transactions'}
            )
            fig_hour_count.update_layout(height=350, showlegend=False)
            st.plotly_chart(fig_hour_count, use_container_width=True)

    with tab3:
        # Spending heatmap (day of week vs week number)
        df_copy = df.copy()
        df_copy['week'] = pd.to_datetime(df_copy['date']).dt.isocalendar().week
        df_copy['year'] = pd.to_datetime(df_copy['date']).dt.year
        df_copy['year_week'] = df_copy['year'].astype(str) + '-W' + df_copy['week'].astype(str).str.zfill(2)

        heatmap_data = df_copy.groupby(['year_week', 'day_of_week'])['amount'].sum().unstack(fill_value=0)
        heatmap_data = heatmap_data.reindex(columns=day_order, fill_value=0)

        # Limit to last 12 weeks for readability
        if len(heatmap_data) > 12:
            heatmap_data = heatmap_data.tail(12)

        fig_heatmap = px.imshow(
            heatmap_data.T,
            labels=dict(x="Week", y="Day of Week", color="Amount"),
            title="Spending Heatmap (Last 12 Weeks)",
            aspect="auto",
            color_continuous_scale='YlOrRd'
        )
        fig_heatmap.update_layout(height=400)
        st.plotly_chart(fig_heatmap, use_container_width=True)

    with tab4:
        # Sender/payment method analysis
        if 'sender' in df.columns and df['sender'].notna().any():
            sender_stats = df.groupby('sender').agg({
                'amount': ['sum', 'count', 'mean']
            }).round(2)
            sender_stats.columns = ['Total Spent', 'Transactions', 'Avg Transaction']
            sender_stats = sender_stats.sort_values('Total Spent', ascending=False)

            col1, col2 = st.columns(2)

            with col1:
                if 'currency' in df.columns:
                    primary_currency = df['currency'].mode()[0] if len(df['currency'].mode()) > 0 else 'SAR'
                    symbol = CURRENCY_SYMBOLS.get(primary_currency, primary_currency)
                    if primary_currency == 'SAR':
                        format_str = f'{symbol} {{:,.2f}}'
                    else:
                        format_str = f'{symbol}{{:,.2f}}'
                else:
                    format_str = '${:,.2f}'

                st.dataframe(
                    sender_stats.style.format({
                        'Total Spent': format_str,
                        'Avg Transaction': format_str
                    }),
                    use_container_width=True
                )

            with col2:
                fig_sender = px.pie(
                    values=sender_stats['Total Spent'],
                    names=sender_stats.index,
                    title="Spending by Payment Method",
                    hole=0.4
                )
                fig_sender.update_layout(height=400)
                st.plotly_chart(fig_sender, use_container_width=True)
        else:
            st.info("No payment method information available in the data.")

    st.markdown("---")

    # Currency breakdown (if multiple currencies)
    if 'currency' in df.columns and len(df['currency'].unique()) > 1:
        st.subheader("💱 Currency Breakdown")

        col1, col2, col3 = st.columns(3)

        currency_stats = df.groupby('currency').agg({
            'amount': ['sum', 'count', 'mean']
        }).round(2)
        currency_stats.columns = ['Total', 'Count', 'Average']

        with col1:
            fig_currency = px.pie(
                values=currency_stats['Total'],
                names=currency_stats.index,
                title="Spending by Currency",
                hole=0.4
            )
            fig_currency.update_layout(height=300)
            st.plotly_chart(fig_currency, use_container_width=True)

        with col2:
            # Currency breakdown table
            st.markdown("### Currency Summary")
            currency_display = currency_stats.copy()
            st.dataframe(currency_display, use_container_width=True)

        with col3:
            # Transaction count by currency
            fig_currency_count = px.bar(
                x=currency_stats.index,
                y=currency_stats['Count'],
                title="Transactions by Currency",
                labels={'x': 'Currency', 'y': 'Transaction Count'}
            )
            fig_currency_count.update_layout(height=300, showlegend=False)
            st.plotly_chart(fig_currency_count, use_container_width=True)

        st.markdown("---")

    # Merchant analysis
    st.subheader("🏪 Merchant Insights")

    tab1, tab2, tab3 = st.tabs(["📊 Top Merchants", "🔄 Frequency", "📈 Spending Trends"])

    with tab1:
        merchant_stats = df.groupby('merchant').agg({
            'amount': ['sum', 'count', 'mean', 'min', 'max']
        }).round(2)
        merchant_stats.columns = ['Total', 'Count', 'Average', 'Min', 'Max']
        merchant_stats = merchant_stats.sort_values('Total', ascending=False).head(20)

        if 'currency' in df.columns:
            primary_currency = df['currency'].mode()[0] if len(df['currency'].mode()) > 0 else 'SAR'
            symbol = CURRENCY_SYMBOLS.get(primary_currency, primary_currency)
            if primary_currency == 'SAR':
                format_str = f'{symbol} {{:,.2f}}'
            else:
                format_str = f'{symbol}{{:,.2f}}'
        else:
            format_str = '${:,.2f}'

        st.dataframe(
            merchant_stats.style.format({
                'Total': format_str,
                'Average': format_str,
                'Min': format_str,
                'Max': format_str
            }).background_gradient(subset=['Total'], cmap='YlOrRd'),
            use_container_width=True,
            height=400
        )

    with tab2:
        # Merchant frequency (most visited)
        merchant_freq = df['merchant'].value_counts().head(15)

        fig_freq = px.bar(
            x=merchant_freq.index,
            y=merchant_freq.values,
            title="Most Frequent Merchants (Top 15)",
            labels={'x': 'Merchant', 'y': 'Number of Transactions'}
        )
        fig_freq.update_layout(height=400, showlegend=False, xaxis_tickangle=-45)
        st.plotly_chart(fig_freq, use_container_width=True)

    with tab3:
        # Merchant spending over time (top 5 merchants)
        top_merchants = df.groupby('merchant')['amount'].sum().nlargest(5).index

        if 'month' not in df.columns:
            df['month'] = pd.to_datetime(df['date']).dt.to_period('M').astype(str)

        merchant_monthly = df[df['merchant'].isin(top_merchants)].groupby(['month', 'merchant'])['amount'].sum().reset_index()

        fig_merchant_trend = px.line(
            merchant_monthly,
            x='month',
            y='amount',
            color='merchant',
            title="Top 5 Merchants - Spending Trends",
            markers=True
        )
        fig_merchant_trend.update_layout(height=400)
        st.plotly_chart(fig_merchant_trend, use_container_width=True)

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
