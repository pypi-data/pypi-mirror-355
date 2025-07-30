import pandas as pd
from urllib.parse import urlparse


def generate_df(data):
    try:
        df = pd.DataFrame(data, columns=['date', 'url', 'title'])
        df['date'] = pd.to_datetime(df['date'])
        
        df['domain'] = df['url'].apply(lambda x: urlparse(str(x)).netloc)
        
        df['hour'] = df['date'].dt.hour
        df['day_of_week'] = df['date'].dt.day_name()
        df['day_num'] = df['date'].dt.dayofweek
        
        df['category'] = df['domain'].apply(categorize_domain)
        
        df = df.dropna(subset=['url', 'domain'])
        df = df[df['domain'] != '']
        
        return df
        
    except Exception as e:
        raise ValueError(f"Error generating DataFrame: {e}")

def categorize_domain(domain):
    if pd.isna(domain) or domain == '':
        return 'Unknown'
    
    domain = domain.lower()
    
    if any(social in domain for social in ['facebook', 'twitter', 'instagram', 'linkedin', 'reddit', 'snapchat', 'tiktok']):
        return 'Social Media'
    
    elif any(search in domain for search in ['google', 'bing', 'yahoo', 'duckduckgo']):
        return 'Search Engine'
    
    elif any(dev in domain for dev in ['github', 'stackoverflow', 'codepen', 'repl', 'jupyter', 'colab']):
        return 'Development'
    
    elif any(ent in domain for ent in ['youtube', 'netflix', 'spotify', 'twitch', 'hulu']):
        return 'Entertainment'
    
    elif any(news in domain for news in ['news', 'bbc', 'cnn', 'reuters', 'times']):
        return 'News'
    
    elif any(shop in domain for shop in ['amazon', 'ebay', 'flipkart', 'myntra', 'shopping']):
        return 'Shopping'
    
    elif any(edu in domain for edu in ['edu', 'coursera', 'udemy', 'khan', 'edx']):
        return 'Education'
    
    elif any(work in domain for work in ['office', 'docs', 'sheets', 'drive', 'dropbox', 'slack']):
        return 'Productivity'
    
    elif 'localhost' in domain or 'file://' in domain or '127.0.0.1' in domain:
        return 'Local Development'
    
    else:
        return 'Other'
    

def get_summary_stats(df):
    total_visits = len(df)
    unique_domains = df['domain'].nunique()
    date_range = f"{df['date'].min().date()} to {df['date'].max().date()}"
    most_active_day = df['day_of_week'].value_counts().index[0]
    most_active_hour = df['hour'].value_counts().index[0]
    top_domain = df['domain'].value_counts().index[0]
    
    return {
        'total_visits': total_visits,
        'unique_domains': unique_domains,
        'date_range': date_range,
        'most_active_day': most_active_day,
        'most_active_hour': f"{most_active_hour}:00",
        'top_domain': top_domain
    }