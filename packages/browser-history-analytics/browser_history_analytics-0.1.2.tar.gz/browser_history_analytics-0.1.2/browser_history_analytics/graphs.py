import plotly.express as px


def create_top_domains_chart(df):
    domain_counts = df['domain'].value_counts().head(15)
    
    fig = px.bar(
        x=domain_counts.values,
        y=domain_counts.index,
        orientation='h',
        title='Top 15 Most Visited Domains',
        labels={'x': 'Visit Count', 'y': 'Domain'},
        color=domain_counts.values,
        color_continuous_scale='viridis'
    )
    
    fig.update_layout(
        height=600,
        yaxis={'categoryorder': 'total ascending'}
    )
    
    return fig

def create_visits_over_time_chart(df):
    daily_visits = df.groupby(df['date'].dt.date).size().reset_index()
    daily_visits.columns = ['date', 'visits']
    
    fig = px.line(
        daily_visits,
        x='date',
        y='visits',
        title='Daily Website Visits Over Time',
        labels={'visits': 'Number of Visits', 'date': 'Date'}
    )
    
    fig.update_traces(line=dict(width=2))
    fig.update_layout(height=400)
    
    return fig

def create_hourly_heatmap(df):
    hourly_activity = df.groupby(['day_of_week', 'hour']).size().reset_index(name='visits')
    
    heatmap_data = hourly_activity.pivot(index='day_of_week', columns='hour', values='visits').fillna(0)
    
    day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    heatmap_data = heatmap_data.reindex(day_order)
    
    fig = px.imshow(
        heatmap_data,
        title='Browsing Activity Heatmap (by Hour and Day)',
        labels={'x': 'Hour of Day', 'y': 'Day of Week', 'color': 'Number of Visits'},
        color_continuous_scale='Blues'
    )
    
    fig.update_layout(height=400)
    
    return fig

def create_category_pie_chart(df):
    category_counts = df['category'].value_counts()
    
    fig = px.pie(
        values=category_counts.values,
        names=category_counts.index,
        title='Website Categories Distribution'
    )
    
    fig.update_traces(textposition='inside', textinfo='percent+label')
    fig.update_layout(height=500)
    
    return fig

def create_browsing_pattern_chart(df):
    hourly_visits = df.groupby('hour').size().reset_index(name='visits')
    
    fig = px.bar(
        hourly_visits,
        x='hour',
        y='visits',
        title='Browsing Patterns by Hour of Day',
        labels={'hour': 'Hour of Day', 'visits': 'Number of Visits'}
    )
    
    fig.update_layout(height=400)
    
    return fig