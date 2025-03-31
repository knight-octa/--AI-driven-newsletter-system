import feedparser
import spacy
import markdown
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from collections import defaultdict

# Load NLP model (using smaller model for faster testing)
nlp = spacy.load("en_core_web_md")

# Define RSS feed URLs by category
RSS_FEEDS = {
    "General News": [
        "https://feeds.bbci.co.uk/news/rss.xml",
        "https://feeds.npr.org/1001/rss.xml",
        "https://rss.cnn.com/rss/edition.rss"
    ],
    "Technology": [
        "http://feeds.feedburner.com/TechCrunch/",
        "https://www.wired.com/feed/rss",
        "https://www.technologyreview.com/feed/"
    ],
    "Finance": [
        "https://www.bloomberg.com/feed/podcast/etf-report.xml",
        "https://www.cnbc.com/id/10000664/device/rss/rss.html",
        "https://www.ft.com/rss/home/us"
    ],
    "Sports": [
        "http://www.espn.com/espn/rss/news",
        "http://feeds.bbci.co.uk/sport/rss.xml?edition=uk",
        "https://www.skysports.com/rss/12040"
    ],
    "Entertainment": [
        "https://variety.com/feed/",
        "https://www.hollywoodreporter.com/feed/",
        "https://www.billboard.com/feed/"
    ],
    "Science": [
        "https://www.nasa.gov/rss/dyn/breaking_news.rss",
        "https://www.sciencedaily.com/rss/all.xml",
        "https://feeds.arstechnica.com/arstechnica/science"
    ]
}

# User preferences
USER_PROFILES = {
    "Alex Parker": {"email": "alex.parker@example.com", "interests": ["AI", "cybersecurity", "blockchain", "startups", "programming"]},
    "Priya Sharma": {"email": "priya.sharma@example.com", "interests": ["Global markets", "startups", "fintech", "cryptocurrency", "economics"]},
    "Marco Rossi": {"email": "marco.rossi@example.com", "interests": ["Football", "F1", "NBA", "Olympic sports", "esports"]},
    "Lisa Thompson": {"email": "lisa.thompson@example.com", "interests": ["Movies", "celebrity news", "TV shows", "music", "books"]},
    "David Martinez": {"email": "david.martinez@example.com", "interests": ["Space exploration", "AI", "biotech", "physics", "renewable energy"]}
}

def fetch_news():
    """Fetch news articles from RSS feeds and store them in a structured format."""
    all_articles = []
    MAX_ARTICLES_PER_CATEGORY = 5  # This will result in max 30 articles (5 articles × 6 categories)
    for category, urls in RSS_FEEDS.items():
        article_count = 0
        for url in urls:
            if article_count >= MAX_ARTICLES_PER_CATEGORY:
                break
            feed = feedparser.parse(url)
            for entry in feed.entries:
                if article_count >= MAX_ARTICLES_PER_CATEGORY:
                    break
                article = {
                    "title": entry.title,
                    "link": entry.link,
                    "source": feed.feed.title if 'title' in feed.feed else "Unknown",
                    "category": category,
                    "summary": entry.summary if 'summary' in entry else "No summary available"
                }
                all_articles.append(article)
                article_count += 1
    return all_articles

def categorize_articles(articles):
    """Use NLP to categorize articles based on their summaries."""
    import warnings
    warnings.filterwarnings("ignore", message="^\\[W007\\]")

    categorized_articles = defaultdict(list)
    total = len(articles)
    print("Starting categorization...")
    for i, article in enumerate(articles, 1):
        if i % 5 == 0:  # Show progress more frequently since we have fewer articles
            print(f"Categorizing... {i}/{total} articles ({(i/total)*100:.1f}%)")
        doc = nlp(article["summary"])
        category_scores = {category: sum(token.similarity(nlp(category)) for token in doc if token.has_vector) for category in RSS_FEEDS.keys()}
        best_category = max(category_scores, key=category_scores.get)
        article["nlp_category"] = best_category
        categorized_articles[best_category].append(article)
    return categorized_articles

def personalize_news(user_name, categorized_articles):
    """Filter and recommend articles based on user interests."""
    user_interests = USER_PROFILES.get(user_name, {}).get("interests", [])
    personalized_articles = []
    for category, articles in categorized_articles.items():
        for article in articles:
            doc = nlp(article["title"] + " " + article["summary"])
            interest_scores = {interest: sum(token.similarity(nlp(interest)) for token in doc if token.has_vector) for interest in user_interests}
            if interest_scores and max(interest_scores.values()) > 0.5:
                article["matched_interest"] = max(interest_scores, key=interest_scores.get)
                personalized_articles.append(article)
    return personalized_articles

def generate_newsletter(user_name, personalized_articles):
    """Generate a personalized newsletter in Markdown format."""
    newsletter_content = f"# Personalized Newsletter for {user_name}\n\n"
    newsletter_content += "## Trending Articles\n"
    for article in personalized_articles[:5]:
        newsletter_content += f"- [{article['title']}]({article['link']}) ({article['matched_interest']})\n"
    newsletter_content += "\n## Detailed Articles by Category\n"
    categorized_news = defaultdict(list)
    for article in personalized_articles:
        categorized_news[article["nlp_category"]].append(article)
    for category, articles in categorized_news.items():
        newsletter_content += f"### {category}\n"
        for article in articles:
            newsletter_content += f"[{article['title']}]({article['link']})\n\n{article['summary']}\n\n"
    return newsletter_content

def send_newsletter(user_name, newsletter_content):
    """Send the newsletter via email."""
    user_email = USER_PROFILES[user_name]["email"]
    sender_email = "your_email@example.com"
    sender_password = "your_password"
    msg = MIMEMultipart()
    msg["From"] = sender_email
    msg["To"] = user_email
    msg["Subject"] = f"Your Personalized Newsletter, {user_name}"
    msg.attach(MIMEText(newsletter_content, "plain"))
    try:
        server = smtplib.SMTP("smtp.example.com", 587)
        server.starttls()
        server.login(sender_email, sender_password)
        server.sendmail(sender_email, user_email, msg.as_string())
        server.quit()
        print(f"Newsletter sent to {user_name} at {user_email}")
    except Exception as e:
        print(f"Failed to send email: {e}")

if __name__ == "main":
    print("Fetching news...")
    articles = fetch_news()
    print(f"Found {len(articles)} articles")

    print("Categorizing articles...")
    categorized_articles = categorize_articles(articles)
    print(f"Categorized into {len(categorized_articles)} categories")

    user_name = "Alex Parker"
    print(f"Personalizing for {user_name}...")
    personalized_articles = personalize_news(user_name, categorized_articles)
    print(f"Selected {len(personalized_articles)} personalized articles")

    newsletter_content = generate_newsletter(user_name, personalized_articles)
    print("\nNewsletter Content:")
    print(newsletter_content)