import requests
from bs4 import BeautifulSoup
import sqlite3
from datetime import datetime
import time
import random


class SimpleScraper:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })

    def scrape_competitor(self, competitor_id, website):
        try:
            print(f"🔍 Scraping {website}...")

            # Add delay to be respectful to websites
            time.sleep(random.uniform(1, 3))

            response = self.session.get(website, timeout=15)
            response.raise_for_status()  # Raise exception for bad status codes

            soup = BeautifulSoup(response.content, 'html.parser')

            # Extract basic information
            title = soup.find('title')
            page_title = title.text.strip() if title else "No title"

            # Look for recent updates in common structures
            updates = []

            # Strategy 1: Look for blog posts or articles
            selectors = ['article', '.post', '.blog-post', '.news-item', '.update']
            for selector in selectors:
                posts = soup.select(selector)
                for post in posts[:5]:  # Limit to 5 posts
                    content = post.get_text(strip=True)
                    if len(content) > 30:
                        updates.append({
                            'competitor_id': competitor_id,
                            'title': page_title,
                            'content': content[:500],  # Limit content length
                            'source': 'website',
                            'url': website,
                            'category': 'general',
                            'detected_at': datetime.now()
                        })

            # Strategy 2: If no specific posts found, use main content
            if not updates:
                main_selectors = ['main', '.main-content', '#content', 'body']
                for selector in main_selectors:
                    main_content = soup.select_one(selector)
                    if main_content:
                        content = main_content.get_text(strip=True)
                        if len(content) > 100:
                            updates.append({
                                'competitor_id': competitor_id,
                                'title': page_title,
                                'content': content[:500],
                                'source': 'website',
                                'url': website,
                                'category': 'general',
                                'detected_at': datetime.now()
                            })
                            break

            print(f"✅ Found {len(updates)} updates from {website}")
            return updates

        except requests.RequestException as e:
            print(f"❌ Network error scraping {website}: {str(e)}")
            return []
        except Exception as e:
            print(f"❌ Error scraping {website}: {str(e)}")
            return []


def save_updates(updates):
    if not updates:
        return

    conn = sqlite3.connect('competeaware.db')
    c = conn.cursor()

    saved_count = 0
    for update in updates:
        try:
            # Check if similar update already exists to avoid duplicates
            c.execute('''
                SELECT id FROM competitor_updates 
                WHERE competitor_id = ? AND content LIKE ? AND detected_at > datetime('now', '-1 day')
            ''', (update['competitor_id'], f"%{update['content'][:50]}%"))

            existing = c.fetchone()

            if not existing:
                c.execute('''
                    INSERT INTO competitor_updates 
                    (competitor_id, title, content, category, source, url, detected_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    update['competitor_id'],
                    update['title'],
                    update['content'],
                    update['category'],
                    update['source'],
                    update['url'],
                    update['detected_at']
                ))
                saved_count += 1

        except Exception as e:
            print(f"Error saving update: {e}")
            continue

    conn.commit()
    conn.close()
    print(f"💾 Saved {saved_count} new updates to database")


def run_scraping_for_all():
    """Run scraping for all active competitors"""
    conn = sqlite3.connect('competeaware.db')
    c = conn.cursor()

    competitors = c.execute('SELECT * FROM competitors WHERE is_active = 1').fetchall()
    conn.close()

    if not competitors:
        print("❌ No active competitors found. Please add competitors first.")
        return

    print(f"🚀 Starting scraping for {len(competitors)} competitors...")

    scraper = SimpleScraper()
    all_updates = []

    for competitor in competitors:
        updates = scraper.scrape_competitor(competitor[0], competitor[2])  # id, website
        all_updates.extend(updates)

    save_updates(all_updates)

    # Categorize the new updates
    from classifier import categorize_updates
    categorize_updates()

    print(f"🎉 Scraping completed! Processed {len(all_updates)} total updates.")