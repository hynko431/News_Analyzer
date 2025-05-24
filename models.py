"""
Model loading and utility functions for the News Analysis application.
Provides centralized access to ML models for sentiment analysis and summarization.
"""
import logging
from functools import lru_cache

from transformers import pipeline

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class ModelLoader:
    """Singleton class for loading and caching NLP models."""
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.models = {}
        return cls._instance
    
    def get_sentiment_model(self):
        """Get sentiment analysis model."""
        if 'sentiment' not in self.models:
            try:
                logging.info("Loading sentiment analysis model...")
                self.models['sentiment'] = pipeline(
                    "sentiment-analysis", 
                    model="distilbert-base-uncased-finetuned-sst-2-english"
                )
                logging.info("Sentiment analysis model loaded successfully")
            except Exception as e:
                logging.error(f"Error loading sentiment model: {str(e)}")
                return None
        return self.models['sentiment']
    
    def get_sentiment_model(self):
        """Get sentiment analysis model with optimized memory usage."""
        if 'sentiment' not in self.models:
            try:
                logging.info("Loading sentiment analysis model...")
                # Use smaller model and disable GPU if not needed
                self.models['sentiment'] = pipeline(
                    "sentiment-analysis", 
                    model="distilbert-base-uncased-finetuned-sst-2-english",
                    device=-1  # Force CPU usage
                )
                logging.info("Sentiment analysis model loaded successfully")
            except Exception as e:
                logging.error(f"Error loading sentiment model: {str(e)}")
                return None
        return self.models['sentiment']
    

@lru_cache(maxsize=100)
def cached_summarize(text, max_length=150):
    """Cached wrapper for text summarization."""
    loader = ModelLoader()
    summarizer = loader.get_summarization_model()
    
    if not summarizer:
        # Fallback to simple extraction if model fails
        sentences = text.split('. ')
        return '. '.join(sentences[:3]) + '.'
    
    try:
        if len(text) > 1024:
            chunks = [text[i:i+1024] for i in range(0, min(len(text), 3072), 1024)]
            summaries = []
            
            for chunk in chunks:
                summary = summarizer(
                    chunk, 
                    max_length=max_length//len(chunks), 
                    min_length=30,
                    do_sample=False
                )[0]['summary_text']
                summaries.append(summary)
                
            return ' '.join(summaries)
        else:
            summary = summarizer(
                text, 
                max_length=max_length, 
                min_length=50,
                do_sample=False
            )[0]['summary_text']
            return summary
    except Exception as e:
        logging.error(f"Error in summarization: {str(e)}")
        # Fallback to simple extraction
        sentences = text.split('. ')
        return '. '.join(sentences[:3]) + '.'

@lru_cache(maxsize=100)
def cached_sentiment_analysis(text):
    """Cached wrapper for sentiment analysis."""
    loader = ModelLoader()
    classifier = loader.get_sentiment_model()
    
    if not classifier or not text:
        return {"label": "Neutral", "score": 0.0}
    
    try:
        # Truncate text for model maximum input size
        shortened_text = text[:512]
        result = classifier(shortened_text)[0]
        
        return {
            "label": "Positive" if result['label'] == 'POSITIVE' else "Negative",
            "score": result['score'] if result['label'] == 'POSITIVE' else -result['score']
        }
    except Exception as e:
        logging.error(f"Error in sentiment analysis: {str(e)}")
        return {"label": "Neutral", "score": 0.0}