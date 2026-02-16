# app.py
from flask import Flask, request, jsonify, render_template
from datetime import datetime
import logging
from auth import gmail_authenticate, fetch_emails  # Your Gmail API auth/fetch functions
from classifier import keyword_categories, decode_subject
from ai_response import generate_ai_greeting
from app  import db,migrate
from app  import models


app = Flask(__name__)
logging.basicConfig(level=logging.INFO)
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://username:password@localhost/email_amplifier_db'  # change this
# or better: os.getenv('DATABASE_URL')

db.init_app(app)
migrate.init_app(app, db)

def classify_fetched_emails(fetched_emails):
    """Classify fetched Gmail API emails by subject keywords."""
    classified = {cat: [] for cat in keyword_categories}
    uncategorized = []

    for msg in fetched_emails:
        # Extract subject from Gmail API message data
        headers = msg.get('payload', {}).get('headers', [])
        subject = ""
        for header in headers:
            if header.get('name', '').lower() == 'subject':
                subject = header.get('value', '')
                break
        
        decoded_subject = decode_subject(subject).lower()

        assigned = False
        for category, keywords in keyword_categories.items():
            if any(kw in decoded_subject for kw in keywords):
                classified[category].append(decoded_subject)
                assigned = True
                break
        if not assigned:
            uncategorized.append(decoded_subject)

    return {
        "classified": {k: {"count": len(v), "examples": v[:10]} for k, v in classified.items() if v},
        "uncategorized_count": len(uncategorized),
        "uncategorized_examples": uncategorized[:10],
        "total_emails": len(fetched_emails)
    }

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/classify', methods=['POST'])
def classify():
    """Classify emails using Gmail API with date range input."""
    data = request.json
    if not data:
        return jsonify({"error": "No data provided"}), 400

    # Get required parameters
    start_date = data.get('start_date')  # YYYY/MM/DD format
    end_date = data.get('end_date')      # YYYY/MM/DD format
    
    if not start_date or not end_date:
        return jsonify({"error": "start_date and end_date are required"}), 400

    try:
        # Authenticate with Gmail API
        service = gmail_authenticate()
        
        # Fetch emails with pagination and error handling
        emails = fetch_emails(service, start_date=start_date, end_date=end_date)
        
        if not emails:
            return jsonify({"message": "No emails found in the specified date range"}), 200
        
        # Classify fetched emails
        results = classify_fetched_emails(emails)
        
        logging.info(f"Classified {len(emails)} emails from {start_date} to {end_date}")
        return jsonify(results)
        
    except Exception as e:
        logging.error(f"Classification error: {str(e)}")
        return jsonify({"error": f"Classification failed: {str(e)}"}), 500

@app.route('/api/greet', methods=['POST'])
def greet():
    """Generate AI greeting (keeping your existing functionality)."""
    data = request.json or {}
    name = data.get('name', 'Valued Partner')
    context = data.get('context', '')
    greeting = generate_ai_greeting(name, context)
    return jsonify({"greeting": greeting})

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)