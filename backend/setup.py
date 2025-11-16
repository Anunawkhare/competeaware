import sqlite3
import json


def setup_database():
    conn = sqlite3.connect('competeaware.db')
    c = conn.cursor()

    # Add sample competitors
    sample_competitors = [
        ('TechCorp Inc', 'https://example.com', '{"twitter": "techcorp"}'),
        ('InnovateLabs', 'https://example.org', '{"twitter": "innovatelabs"}')
    ]

    c.executemany('''
        INSERT OR IGNORE INTO competitors (name, website, social_handles)
        VALUES (?, ?, ?)
    ''', sample_competitors)

    conn.commit()
    conn.close()
    print("Database setup completed with sample data!")


if __name__ == '__main__':
    setup_database()