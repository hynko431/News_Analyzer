"""
Utility functions for news extraction, summarization, and analysis.
"""
import logging
import re
import time
import urllib.parse
from datetime import datetime
from urllib.parse import urlparse

import feedparser
import nltk
import numpy as np
import requests
import spacy
from bs4 import BeautifulSoup
from nltk.corpus import stopwords
from sklearn.feature_extraction.text import TfidfVectorizer
from transformers import pipeline
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Download NLTK data
try:
    nltk.download('stopwords', quiet=True)
    nltk.download('punkt', quiet=True)
except Exception as e:
    logging.warning(f"Error downloading NLTK data: {e}")

# Load spaCy model
try:
    nlp = spacy.load('en_core_web_sm')
except OSError:
    logging.warning("Downloading spaCy model...")
    import subprocess
    subprocess.run(["python", "-m", "spacy", "download", "en_core_web_sm"], check=True)
    nlp = spacy.load('en_core_web_sm')

# News sources for RSS feeds
NEWS_SOURCES = {
    'google_news': 'https://news.google.com/rss/search?q={query}',
    'bing_news': 'https://www.bing.com/news/search?q={query}&format=rss'
}

def sanitize_text(text):
    """Clean extracted text content."""
    if not text:
        return ""
    return re.sub(r'\s+', ' ', text).strip()

def extract_date(soup):
    """Extract publication date from HTML."""
    # Try common date meta tags
    date_patterns = [
        ('meta[property="article:published_time"]', 'content'),
        ('meta[name="pubdate"]', 'content'),
        ('meta[name="publishdate"]', 'content'),
        ('meta[name="timestamp"]', 'content'),
        ('time', 'datetime')
    ]
    
    for selector, attribute in date_patterns:
        date_tag = soup.select_one(selector)
        if date_tag and date_tag.get(attribute):
            try:
                return date_tag[attribute]
            except Exception:
                pass
    
    # Fallback to current date if not found
    return datetime.now().strftime('%Y-%m-%d')

def extract_source(soup, url):
    """Extract source name from HTML or URL."""
    # Try to get from meta tags
    source_tag = soup.select_one('meta[property="og:site_name"]')
    if source_tag and source_tag.get('content'):
        return source_tag['content']
    
    # Fallback to domain name
    domain = urlparse(url).netloc
    return domain.replace('www.', '')

def search_news_articles(company_name, num_articles=15):
    """
    Search for news articles related to the company.
    Returns a list of URLs to be scraped.
    """
    # Get articles from RSS feeds
    articles = fetch_news_feeds(company_name, num_articles)
    
    # If not enough articles found, return the available ones
    return articles[:num_articles]

def fetch_news_feeds(query, num_results=15):
    """Fetch news from various RSS feeds."""
    articles = []
    for source, url_template in NEWS_SOURCES.items():
        try:
            feed_url = url_template.format(query=urllib.parse.quote(query))
            feed = feedparser.parse(feed_url)
            
            for entry in feed.entries[:num_results//2]:
                articles.append({
                    'title': entry.title,
                    'url': entry.link,
                    'published': getattr(entry, 'published', datetime.now().strftime('%Y-%m-%d'))
                })
                
        except Exception as e:
            logging.error(f"Error fetching from {source}: {str(e)}")
    
    return articles

def scrape_article(url):
    """
    Scrape article content from a given URL using BeautifulSoup.
    Returns article title, content, publication date, and source.
    """
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'lxml')
        
        # Extract article components
        title = soup.find('h1')
        if title:
            title = title.text.strip()
        else:
            title = soup.title.text if soup.title else "No title found"
        
        # Find article body - try common article selectors
        article_selectors = [
            'article', 
            'div[class*=article]', 
            'div[class*=content]',
            'div[class*=story]',
            'div.post'
        ]
        
        article_body = None
        for selector in article_selectors:
            article_body = soup.select_one(selector)
            if article_body:
                break
        
        # Fallback to all paragraphs if no article container found
        if not article_body:
            article_body = soup
            
        content = ' '.join([p.text for p in article_body.find_all('p')])
        date = extract_date(soup)
        source = extract_source(soup, url)
        
        # Ensure minimum content
        if len(content) < 100:
            content = ' '.join([div.text for div in article_body.find_all('div') 
                              if len(div.text) > 100])
        
        # Final sanity check
        if not content or len(content) < 50:
            return None
            
        return {
            'title': sanitize_text(title),
            'content': sanitize_text(content),
            'date': date,
            'source': source,
            'url': url
        }
    except Exception as e:
        logging.error(f"Error scraping {url}: {str(e)}")
        return None

def summarize_text(text, max_length=150):
    """
    Summarize text using a transformer model.
    Returns a concise summary of the input text.
    """
    if not text or len(text) < 100:
        return text
        
    try:
        summarizer = pipeline("summarization", model="facebook/bart-large-cnn")
        
        # Handle long texts by summarizing in chunks
        if len(text) > 1024:
            chunks = [text[i:i+1024] for i in range(0, len(text), 1024)]
            summaries = []
            
            for chunk in chunks[:3]:  # Limit to first 3 chunks to avoid too long processing
                summary = summarizer(chunk, 
                                     max_length=max_length//len(chunks[:3]), 
                                     min_length=30,
                                     do_sample=False)[0]['summary_text']
                summaries.append(summary)
                
            return ' '.join(summaries)
        else:
            summary = summarizer(text, 
                                max_length=max_length, 
                                min_length=50,
                                do_sample=False)[0]['summary_text']
            return summary
            
    except Exception as e:
        logging.error(f"Error in text summarization: {str(e)}")
        # Fallback to simple extractive summarization
        sentences = nltk.sent_tokenize(text)
        return ' '.join(sentences[:3]) if sentences else text

def analyze_sentiment(text):
    """
    Analyze sentiment using a hybrid approach (VADER + transformer model).
    Returns sentiment label and score.
    """
    if not text:
        return {"label": "Neutral", "score": 0.0}
        
    try:
        # Rule-based approach (VADER)
        analyzer = SentimentIntensityAnalyzer()
        vader_scores = analyzer.polarity_scores(text)
        
        # Transformer-based approach - use a smaller model for speed
        classifier = pipeline("sentiment-analysis", model="distilbert-base-uncased-finetuned-sst-2-english")
        
        # Process shorter text for efficiency
        shortened_text = text[:512]
        transformer_result = classifier(shortened_text)[0]
        
        # Normalize transformer scores
        transformer_score = transformer_result['score']
        if transformer_result['label'] == 'NEGATIVE':
            transformer_score = -transformer_score
            
        # Combine results (weighted average)
        final_score = (0.4 * vader_scores['compound'] + 0.6 * transformer_score)
        
        # Determine sentiment label
        if final_score > 0.1:
            label = "Positive"
        elif final_score < -0.1:
            label = "Negative"
        else:
            label = "Neutral"
        
        return {
            'label': label,
            'score': final_score,
            'vader_score': vader_scores['compound'],
            'transformer_score': transformer_score
        }
        
    except Exception as e:
        logging.error(f"Error in sentiment analysis: {str(e)}")
        # Fallback to just VADER if transformer fails
        try:
            analyzer = SentimentIntensityAnalyzer()
            vader_scores = analyzer.polarity_scores(text)
            compound = vader_scores['compound']
            
            if compound > 0.05:
                return {"label": "Positive", "score": compound}
            elif compound < -0.05:
                return {"label": "Negative", "score": compound}
            else:
                return {"label": "Neutral", "score": compound}
        except:
            return {"label": "Neutral", "score": 0.0}

def extract_topics(text, num_topics=5):
    """
    Extract main topics/keywords from text using TF-IDF and NER.
    Returns a list of key topics.
    """
    if not text or len(text) < 100:
        return ["Not enough content"]
        
    try:
        # Extract named entities
        doc = nlp(text[:5000])  # Limit text length for processing speed
        entities = []
        
        for ent in doc.ents:
            if ent.label_ in ['ORG', 'PRODUCT', 'PERSON', 'GPE', 'LOC', 'MONEY', 'PERCENT']:
                entities.append(ent.text)
        
        # Use TF-IDF for keyword extraction
        stop_words = set(stopwords.words('english'))
        vectorizer = TfidfVectorizer(stop_words='english', ngram_range=(1, 2), max_features=10)
        
        try:
            tfidf_matrix = vectorizer.fit_transform([text])
            feature_names = vectorizer.get_feature_names_out()
            dense = tfidf_matrix.todense()
            scores = dense[0].tolist()[0]
            
            # Create a dictionary of words and their TF-IDF scores
            word_scores = {feature_names[i]: scores[i] for i in range(len(feature_names))}
            
            # Sort by score and get top keywords
            sorted_words = sorted(word_scores.items(), key=lambda x: x[1], reverse=True)
            keywords = [word for word, score in sorted_words[:num_topics]]
        except:
            keywords = []
        
        # Combine named entities and keywords, prioritizing entities
        combined = list(set(entities + keywords))
        
        # Return top topics, ensuring we don't exceed requested number
        return combined[:num_topics]
        
    except Exception as e:
        logging.error(f"Error extracting topics: {str(e)}")
        return ["Topic extraction failed"]

def compare_articles(articles):
    """
    Compare sentiment and topics across multiple articles.
    Returns comparative analysis results.
    """
    if not articles:
        return {
            "Sentiment Distribution": {"Positive": 0, "Negative": 0, "Neutral": 0},
            "Coverage Differences": [],
            "Topic Overlap": {"Common Topics": [], "Unique Topics": []}
        }
    
    try:
        # Aggregate sentiment data
        sentiment_distribution = {
            "Positive": sum(1 for a in articles if a.get('sentiment', {}).get('label') == "Positive"),
            "Negative": sum(1 for a in articles if a.get('sentiment', {}).get('label') == "Negative"),
            "Neutral": sum(1 for a in articles if a.get('sentiment', {}).get('label') == "Neutral")
        }
        
        # Find topic overlap and unique topics
        all_topics = [set(a.get('topics', [])) for a in articles if 'topics' in a]
        common_topics = set.intersection(*all_topics) if all_topics else set()
        
        # Handle empty intersection
        if not common_topics and all_topics:
            # Try to find topics that appear in at least 30% of articles
            topic_counts = {}
            for topic_set in all_topics:
                for topic in topic_set:
                    topic_counts[topic] = topic_counts.get(topic, 0) + 1
            
            threshold = max(2, len(all_topics) * 0.3)  # At least 30% of articles or 2, whichever is larger
            common_topics = {topic for topic, count in topic_counts.items() if count >= threshold}
        
        # Generate coverage differences and impact analysis
        coverage_differences = []
        for i in range(len(articles)):
            for j in range(i+1, min(i+3, len(articles))):  # Compare with next 2 articles to avoid too many comparisons
                if articles[i].get('sentiment', {}).get('label') != articles[j].get('sentiment', {}).get('label'):
                    # Get top 3 topics for each article (or fewer if not available)
                    topics_i = articles[i].get('topics', [])[:3]
                    topics_j = articles[j].get('topics', [])[:3]
                    
                    comparison = (f"Article '{articles[i].get('title', f'Article {i+1}')}' has "
                                f"{articles[i].get('sentiment', {}).get('label', 'Unknown')} sentiment about "
                                f"{', '.join(topics_i) if topics_i else 'the subject'}, while "
                                f"Article '{articles[j].get('title', f'Article {j+1}')}' has "
                                f"{articles[j].get('sentiment', {}).get('label', 'Unknown')} sentiment about "
                                f"{', '.join(topics_j) if topics_j else 'the subject'}.")
                    
                    # Generate impact analysis
                    impact = generate_impact_analysis(articles[i], articles[j])
                    
                    coverage_differences.append({
                        "Comparison": comparison,
                        "Impact": impact
                    })
        
        # Get unique topics per article
        unique_topics = []
        for i, topic_set in enumerate(all_topics):
            unique = topic_set - common_topics
            unique_topics.append(list(unique))
        
        return {
            "Sentiment Distribution": sentiment_distribution,
            "Coverage Differences": coverage_differences[:5],  # Limit to top 5 differences
            "Topic Overlap": {
                "Common Topics": list(common_topics),
                "Unique Topics": unique_topics
            }
        }
        
    except Exception as e:
        logging.error(f"Error in comparative analysis: {str(e)}")
        return {
            "Sentiment Distribution": {"Positive": 0, "Negative": 0, "Neutral": 0},
            "Coverage Differences": [],
            "Topic Overlap": {"Common Topics": [], "Unique Topics": []}
        }

def generate_impact_analysis(article1, article2):
    """Generate insights on how different coverage might impact perception."""
    try:
        sentiment1 = article1.get('sentiment', {}).get('label', 'Unknown')
        sentiment2 = article2.get('sentiment', {}).get('label', 'Unknown')
        
        if sentiment1 == sentiment2:
            return "Both articles share similar sentiment, reinforcing the same perception."
            
        if sentiment1 == "Positive" and sentiment2 == "Negative":
            return ("The conflicting sentiment between these articles may create market uncertainty. "
                   "Investors might need to evaluate both perspectives before making decisions.")
        
        if sentiment1 == "Negative" and sentiment2 == "Positive":
            return ("The contrasting views present a complex picture. "
                   "This divergence suggests the company's situation has multiple interpretations.")
        
        if "Neutral" in [sentiment1, sentiment2]:
            other = sentiment1 if sentiment2 == "Neutral" else sentiment2
            return f"The {other.lower()} sentiment in one article is counterbalanced by a neutral perspective in the other."
            
        return "The articles present different aspects of the company's situation."
        
    except Exception as e:
        logging.error(f"Error in impact analysis: {str(e)}")
        return "Impact analysis not available."

def get_overall_sentiment(analysis_data):
    """Determine overall sentiment based on distribution."""
    if not analysis_data:
        return "Neutral"
        
    try:
        sentiment_dist = analysis_data.get("Sentiment Distribution", {})
        total = sum(sentiment_dist.values())
        
        if total == 0:
            return "Neutral"
            
        positive_ratio = sentiment_dist.get("Positive", 0) / total
        negative_ratio = sentiment_dist.get("Negative", 0) / total
        
        if positive_ratio > 0.6:
            return "Very Positive"
        elif positive_ratio > 0.4:
            return "Moderately Positive"
        elif negative_ratio > 0.6:
            return "Very Negative"
        elif negative_ratio > 0.4:
            return "Moderately Negative"
        else:
            return "Mixed or Neutral"
            
    except Exception as e:
        logging.error(f"Error calculating overall sentiment: {str(e)}")
        return "Neutral"

def generate_final_sentiment_text(company_name, analysis_data):
    """Generate a human-readable final sentiment analysis."""
    overall = get_overall_sentiment(analysis_data)
    
    try:
        # Count articles by sentiment
        sentiment_dist = analysis_data.get("Sentiment Distribution", {})
        total = sum(sentiment_dist.values())
        
        if total == 0:
            return f"No reliable sentiment data available for {company_name}."
            
        # Generate descriptive text
        if overall == "Very Positive":
            return (f"{company_name}'s latest news coverage is overwhelmingly positive. "
                   "The company is receiving favorable attention which may indicate strong performance.")
        elif overall == "Moderately Positive":
            return (f"{company_name}'s recent news coverage leans positive. "
                   "The company appears to be performing well despite some challenges.")
        elif overall == "Very Negative":
            return (f"{company_name}'s latest news coverage is predominantly negative. "
                   "The company may be facing significant challenges that could impact its performance.")
        elif overall == "Moderately Negative":
            return (f"{company_name}'s recent news coverage tends to be negative. "
                   "The company appears to be facing some challenges that warrant attention.")
        else:  # Mixed or Neutral
            return (f"{company_name}'s recent news coverage shows mixed sentiment. "
                   "The company has both positive developments and challenges to navigate.")
                   
    except Exception as e:
        logging.error(f"Error generating final sentiment text: {str(e)}")
        return f"Analysis of {company_name}'s recent news coverage is inconclusive."