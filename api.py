"""
Flask API for news analysis application.
Provides endpoints for fetching, analyzing, and converting news to speech.
"""
import json
import os
import time
import uuid
from tempfile import mkdtemp

from flask import Flask, jsonify, request, send_file
from flask_cors import CORS
from gtts import gTTS

# Use Waitress for production deployment
from waitress import serve  # Install with: pip install waitress

from communication.utils import (analyze_sentiment, compare_articles, extract_topics,
                  generate_final_sentiment_text, scrape_article,
                  search_news_articles, summarize_text)

app = Flask(__name__)
CORS(app)  # Enable cross-origin requests

# Create a temporary directory for audio files
TEMP_DIR = mkdtemp()
os.makedirs(TEMP_DIR, exist_ok=True)

# Map of language names to gTTS language codes
LANGUAGE_CODES = {
    'English': 'en',
    'Hindi': 'hi'
}

@app.route('/api/news', methods=['GET'])
def get_news():
    """Fetch news articles for a company."""
    company_name = request.args.get('company', '')
    if not company_name:
        return jsonify({"error": "Company name is required"}), 400

    try:
        # Get article URLs
        articles = search_news_articles(company_name)

        if not articles:
            return jsonify({
                "error": "No articles found for this company",
                "company": company_name
            }), 404

        return jsonify({
            "company": company_name,
            "articles": articles
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/scrape', methods=['POST'])
def scrape_articles():
    """Scrape content from article URLs."""
    data = request.json
    if not data or 'articles' not in data:
        return jsonify({"error": "Articles data is required"}), 400

    try:
        articles_data = data['articles']
        scraped_articles = []

        for article in articles_data:
            scraped = scrape_article(article['url'])
            if scraped:
                scraped_articles.append(scraped)

            # Add delay to avoid overloading servers
            time.sleep(0.5)

        if not scraped_articles:
            return jsonify({
                "error": "Failed to scrape any articles",
                "company": data.get('company', '')
            }), 404

        return jsonify({
            "company": data.get('company', ''),
            "articles": scraped_articles
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/analyze', methods=['POST'])
def analyze_articles():
    """Analyze scraped articles for sentiment and topics."""
    data = request.json
    if not data or 'articles' not in data:
        return jsonify({"error": "Articles data is required"}), 400

    try:
        articles = data['articles']
        results = []

        for article in articles:
            # Skip articles with insufficient content
            if not article.get('content') or len(article.get('content', '')) < 100:
                continue

            summary = summarize_text(article['content'])
            sentiment = analyze_sentiment(article['content'])
            topics = extract_topics(article['content'])

            results.append({
                "title": article['title'],
                "summary": summary,
                "sentiment": sentiment,
                "topics": topics,
                "date": article.get('date'),
                "source": article.get('source'),
                "url": article.get('url')
            })

        # Generate comparative analysis
        comparative = compare_articles(results)

        # Generate final sentiment text
        final_sentiment = generate_final_sentiment_text(data.get('company', ''), comparative)

        return jsonify({
            "company": data.get('company', ''),
            "articles": results,
            "comparative_sentiment_score": comparative,
            "final_sentiment_analysis": final_sentiment
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/tts', methods=['POST'])
def generate_tts():
    """Generate text-to-speech audio from text."""
    data = request.json
    if not data or 'text' not in data or 'language' not in data:
        return jsonify({"error": "Text and language are required"}), 400

    if data['language'] not in LANGUAGE_CODES:
        return jsonify({"error": f"Unsupported language. Choose from: {list(LANGUAGE_CODES.keys())}"}), 400

    try:
        text = data['text']
        language = data['language']
        lang_code = LANGUAGE_CODES[language]

        # Generate unique filename
        filename = f"speech_{language.lower()}_{uuid.uuid4()}.mp3"
        file_path = os.path.join(TEMP_DIR, filename)

        # Create gTTS object
        tts = gTTS(text=text, lang=lang_code, slow=False)

        # Save to file
        tts.save(file_path)

        # Return URL path to the audio file
        return jsonify({"audio_file": file_path, "filename": filename})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/audio/<filename>', methods=['GET'])
def get_audio(filename):
    try:
        file_path = os.path.join(TEMP_DIR, filename)
        if os.path.exists(file_path):
            return send_file(file_path, mimetype='audio/mpeg')
        else:
            return jsonify({"error": "Audio file not found"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == '__main__':
    # For development:
    # app.run(debug=True, host='0.0.0.0', port=5000)

    # For production:
    serve(
        app,
        host='0.0.0.0',
        port=5000,
        threads=4,         # Adjust based on your server capacity
        connection_limit=100,
        channel_timeout=120  # 2 minutes timeout
    )