import os
import requests
from bs4 import BeautifulSoup
import feedparser
import json
from datetime import datetime
import pytz
import re

# 配置
NEWS_URL = os.getenv('NEWS_URL', 'https://news.google.com/topics/CAAqJggKIiBDQkFTRWdvSUwyMHZNRGx1YlY4U0FtVnVHZ0pWVXlnQVAB?ceid=US:en&oc=3')
OUTPUT_DIR = 'news'
MAX_ARTICLES = 20  # 最大保存文章数量

def get_rss_feed_url(topic_url):
    """从 Google News 主题页面提取 RSS feed URL"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(topic_url, headers=headers, timeout=30)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        rss_link = soup.find('link', {'type': 'application/rss+xml'})
        
        if rss_link:
            return rss_link['href']
        else:
            # 尝试通过模式匹配查找 RSS URL
            match = re.search(r'https://news\.google\.com/rss/topics/[^\'"]+', response.text)
            return match.group(0) if match else None
    except Exception as e:
        print(f"Error getting RSS URL: {e}")
        return None

def parse_rss_feed(rss_url):
    """解析 RSS feed 并提取新闻内容"""
    try:
        feed = feedparser.parse(rss_url)
        articles = []
        
        for entry in feed.entries[:MAX_ARTICLES]:
            # 清理来源信息
            source = entry.get('source', {}).get('title', '') if 'source' in entry else ''
            if ' - ' in source:
                source = source.split(' - ')[0]
                
            article = {
                'title': entry.title,
                'link': entry.link,
                'published': entry.get('published', ''),
                'source': source,
                'summary': entry.get('summary', '')
            }
            articles.append(article)
            
        return articles
    except Exception as e:
        print(f"Error parsing RSS feed: {e}")
        return []

def save_news_data(articles):
    """保存新闻数据到文件"""
    try:
        # 确保目录存在
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        
        # 获取当前日期（北京时间）
        beijing_tz = pytz.timezone('Asia/Shanghai')
        now = datetime.now(beijing_tz)
        date_str = now.strftime('%Y-%m-%d')
        
        # 保存为JSON文件
        json_file = os.path.join(OUTPUT_DIR, f'google-news-{date_str}.json')
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump({
                'date': date_str,
                'source_url': NEWS_URL,
                'articles': articles
            }, f, ensure_ascii=False, indent=2)
            
        # 更新README.md
        update_readme(articles, date_str)
        
        print(f"Successfully saved {len(articles)} articles for {date_str}")
    except Exception as e:
        print(f"Error saving news data: {e}")

def update_readme(articles, date_str):
    """更新README文件显示最新新闻"""
    try:
        readme_path = 'README.md'
        markdown_content = f"# Google News Daily Archive\n\n"
        markdown_content += f"**Last Updated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} (UTC)\n\n"
        markdown_content += f"## Today's Top News ({date_str})\n\n"
        
        for i, article in enumerate(articles[:5], 1):  # 只显示前5条
            markdown_content += f"{i}. [{article['title']}]({article['link']}) - *{article['source']}*\n"
            markdown_content += f"   > {article['summary'][:150]}...\n\n"
        
        markdown_content += f"\n[View all articles for {date_str}](news/google-news-{date_str}.json)\n\n"
        markdown_content += "## Historical Data\n"
        markdown_content += "| Date | Articles | View |\n"
        markdown_content += "|------|----------|------|\n"
        
        # 添加历史文件链接
        for file in sorted(os.listdir(OUTPUT_DIR), reverse=True):
            if file.startswith('google-news-') and file.endswith('.json'):
                date = file[12:-5]
                article_count = len(json.load(open(os.path.join(OUTPUT_DIR, file)))['articles'])
                markdown_content += f"| {date} | {article_count} articles | [View]({os.path.join(OUTPUT_DIR, file)}) |\n"
        
        with open(readme_path, 'w', encoding='utf-8') as f:
            f.write(markdown_content)
    except Exception as e:
        print(f"Error updating README: {e}")

if __name__ == "__main__":
    print("Starting Google News scraper...")
    print(f"Target URL: {NEWS_URL}")
    
    # 获取RSS feed URL
    rss_url = get_rss_feed_url(NEWS_URL)
    if not rss_url:
        print("Failed to find RSS feed URL")
        exit(1)
        
    print(f"Found RSS feed: {rss_url}")
    
    # 解析RSS feed
    articles = parse_rss_feed(rss_url)
    if not articles:
        print("No articles found in RSS feed")
        exit(1)
        
    print(f"Found {len(articles)} articles")
    
    # 保存结果
    save_news_data(articles)
    print("Scraping completed successfully")
