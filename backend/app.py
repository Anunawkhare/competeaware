from flask import Flask, jsonify, request
from flask_cors import CORS
import sqlite3
from datetime import datetime
import threading
import time
import sys
import os

# Add current directory to Python path
sys.path.append(os.path.dirname(__file__))

try:
    from scraper import run_scraping_for_all
    from classifier import categorize_updates, SimpleClassifier
    from database import init_db, get_db_connection

    print("✅ All modules imported successfully!")
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("💡 Make sure all required packages are installed: pip install -r requirements.txt")

app = Flask(__name__)
CORS(app)

# Initialize database
try:
    init_db()
    print("✅ Database initialized successfully!")
except Exception as e:
    print(f"❌ Database initialization error: {e}")


@app.route('/')
def home():
    return jsonify({
        "message": "CompeteAware API is running!",
        "status": "healthy",
        "endpoints": {
            "competitors": "/api/competitors",
            "updates": "/api/updates",
            "dashboard": "/api/dashboard/stats",
            "scrape": "/api/scrape (POST)"
        }
    })


@app.route('/api/competitors', methods=['GET'])
def get_competitors():
    try:
        conn = get_db_connection()
        competitors = conn.execute('SELECT * FROM competitors WHERE is_active = 1').fetchall()
        conn.close()

        competitors_list = []
        for comp in competitors:
            competitors_list.append({
                'id': comp[0],
                'name': comp[1],
                'website': comp[2],
                'social_handles': comp[3],
                'is_active': bool(comp[4]),
                'created_at': comp[5]
            })

        return jsonify(competitors_list)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/competitors', methods=['POST'])
def add_competitor():
    try:
        data = request.get_json()
        name = data.get('name')
        website = data.get('website')
        social_handles = data.get('social_handles', '{}')

        conn = get_db_connection()
        c = conn.cursor()

        c.execute('''
            INSERT INTO competitors (name, website, social_handles, created_at)
            VALUES (?, ?, ?, ?)
        ''', (name, website, social_handles, datetime.now()))

        conn.commit()
        conn.close()

        return jsonify({'message': 'Competitor added successfully'}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/updates', methods=['GET'])
def get_updates():
    try:
        competitor_id = request.args.get('competitor_id')
        category = request.args.get('category')
        limit = int(request.args.get('limit', 50))

        conn = get_db_connection()
        query = 'SELECT * FROM competitor_updates WHERE 1=1'
        params = []

        if competitor_id:
            query += ' AND competitor_id = ?'
            params.append(competitor_id)
        if category:
            query += ' AND category = ?'
            params.append(category)

        query += ' ORDER BY detected_at DESC LIMIT ?'
        params.append(limit)

        updates = conn.execute(query, params).fetchall()
        conn.close()

        updates_list = []
        for update in updates:
            updates_list.append({
                'id': update[0],
                'competitor_id': update[1],
                'title': update[2],
                'content': update[3],
                'category': update[4],
                'source': update[5],
                'url': update[6],
                'impact_score': update[7],
                'detected_at': update[8],
                'created_at': update[9]
            })

        return jsonify(updates_list)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/dashboard/stats', methods=['GET'])
def get_dashboard_stats():
    try:
        conn = get_db_connection()

        total_competitors = conn.execute('SELECT COUNT(*) FROM competitors WHERE is_active = 1').fetchone()[0]
        total_updates = conn.execute('SELECT COUNT(*) FROM competitor_updates').fetchone()[0]

        recent_updates = conn.execute('''
            SELECT * FROM competitor_updates 
            ORDER BY detected_at DESC LIMIT 10
        ''').fetchall()

        # Category distribution
        categories = conn.execute('''
            SELECT category, COUNT(*) as count 
            FROM competitor_updates 
            GROUP BY category
        ''').fetchall()

        conn.close()

        # Convert to dict
        recent_updates_list = []
        for update in recent_updates:
            recent_updates_list.append({
                'id': update[0],
                'competitor_id': update[1],
                'title': update[2],
                'content': update[3],
                'category': update[4],
                'source': update[5],
                'url': update[6],
                'impact_score': update[7],
                'detected_at': update[8]
            })

        category_distribution = {}
        for cat in categories:
            category_distribution[cat[0] or 'uncategorized'] = cat[1]

        return jsonify({
            'total_competitors': total_competitors,
            'total_updates': total_updates,
            'recent_updates': recent_updates_list,
            'category_distribution': category_distribution,
            'last_updated': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/scrape', methods=['POST'])
def trigger_scraping():
    """Manually trigger scraping for all competitors"""
    try:
        thread = threading.Thread(target=run_scraping_for_all)
        thread.daemon = True
        thread.start()
        return jsonify({"message": "Scraping started in background", "status": "started"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


def background_scraper():
    """Run scraping every hour in background"""
    while True:
        try:
            print("🕒 Running scheduled scraping...")
            run_scraping_for_all()
            time.sleep(3600)  # 1 hour
        except Exception as e:
            print(f"❌ Background scraping error: {e}")
            time.sleep(300)  # Wait 5 minutes before retrying


if __name__ == '__main__':
    print("🚀 Starting CompeteAware Backend Server...")
    print("📊 API will be available at: http://localhost:5000")
    print("🌐 Dashboard: open frontend/index.html in your browser")

    # Train classifier on startup
    try:
        classifier = SimpleClassifier()
        classifier.load_model()
        print("✅ Classifier ready!")
    except Exception as e:
        print(f"❌ Classifier setup failed: {e}")

    # Start background scraping thread
    try:
        scraper_thread = threading.Thread(target=background_scraper)
        scraper_thread.daemon = True
        scraper_thread.start()
        print("✅ Background scraper started!")
    except Exception as e:
        print(f"❌ Background scraper failed: {e}")

    # Start Flask app
    app.run(debug=True, host='0.0.0.0', port=5000)