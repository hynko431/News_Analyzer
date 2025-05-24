"""
Unit tests for utility functions in the News Analysis application.
"""
import unittest
from unittest.mock import patch, MagicMock

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from communication.utils import sanitize_text, extract_topics, analyze_sentiment, scrape_article, summarize_text

class TestUtils(unittest.TestCase):
    """Test cases for utility functions."""
    
    def test_sanitize_text(self):
        """Test text sanitization."""
        dirty_text = "This  has  multiple   spaces \n and\tlinebreaks"
        clean_text = sanitize_text(dirty_text)
        self.assertEqual(clean_text, "This has multiple spaces and linebreaks")
        
        self.assertEqual(sanitize_text(None), "")
        self.assertEqual(sanitize_text(""), "")
    
    def test_extract_topics(self):
        """Test topic extraction."""
        text = "Apple Inc. is developing new technologies while Microsoft focuses on cloud computing. Both companies are investing in artificial intelligence."
        topics = extract_topics(text, num_topics=3)
        
        self.assertIsInstance(topics, list)
        self.assertLessEqual(len(topics), 3)
        
        # Test with empty text
        self.assertEqual(extract_topics("", num_topics=3), ["Not enough content"])
        self.assertEqual(extract_topics(None, num_topics=3), ["Not enough content"])
    
    @patch('utils.SentimentIntensityAnalyzer')
    @patch('utils.pipeline')
    def test_analyze_sentiment(self, mock_pipeline, mock_vader):
        """Test sentiment analysis."""
        # Mock VADER
        mock_vader_instance = MagicMock()
        mock_vader_instance.polarity_scores.return_value = {
            'compound': 0.8, 'neg': 0.0, 'neu': 0.2, 'pos': 0.8
        }
        mock_vader.return_value = mock_vader_instance
        
        # Mock transformer pipeline
        mock_classifier = MagicMock()
        mock_classifier.return_value = [{'label': 'POSITIVE', 'score': 0.9}]
        mock_pipeline.return_value = mock_classifier
        
        # Test positive sentiment
        result = analyze_sentiment("This is a great product!")
        self.assertEqual(result['label'], "Positive")
        self.assertGreater(result['score'], 0)
        
        # Test with empty text
        result = analyze_sentiment("")
        self.assertEqual(result['label'], "Neutral")
        self.assertEqual(result['score'], 0.0)
    
    @patch('utils.requests.get')
    def test_scrape_article(self, mock_get):
        """Test article scraping."""
        # Mock response
        mock_response = MagicMock()
        mock_response.text = """
        <html>
            <head><title>Test Article</title></head>
            <body>
                <h1>Test Article Heading</h1>
                <article>
                    <p>This is a test paragraph.</p>
                    <p>This is another paragraph.</p>
                </article>
            </body>
        </html>
        """
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        result = scrape_article("https://example.com/article")
        
        self.assertIsNotNone(result)
        self.assertIn('title', result)
        self.assertIn('content', result)
        self.assertIn('date', result)
        self.assertIn('source', result)
        
        # Test with failed request
        mock_get.side_effect = Exception("Connection error")
        result = scrape_article("https://example.com/error")
        self.assertIsNone(result)
    
    @patch('utils.pipeline')
    def test_summarize_text(self, mock_pipeline):
        """Test text summarization."""
        # Mock summarizer
        mock_summarizer = MagicMock()
        mock_summarizer.return_value = [{'summary_text': 'This is a summary.'}]
        mock_pipeline.return_value = mock_summarizer
        
        result = summarize_text("This is a long text that needs to be summarized. It contains multiple sentences that should be condensed into a shorter version while retaining the main points.")
        
        self.assertEqual(result, 'This is a summary.')
        
        # Test with short text
        short_text = "This is short."
        result = summarize_text(short_text)
        self.assertEqual(result, short_text)
        
        # Test with empty text
        self.assertEqual(summarize_text(""), "")
        self.assertEqual(summarize_text(None), None)

if __name__ == '__main__':
    unittest.main()