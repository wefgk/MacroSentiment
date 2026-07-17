from database.db_manager import DataBaseManager
from extractors.news_parser import pars_news
from transforms.news_cleaner import NewsTransformer
import logging

logging.basicConfig(
    level=logging.INFO, 
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s", 
    datefmt="%Y-%m-%d %H:%M:%S"
)

logger=logging.getLogger(__name__)


urls=["https://feeds.bbci.co.uk/news/world/rss.xml"]



def main(urls:list):
    #data=pars_news(urls)
    manager=DataBaseManager()
    #manager.insert_raw_news(data)


    data=manager.get_all_new_news()

    if not data:
        logger.info("There is no new data")
        return
    
    transformer=NewsTransformer()

    for item in data:

        full_text=f"{item.get("title")}. {item.get("description")}"
        
        print(full_text)
        print(transformer.extract_countries(full_text))

if __name__=="__main__":
    main(urls)