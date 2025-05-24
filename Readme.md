# 🎙️ News Analyzer - Bilingual Sentiment Analysis Platform

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://python.org)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.31.0-red.svg)](https://streamlit.io)
[![Flask](https://img.shields.io/badge/Flask-2.3.3-green.svg)](https://flask.palletsprojects.com)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

A comprehensive web application for analyzing company news sentiment with **automatic bilingual text-to-speech functionality**. Get instant sentiment analysis in both **English and Hindi** without language selection hassle!

## ✨ Key Features

- 📰 **Real-time news aggregation** from multiple sources (Google News, Bing News)
- 🕷️ **Intelligent web scraping** of article content with fallback mechanisms
- 🧠 **Hybrid sentiment analysis** combining VADER and transformer models
- 📝 **AI-powered text summarization** using Facebook BART model
- 🏷️ **Topic extraction** with Named Entity Recognition and TF-IDF
- 📊 **Comparative analysis** across multiple news sources
- 🎙️ **Automatic bilingual TTS** - English & Hindi audio summaries generated simultaneously
- 📈 **Interactive visualizations** with Plotly charts and graphs
- 🌐 **Modern web interface** built with Streamlit

## 🏗️ Architecture

```
news-analyzer-bilingual/
├── 🎨 Frontend (Streamlit)
│   ├── app.py                      # Main Streamlit dashboard
│   └── static/logo.png             # Application logo
├── 🔧 Backend (Flask API)
│   ├── api.py                      # REST API endpoints
│   ├── communication/
│   │   └── utils.py                # Core processing utilities
│   └── models.py                   # ML model management
├── 🧪 Testing
│   └── tests/test_utils.py         # Unit tests
├── 📋 Configuration
│   ├── requirements.txt            # Python dependencies
│   ├── .gitignore                  # Git ignore rules
│   └── README.md                   # This file
└── 📄 Documentation
    └── News Analyzer Project Structure.doc
```

## 🚀 Quick Start

### Prerequisites

- Python 3.8 or higher
- pip package manager
- Internet connection (for news fetching and TTS)

### Installation

1. **Clone the repository**
```bash
git clone https://github.com/yourusername/news-analyzer-bilingual.git
cd news-analyzer-bilingual
```

2. **Create virtual environment**
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate     # Windows
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
python -m spacy download en_core_web_sm
```

4. **Start the application**

**Terminal 1 - Start Flask API:**
```bash
python api.py
```

**Terminal 2 - Start Streamlit App:**
```bash
streamlit run app.py
```

5. **Access the application**
   - Open your browser and navigate to `http://localhost:8501`
   - The Flask API runs on `http://localhost:5000`

## 🎯 How to Use

### Step-by-Step Workflow

1. **📰 Fetch News** - Enter a company name (e.g., "Tesla", "Apple") and fetch recent articles
2. **🕷️ Scrape Content** - Extract full article text from news URLs
3. **🧠 Analyze Articles** - Perform sentiment analysis and topic extraction
4. **🎙️ Generate Summary** - Automatically create bilingual audio summaries

### 🎙️ Bilingual TTS Feature

The application automatically generates audio summaries in **both English and Hindi** simultaneously:

- **🇺🇸 English Audio** - Uses original analysis text
- **🇮🇳 Hindi Audio** - Generates contextual Hindi summary
- **No language selection required** - Both languages generated automatically
- **Side-by-side players** - Easy access to both audio versions

## 🔌 API Documentation

The Flask backend provides RESTful endpoints for all core functionality:

### Base URL
```
http://localhost:5000/api
```

### Endpoints

#### 📰 GET /api/news
Fetch news articles for a company.

**Parameters:**
- `company` (query): Company name to search

**Example:**
```bash
curl "http://localhost:5000/api/news?company=Tesla"
```

#### 🕷️ POST /api/scrape
Scrape content from article URLs.

**Request Body:**
```json
{
  "company": "Tesla",
  "articles": [
    {"title": "Article Title", "url": "https://example.com/article"}
  ]
}
```

#### 🧠 POST /api/analyze
Analyze articles for sentiment and topics.

**Request Body:**
```json
{
  "company": "Tesla",
  "articles": [
    {
      "title": "Article Title",
      "content": "Article content...",
      "date": "2025-01-01",
      "source": "example.com"
    }
  ]
}
```

#### 🎙️ POST /api/tts
Generate text-to-speech audio.

**Request Body:**
```json
{
  "text": "Text to convert to speech",
  "language": "English"  // or "Hindi"
}
```

**Response:**
```json
{
  "audio_file": "/path/to/audio.mp3",
  "filename": "speech_english_uuid.mp3"
}
```

#### 🔊 GET /api/audio/<filename>
Serve generated audio files.

## 🛠️ Technology Stack

### Backend
- **Flask** - RESTful API framework
- **Waitress** - Production WSGI server
- **Transformers** - Hugging Face models for NLP
- **spaCy** - Named Entity Recognition
- **VADER Sentiment** - Rule-based sentiment analysis
- **gTTS** - Google Text-to-Speech
- **BeautifulSoup** - Web scraping
- **scikit-learn** - TF-IDF vectorization

### Frontend
- **Streamlit** - Interactive web application
- **Plotly** - Data visualization
- **Pandas** - Data manipulation

### ML Models
- **facebook/bart-large-cnn** - Text summarization
- **distilbert-base-uncased-finetuned-sst-2-english** - Sentiment analysis
- **en_core_web_sm** - spaCy English model

## 📋 Dependencies

### Core Requirements
```
streamlit==1.31.0
flask==2.3.3
transformers==4.38.0
torch>=1.9.0
spacy==3.7.4
nltk==3.8.1
pandas==2.1.3
plotly==5.18.0
requests==2.31.0
beautifulsoup4==4.12.2
vaderSentiment==3.3.2
gtts==2.3.2
waitress==3.0.2
scikit-learn>=1.3.0
```

See `requirements.txt` for complete dependency list.

## 🧪 Testing

Run the unit tests:
```bash
python -m unittest discover tests
```

Test individual components:
```bash
# Test utility functions
python -m unittest tests.test_utils

# Test API endpoints (ensure API is running)
curl -X GET "http://localhost:5000/api/news?company=Tesla"
```

## 🚀 Deployment Options

### Option 1: Streamlit Cloud
1. Push code to GitHub
2. Connect repository to [Streamlit Cloud](https://streamlit.io/cloud)
3. Configure environment variables
4. Deploy with one click

### Option 2: Heroku
1. Create `Procfile`:
```
web: streamlit run app.py --server.port=$PORT --server.address=0.0.0.0
api: python api.py
```
2. Deploy using Heroku CLI

### Option 3: Docker
```dockerfile
FROM python:3.9-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
RUN python -m spacy download en_core_web_sm
COPY . .
EXPOSE 8501 5000
CMD ["streamlit", "run", "app.py"]
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Development Guidelines
- Follow PEP 8 style guidelines
- Add unit tests for new features
- Update documentation for API changes
- Test bilingual TTS functionality

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgements

- [Hugging Face](https://huggingface.co/) - Transformer models and tokenizers
- [Google Text-to-Speech](https://gtts.readthedocs.io/) - Bilingual audio generation
- [Streamlit](https://streamlit.io/) - Interactive web application framework
- [Flask](https://flask.palletsprojects.com/) - RESTful API backend
- [VADER Sentiment](https://github.com/cjhutto/vaderSentiment) - Rule-based sentiment analysis
- [spaCy](https://spacy.io/) - Industrial-strength NLP

## 📞 Support

- 🐛 **Bug Reports**: [GitHub Issues](https://github.com/yourusername/news-analyzer-bilingual/issues)
- 💡 **Feature Requests**: [GitHub Discussions](https://github.com/yourusername/news-analyzer-bilingual/discussions)
- 📧 **Contact**: your.email@example.com

---

**Made with ❤️ for bilingual news analysis**
