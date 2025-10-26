# Dashboard Features

## Overview
The enhanced expense tracker dashboard now includes comprehensive analytics and visualizations to help you understand your spending patterns better.

## 📊 Summary Statistics (Top Cards)

1. **Total Spent** - Shows total spending with proper currency symbols
   - Supports multiple currencies (SAR, USD, EUR, GBP, INR)
   - Shows breakdown if multiple currencies present

2. **Transactions** - Total number of transactions in selected period

3. **Avg Transaction** - Average transaction amount

4. **Avg per Day** - Average daily spending

## 📈 Monthly Analysis (3 Tabs)

### Month-over-Month Comparison
- **Bar chart** showing total spending per month
- **Change table** displaying:
  - Month
  - Total spending
  - Change from previous month (absolute)
  - Change percentage
  - Color-coded: Green for decrease, Red for increase

### Category Trends
- Line chart showing how spending in each category changes over time
- Helps identify seasonal patterns or category-specific trends

### Monthly Breakdown
- Heatmap table showing spending by month and category
- Color-coded intensity (Yellow to Red) for easy pattern recognition
- Shows total column for each month

## ⏰ Spending Patterns (4 Tabs)

### Day of Week Analysis
- **Total spending by day** - Bar chart showing which days you spend most
- **Transaction count by day** - See which days have most transactions
- Helps identify weekly spending patterns

### Hour of Day Analysis
- **Spending by hour** - Line chart showing spending throughout the day
- **Transaction count by hour** - Bar chart of transaction frequency
- Useful for understanding when you make most purchases

### Spending Heatmap
- 2D heatmap showing spending by week and day
- Shows last 12 weeks for readability
- Color intensity indicates amount spent
- Great for spotting weekly patterns

### Payment Methods
- Table showing spending by sender (AlRajhiBank, Barq, STC Pay, etc.)
- Metrics: Total spent, transaction count, average transaction
- Pie chart showing distribution across payment methods

## 💱 Currency Breakdown
*Only shown if you have transactions in multiple currencies*

- **Pie chart** - Spending distribution by currency
- **Summary table** - Total, count, and average per currency
- **Bar chart** - Transaction count by currency

## 🏪 Merchant Insights (3 Tabs)

### Top Merchants
- Table showing top 20 merchants by total spending
- Columns: Total, Count, Average, Min, Max
- Color gradient highlighting biggest spenders
- Helps identify where most money goes

### Frequency Analysis
- Bar chart of most frequently visited merchants (top 15)
- Shows transaction count, not amount
- Identifies your regular merchants

### Spending Trends
- Line chart tracking top 5 merchants over time
- Shows monthly spending per merchant
- Helps spot trends (increasing/decreasing with specific merchants)

## 📊 Category Breakdown

### Top Categories
- Table with:
  - Total spending per category
  - Transaction count
  - Average transaction
  - Percentage of total spending
- Sorted by total spending

### Top Merchants Chart
- Horizontal bar chart of top 10 merchants
- Quick visual of biggest merchants

## 📈 Timeline Charts

### Daily Spending
- Line chart showing spending over time
- Helps spot spending spikes or trends

### Spending by Category (Pie Chart)
- Donut chart showing category distribution
- Interactive - hover for details

## 📝 Recent Transactions

### Filters
- **Category filter** - Multi-select dropdown
- **Merchant filter** - Multi-select dropdown
- **Minimum amount** - Number input

### Transaction Table
- Shows last 50 transactions (filtered)
- Columns: Date, Merchant, Amount (with currency), Category
- Properly formatted with currency symbols
- Sorted by date (newest first)

### Export
- **Export to CSV** button
- Downloads filtered transactions
- Filename includes date range

## 📊 Sidebar Quick Stats

- **Top Category** - Category with highest spending
- **Top Merchant** - Merchant with highest spending
- **Anomaly Detection** - Warning if unusual transactions detected

## 🎯 Date Range Options

- All Time
- This Month
- Last Month
- Last 3 Months
- Last 6 Months
- Custom Range (with date pickers)

## 📱 Interactive Features

- All charts are interactive (Plotly)
- Hover over charts for detailed information
- Click legend items to show/hide data
- Zoom and pan on charts
- Download charts as images

## 🎨 Visual Enhancements

- Color-coded metrics (green = saving, red = spending more)
- Heatmaps with intensity gradients
- Consistent color schemes across charts
- Professional, clean layout
- Responsive design (works on different screen sizes)

## 📊 Analytics Insights You Can Derive

1. **Spending Habits**
   - Which days you spend most (weekend vs weekday)
   - What time of day you make purchases
   - Weekly patterns and trends

2. **Budget Planning**
   - Month-over-month changes help set realistic budgets
   - Category breakdowns show where to cut spending
   - Average per day helps with daily budgets

3. **Merchant Behavior**
   - Identify your most expensive merchants
   - See which merchants you visit most frequently
   - Track if spending with specific merchants is increasing

4. **Currency Management**
   - See how much you spend in each currency
   - Useful for expats or frequent travelers

5. **Payment Method Insights**
   - Which payment method you use most
   - Compare spending across different banks/wallets

## 🚀 How to Use

1. Run the dashboard:
   ```bash
   streamlit run src/dashboard.py
   ```

2. Select your desired date range from the sidebar

3. Explore different sections:
   - Scroll through summary cards at top
   - Check monthly analysis for trends
   - Dive into spending patterns
   - Analyze merchant behavior
   - Review recent transactions

4. Use filters to focus on specific:
   - Categories
   - Merchants
   - Amount ranges

5. Export data as needed for further analysis

## 💡 Tips

- Use "Last 3 Months" for monthly comparisons (need at least 30 days)
- Check the heatmap to spot unusual spending weeks
- Review top merchants regularly to identify subscription renewals
- Use merchant frequency to find your regular spots
- Compare MoM changes to track budget improvement
- Filter by high amounts to find big purchases
