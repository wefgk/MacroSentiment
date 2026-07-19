from database.db_manager import DataBaseManager
from extractors.news_parser import pars_news
from transforms.news_cleaner import NewsTransformer
from transforms.AI_analyzer import AIAnalyzer
import logging
from pprint import pprint
import time

logging.basicConfig(
    level=logging.INFO, 
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s", 
    datefmt="%Y-%m-%d %H:%M:%S"
)

logger=logging.getLogger(__name__)


urls=["https://feeds.bbci.co.uk/news/world/rss.xml"]



def main(urls: list):
    raw_data = pars_news(urls)
    db = DataBaseManager()
    db.insert_raw_news(raw_data)

    unanalyzed_news = db.get_all_new_news()

    if not unanalyzed_news:
        logger.info("There is no new data for analysis.")
        return
    
    transformer = NewsTransformer()
    ai = AIAnalyzer(url = "http://localhost:1234/v1", api_key = "lm-studio")

    logger.info(f"Found {len(unanalyzed_news)} raw news. Starting pipeline")

    processed_logs = []

    for item in unanalyzed_news[:5]:
        news_id = item.get("id")
        title = item.get("title")
        description = item.get("description")
        
        full_text = f"{title}. {description}"

        geo_data = transformer.extract_geo_data(full_text)
        
        all_entities = geo_data["countries"] + geo_data["alliances"]

        if not all_entities:
            continue


        logger.info(f"Analyzing sentiment for news ID {news_id} targets: {all_entities}")
        sentiment_ratings = ai.analyze_sentiment(full_text, all_entities,)
        

        if sentiment_ratings:
            
            processed_logs.append({
                "news_id": news_id,
                "title": title,
                "geo_data": geo_data,
                "ai_ratings": sentiment_ratings
            })
        time.sleep(0.1)
            
    
    print("\n=== PIPELINE SUCCESSFUL RESULTS ===")
    pprint(processed_logs, sort_dicts=False)
        

if __name__=="__main__":
    main(urls)