# News Analyzer

A comprehensive web application for analyzing company news sentiment and providing multilingual text-to-speech functionality.

## Features

- Real-time news aggregation from multiple sources
- Web scraping of article content
- Sentiment analysis using hybrid approach (rule-based + machine learning)
- Extractive and abstractive text summarization
- Topic extraction and keyword analysis
- Comparative analysis across multiple news sources
- Bilingual text-to-speech conversion (English, Hindi)
- Interactive data visualization dashboard

## Project Structure

```
news_analyzer/
├── app.py                  # Main Streamlit application
├── api.py                  # API endpoints for backend-frontend communication
├── utils.py                # Utility functions for data processing
├── models.py               # ML model loading and utilities
├── requirements.txt        # Dependencies
├── README.md               # Documentation
├── static/                 # Static assets
│   └── logo.png            # App logo
└── tests/                  # Unit tests
    └── test_utils.py       # Tests for utility functions
```

## Installation

Clone the repository:
```bash
git clone https://github.com/yourusername/news-analyzer.git
cd news-analyzer
```

Create a virtual environment and install dependencies:
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate     # Windows

pip install -r requirements.txt
python -m spacy download en_core_web_sm
```

## Usage

1. Start the API server:
```bash
python api.py
```

2. In a new terminal, start the Streamlit application:
```bash
streamlit run app.py
```

3. Open your browser and navigate to http://localhost:8501

## API Endpoints

### GET /api/news
Fetches news articles for a specified company.

**Parameters:**
- `company` (query string): Company name to search for

**Response:**
```json
{
  "company": "Company Name",
  "articles": [
    {
      "title": "Article Title",
      "url": "https://example.com/article",
      "published": "2025-03-15"
    }
  ]
}
```

### POST /api/scrape
Scrapes content from article URLs.

**Request Body:**
```json
{
  "company": "Company Name",
  "articles": [
    {
      "title": "Article Title",
      "url": "https://example.com/article"
    }
  ]
}
```

**Response:**
```json
{
  "company": "Company Name",
  "articles": [
    {
      "title": "Article Title",
      "content": "Article content...",
      "date": "2025-03-15",
      "source": "example.com",
      "url": "https://example.com/article"
    }
  ]
}
```

### POST /api/analyze
Analyzes scraped articles for sentiment and topics.

**Request Body:**
```json
{
  "company": "Company Name",
  "articles": [
    {
      "title": "Article Title",
      "content": "Article content...",
      "date": "2025-03-15",
      "source": "example.com",
      "url": "https://example.com/article"
    }
  ]
}
```

**Response:**
```json
{
  "company": "Company Name",
  "articles": [
    {
      "title": "Article Title",
      "summary": "Article summary...",
      "sentiment": {
        "label": "Positive",
        "score": 0.75
      },
      "topics": ["AI", "Technology", "Innovation"],
      "date": "2025-03-15",
      "source": "example.com",
      "url": "https://example.com/article"
    }
  ],
  "comparative_sentiment_score": {
    "Sentiment Distribution": {
      "Positive": 3,
      "Negative": 1,
      "Neutral": 2
    }
  },
  "final_sentiment_analysis": "Company Name's recent news coverage leans positive..."
}
```

### POST /api/tts
Generates text-to-speech audio from text.

**Request Body:**
```json
{
  "text": "Text to convert to speech",
  "language": "English"
}
```

**Response:**
```json
{
  "audio_file": "/path/to/audio/file.mp3",
  "filename": "speech_english_uuid.mp3"
}
```

### GET /api/audio/<filename>
Serves generated audio files.

## Testing

Run the tests with:
```bash
python -m unittest discover tests
```

## Deployment

### Hugging Face Spaces

1. Create a new Space with Docker container runtime
2. Configure storage for temporary audio files
3. Set environment variables in Dockerfile

## License

MIT

## Acknowledgements

- [Hugging Face](https://huggingface.co/) for transformers models
- [VADER Sentiment](https://github.com/cjhutto/vaderSentiment) for rule-based sentiment analysis
- [Streamlit](https://streamlit.io/) for the interactive web application
- [Flask](https://flask.palletsprojects.com/) for the API backend
- [gTTS](https://gtts.readthedocs.io/) for text-to-speech conversion