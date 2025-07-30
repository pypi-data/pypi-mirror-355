# Browser History Analytics

A Python package that analyzes and visualizes your browser history data with interactive charts and insights.

## Features

- 📈 **Interactive Visualizations**: Beautiful charts showing your browsing patterns  
- 🔍 **Category Analysis**: Automatically categorizes websites (Social Media, Development, Entertainment, etc.)  
- ⏰ **Time-based Insights**: Hourly and daily browsing patterns with heatmaps  
- 📊 **Summary Statistics**: Key metrics about your browsing habits  
- 🎛️ **Interactive Filters**: Filter by date range and categories  
- 📋 **Raw Data View**: Search and export your browsing data  
- 🌐 **Multi-browser Support**: Works with Chrome, Firefox, Safari, and more  

## Installation

### Option 1: Install from source

```bash
git clone https://github.com/your-username/browser-history-analytics.git
cd browser-history-analytics
pip install -e .
```

### Option 2: Install directly

```bash
pip install browser-history-analytics
```

## Usage
Command prompt: 
```
pip install browser-history-analytics && browser_history_analytics
```
Powershell: 
```
pip install browser-history-analytics ; browser_history_analytics
```

This will launch the web application in your default browser.

## What You'll See

### Dashboard Tabs

1. **Home**: Main dashboard with visualizations and summary statistics
2. **Raw Data**: Searchable table with export functionality
3. **Additional Info**: Detailed insights and browsing habits analysis

### Visualizations

* **Top Domains**: Bar chart of most visited websites
* **Activity Timeline**: Daily visits over time
* **Activity Heatmap**: Browsing patterns by hour and day of week
* **Category Distribution**: Pie chart of website categories
* **Hourly Patterns**: Bar chart showing peak browsing hours

## Requirements

* Python 3.7+
* Browser history data (automatically detected)

## Dependencies

* `streamlit`
* `plotly`
* `pandas`
* `browser-history`
* `numpy`
* `seaborn`
* `matplotlib`
* `urllib3`

## Privacy Note

This tool only reads your local browser history files. No data is sent to external servers – everything runs locally on your machine.

## Supported Browsers

* Google Chrome
* Mozilla Firefox
* Safari
* Microsoft Edge
* Opera

## Contributing

Feel free to open issues and submit pull requests!

## License

[MIT License](LICENSE)

## Author

Arpit Sengar ([@arpy8](https://github.com/arpy8))