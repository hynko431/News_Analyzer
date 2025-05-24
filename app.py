"""
Main Streamlit application for News Analysis and Text-to-Speech.
Provides an interactive dashboard for analyzing company news.
"""

import io
import os
import requests
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from PIL import Image

# API base URL - change this if your API is running on a different host
API_BASE_URL = "http://localhost:5000/api"
# For Streamlit Cloud/Hugging Face, use relative URL:
# API_BASE_URL = "/api"  # When both Streamlit and Flask run on the same server

# Configure page
st.set_page_config(
    page_title="Company News Analyzer",
    page_icon="📰",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Apply custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #1E88E5;
        text-align: center;
        margin-bottom: 1rem;
    }
    .sub-header {
        font-size: 1.5rem;
        color: #0D47A1;
        margin-top: 2rem;
    }
    .card {
        padding: 1.5rem;
        border-radius: 0.5rem;
        margin: 1rem 0;
        background-color: #f8f9fa;
        border: 1px solid #dee2e6;
        color: #000000;
    }
</style>
""", unsafe_allow_html=True)

@st.cache_data(ttl=3600)  # Cache results for 1 hour
def fetch_news(company_name):
    """Fetch news articles from API."""
    try:
        response = requests.get(f"{API_BASE_URL}/news?company={company_name}")
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Error fetching news: {str(e)}")
        return None

@st.cache_data(ttl=3600)  # Cache results for 1 hour
def scrape_articles(news_data):
    """Scrape article content from URLs."""
    try:
        response = requests.post(f"{API_BASE_URL}/scrape", json=news_data)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Error scraping articles: {str(e)}")
        return None

@st.cache_data(ttl=3600)  # Cache results for 1 hour
def analyze_articles(scraped_data):
    """Analyze article content for sentiment and topics."""
    try:
        response = requests.post(f"{API_BASE_URL}/analyze", json=scraped_data)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Error analyzing articles: {str(e)}")
        return None

def generate_audio(text, language):
    """Generate text-to-speech audio."""
    try:
        response = requests.post(
            f"{API_BASE_URL}/tts",
            json={"text": text, "language": language}
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Error generating audio: {str(e)}")
        return None

def generate_dual_audio(english_text, hindi_text=None):
    """Generate text-to-speech audio in both English and Hindi."""
    results = {
        "english": {"success": False, "audio_file": None, "filename": None, "error": None},
        "hindi": {"success": False, "audio_file": None, "filename": None, "error": None}
    }

    # Generate English audio
    try:
        english_response = generate_audio(english_text, "English")
        if english_response:
            results["english"]["success"] = True
            results["english"]["audio_file"] = english_response.get('audio_file')
            results["english"]["filename"] = english_response.get('filename')
        else:
            results["english"]["error"] = "Failed to generate English audio"
    except Exception as e:
        results["english"]["error"] = f"English audio error: {str(e)}"

    # Generate Hindi audio
    # If no Hindi text provided, create a simple Hindi template
    if not hindi_text:
        # Extract company name from English text for Hindi template
        company_match = english_text.split("for ")[1].split(":")[0] if "for " in english_text else "कंपनी"
        hindi_text = f"{company_match} की समाचार विश्लेषण रिपोर्ट तैयार है। यह रिपोर्ट कंपनी की हाल की खबरों का विश्लेषण प्रस्तुत करती है।"

    try:
        hindi_response = generate_audio(hindi_text, "Hindi")
        if hindi_response:
            results["hindi"]["success"] = True
            results["hindi"]["audio_file"] = hindi_response.get('audio_file')
            results["hindi"]["filename"] = hindi_response.get('filename')
        else:
            results["hindi"]["error"] = "Failed to generate Hindi audio"
    except Exception as e:
        results["hindi"]["error"] = f"Hindi audio error: {str(e)}"

    return results

def display_sentiment_distribution(data):
    """Display sentiment distribution chart."""
    sentiment_dist = data.get("comparative_sentiment_score", {}).get("Sentiment Distribution", {})

    if not sentiment_dist:
        st.warning("No sentiment data available")
        return

    # Convert dict to dataframe
    df = pd.DataFrame({
        "Sentiment": list(sentiment_dist.keys()),
        "Count": list(sentiment_dist.values())
    })

    # Create pie chart
    fig = px.pie(
        df,
        values="Count",
        names="Sentiment",
        title="Sentiment Distribution",
        color="Sentiment",
        color_discrete_map={
            "Positive": "#4CAF50",
            "Negative": "#F44336",
            "Neutral": "#9E9E9E"
        }
    )

    fig.update_traces(textposition='inside', textinfo='percent+label')

    st.plotly_chart(fig, use_container_width=True)

def display_sentiment_scores(articles):
    """Display sentiment scores for each article."""
    if not articles:
        st.warning("No articles available for sentiment score visualization")
        return

    # Extract sentiment scores and article titles
    data = []
    for i, article in enumerate(articles):
        sentiment = article.get("sentiment", {})
        if sentiment:
            data.append({
                "Article": article.get("title", f"Article {i+1}")[:30] + "...",
                "Score": sentiment.get("score", 0),
                "Label": sentiment.get("label", "Neutral")
            })

    if not data:
        st.warning("No sentiment scores available")
        return

    df = pd.DataFrame(data)

    # Create horizontal bar chart
    fig = px.bar(
        df,
        x="Score",
        y="Article",
        color="Label",
        orientation="h",
        title="Sentiment Scores by Article",
        color_discrete_map={
            "Positive": "#4CAF50",
            "Negative": "#F44336",
            "Neutral": "#9E9E9E"
        }
    )

    fig.update_layout(yaxis={"categoryorder": "total ascending"})

    st.plotly_chart(fig, use_container_width=True)

def display_topic_network(articles):
    """Display topic network visualization."""
    if not articles:
        st.warning("No topics available for visualization")
        return

    # Extract topics
    all_topics = {}
    for i, article in enumerate(articles):
        topics = article.get("topics", [])
        for topic in topics:
            if topic in all_topics:
                all_topics[topic] += 1
            else:
                all_topics[topic] = 1

    # Sort topics by frequency
    sorted_topics = dict(sorted(all_topics.items(), key=lambda x: x[1], reverse=True)[:10])

    if not sorted_topics:
        st.warning("No topics found")
        return

    # Create bar chart
    df = pd.DataFrame({
        "Topic": list(sorted_topics.keys()),
        "Frequency": list(sorted_topics.values())
    })

    fig = px.bar(
        df,
        x="Topic",
        y="Frequency",
        title="Most Common Topics",
        color="Frequency",
        color_continuous_scale="Viridis"
    )

    st.plotly_chart(fig, use_container_width=True)

def main():
    """Main application function."""
    # Display header
    st.markdown('<h1 class="main-header">Company News Analyzer</h1>', unsafe_allow_html=True)
    st.markdown("""
    This application analyzes recent news articles about a company to determine sentiment and extract key topics.
    It automatically provides bilingual text-to-speech summaries in both English and Hindi.
    """)

    # Sidebar
    st.sidebar.image("static/logo.png", width=150)
    st.sidebar.title("Controls")

    # Company input
    company_name = st.sidebar.text_input("Enter Company Name:", "Tesla")

    # Number of articles
    num_articles = st.sidebar.slider("Number of Articles:", min_value=5, max_value=20, value=10)

    # Analysis process
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        fetch_button = st.button("1. Fetch News", use_container_width=True)
    with col2:
        scrape_button = st.button("2. Scrape Content", use_container_width=True)
    with col3:
        analyze_button = st.button("3. Analyze Articles", use_container_width=True)
    with col4:
        summarize_button = st.button("4. Generate Summary", use_container_width=True)

    # Initialize session state
    if 'news_data' not in st.session_state:
        st.session_state.news_data = None
    if 'scraped_data' not in st.session_state:
        st.session_state.scraped_data = None
    if 'analysis_data' not in st.session_state:
        st.session_state.analysis_data = None
    if 'summary_text' not in st.session_state:
        st.session_state.summary_text = ""
    if 'dual_audio' not in st.session_state:
        st.session_state.dual_audio = None

    # Step 1: Fetch News
    if fetch_button or ('news_data' in st.session_state and st.session_state.news_data):
        with st.spinner("Fetching news articles..."):
            if fetch_button:
                st.session_state.news_data = fetch_news(company_name)

            if st.session_state.news_data:
                st.success(f"Found {len(st.session_state.news_data.get('articles', []))} articles about {company_name}")

                with st.expander("View Article URLs"):
                    for i, article in enumerate(st.session_state.news_data.get('articles', [])):
                        st.write(f"{i+1}. [{article.get('title')}]({article.get('url')})")

    # Step 2: Scrape Content
    if scrape_button or ('scraped_data' in st.session_state and st.session_state.scraped_data):
        if not st.session_state.news_data and scrape_button:
            st.warning("Please fetch news first")
        else:
            with st.spinner("Scraping article content..."):
                if scrape_button:
                    st.session_state.scraped_data = scrape_articles(st.session_state.news_data)

                if st.session_state.scraped_data:
                    st.success(f"Scraped content from {len(st.session_state.scraped_data.get('articles', []))} articles")

                    with st.expander("View Article Content"):
                        for i, article in enumerate(st.session_state.scraped_data.get('articles', [])):
                            st.markdown(f"""
                            **{i+1}. {article.get('title')}**
                            Source: {article.get('source')}
                            Date: {article.get('date')}
                            Content: {article.get('content')[:200]}...
                            """)

    # Step 3: Analyze Articles
    if analyze_button or ('analysis_data' in st.session_state and st.session_state.analysis_data):
        if not st.session_state.scraped_data and analyze_button:
            st.warning("Please scrape articles first")
        else:
            with st.spinner("Analyzing articles..."):
                if analyze_button:
                    st.session_state.analysis_data = analyze_articles(st.session_state.scraped_data)

                if st.session_state.analysis_data:
                    st.success("Analysis complete!")

                    # Display final sentiment analysis
                    st.markdown('<h2 class="sub-header">Overall Sentiment Analysis</h2>', unsafe_allow_html=True)

                    with st.container():
                        st.markdown(f"""
                        <div class="card">
                            <h3 style="color: #000000;">{st.session_state.analysis_data.get('company')}</h3>
                            <p style="color: #000000;">{st.session_state.analysis_data.get('final_sentiment_analysis')}</p>
                        </div>
                        """, unsafe_allow_html=True)

                    # Display charts
                    col1, col2 = st.columns(2)

                    with col1:
                        display_sentiment_distribution(st.session_state.analysis_data)

                    with col2:
                        display_sentiment_scores(st.session_state.analysis_data.get('articles', []))

                    # Display topic network
                    display_topic_network(st.session_state.analysis_data.get('articles', []))

                    # Display comparative analysis
                    st.markdown('<h2 class="sub-header">Comparative Analysis</h2>', unsafe_allow_html=True)

                    coverage_differences = st.session_state.analysis_data.get('comparative_sentiment_score', {}).get('Coverage Differences', [])

                    if coverage_differences:
                        for diff in coverage_differences:
                            st.markdown(f"""
                            <div class="card">
                                <p style="color: #000000;">{diff.get('Comparison')}</p>
                                <p style="color: #000000;"><strong>Impact:</strong> {diff.get('Impact')}</p>
                            </div>
                            """, unsafe_allow_html=True)
                    else:
                        st.info("No significant coverage differences found")

                    # Generate session summary text
                    if not st.session_state.summary_text:
                        company = st.session_state.analysis_data.get('company')
                        sentiment = st.session_state.analysis_data.get('final_sentiment_analysis')

                        # Extract common topics
                        common_topics = st.session_state.analysis_data.get('comparative_sentiment_score', {}).get('Topic Overlap', {}).get('Common Topics', [])
                        topics_text = ", ".join(common_topics[:5]) if common_topics else "various topics"

                        st.session_state.summary_text = f"""
                        Summary of news analysis for {company}: {sentiment} The articles mainly discuss {topics_text}.
                        """

    # Step 4: Generate Audio Summary
    if summarize_button or ('dual_audio' in st.session_state and st.session_state.dual_audio):
        if not st.session_state.analysis_data and summarize_button:
            st.warning("Please analyze articles first")
        else:
            with st.spinner("Generating bilingual audio summaries..."):
                if summarize_button:
                    # Create summary text if not already created
                    if not st.session_state.summary_text:
                        st.session_state.summary_text = f"No analysis data available for {company_name}"

                    # Generate dual audio
                    st.session_state.dual_audio = generate_dual_audio(st.session_state.summary_text)

                if st.session_state.dual_audio:
                    # Check if at least one audio generation was successful
                    english_success = st.session_state.dual_audio["english"]["success"]
                    hindi_success = st.session_state.dual_audio["hindi"]["success"]

                    if english_success or hindi_success:
                        st.success("Bilingual audio summaries generated!")

                        # Display summary text
                        st.markdown('<h2 class="sub-header">Summary</h2>', unsafe_allow_html=True)
                        st.markdown(f"""
                        <div class="card">
                            <p style="color: #000000;">{st.session_state.summary_text}</p>
                        </div>
                        """, unsafe_allow_html=True)

                        # Display audio players
                        st.markdown('<h2 class="sub-header">Audio Summaries</h2>', unsafe_allow_html=True)

                        # Create two columns for side-by-side audio players
                        audio_col1, audio_col2 = st.columns(2)

                        # English Audio Player
                        with audio_col1:
                            st.markdown('<h3>🇺🇸 English Audio Summary</h3>', unsafe_allow_html=True)
                            if english_success:
                                try:
                                    english_filename = st.session_state.dual_audio["english"]["filename"]
                                    audio_url = f"{API_BASE_URL}/audio/{english_filename}"
                                    audio_response = requests.get(audio_url, timeout=30)
                                    audio_response.raise_for_status()
                                    st.audio(io.BytesIO(audio_response.content), format="audio/mp3")
                                except requests.RequestException as e:
                                    st.error(f"Failed to load English audio: {e}")
                            else:
                                st.error(f"English audio generation failed: {st.session_state.dual_audio['english']['error']}")

                        # Hindi Audio Player
                        with audio_col2:
                            st.markdown('<h3>🇮🇳 Hindi Audio Summary</h3>', unsafe_allow_html=True)
                            if hindi_success:
                                try:
                                    hindi_filename = st.session_state.dual_audio["hindi"]["filename"]
                                    audio_url = f"{API_BASE_URL}/audio/{hindi_filename}"
                                    audio_response = requests.get(audio_url, timeout=30)
                                    audio_response.raise_for_status()
                                    st.audio(io.BytesIO(audio_response.content), format="audio/mp3")
                                except requests.RequestException as e:
                                    st.error(f"Failed to load Hindi audio: {e}")
                            else:
                                st.error(f"Hindi audio generation failed: {st.session_state.dual_audio['hindi']['error']}")
                    else:
                        st.error("Failed to generate audio in both languages. Please try again.")

    # Footer
    st.markdown("---")
    st.markdown("© 2025 News Analyzer App")

if __name__ == "__main__":
    main()