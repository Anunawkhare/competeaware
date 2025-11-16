import joblib
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import Pipeline
import re
import sqlite3


class SimpleClassifier:
    def __init__(self):
        self.model = None
        self.categories = ['pricing', 'campaign', 'product_release', 'partnership', 'other']

    def train_model(self):
        print("Training classification model...")

        # Training data - simple lists instead of pandas
        texts = [
            "price discount sale offer cheap cost reduction affordable special deal limited time",
            "campaign promotion advertise marketing launch event special announcement",
            "new feature update release version product launch announced innovation",
            "partnership collaboration alliance merge joint venture cooperation",
            "company office team hiring news update information blog post"
        ]

        labels = ['pricing', 'campaign', 'product_release', 'partnership', 'other']

        self.model = Pipeline([
            ('tfidf', TfidfVectorizer()),
            ('clf', MultinomialNB())
        ])

        self.model.fit(texts, labels)
        joblib.dump(self.model, 'classifier_model.pkl')
        print("Model trained and saved successfully!")

    def load_model(self):
        try:
            self.model = joblib.load('classifier_model.pkl')
            print("Model loaded successfully!")
        except FileNotFoundError:
            print("No trained model found. Training new model...")
            self.train_model()

    def predict_category(self, text):
        if not self.model:
            self.load_model()

        # Simple text cleaning
        text = re.sub(r'[^\w\s]', '', text.lower())

        try:
            prediction = self.model.predict([text])[0]
            confidence = max(self.model.predict_proba([text])[0])
            return prediction, confidence
        except Exception as e:
            print(f"Prediction error: {e}")
            return "other", 0.5


def categorize_updates():
    classifier = SimpleClassifier()
    conn = sqlite3.connect('competeaware.db')
    c = conn.cursor()

    # Get uncategorized updates
    c.execute("SELECT id, content FROM competitor_updates WHERE category = 'general' OR category IS NULL")
    updates = c.fetchall()

    print(f"Found {len(updates)} updates to categorize...")

    categorized_count = 0
    for update_id, content in updates:
        if content and len(content) > 10:  # Only categorize if there's meaningful content
            category, confidence = classifier.predict_category(content)

            # Update the category in database
            c.execute("UPDATE competitor_updates SET category = ?, impact_score = ? WHERE id = ?",
                      (category, confidence, update_id))
            categorized_count += 1

    conn.commit()
    conn.close()
    print(f"Successfully categorized {categorized_count} updates")


if __name__ == '__main__':
    # Train the model when this file is run directly
    classifier = SimpleClassifier()
    classifier.train_model()
    print("Classifier setup completed!")