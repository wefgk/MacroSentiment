from database.db_manager import DataBaseManager
from extractors.news_parser import pars_news
from transforms.news_cleaner import NewsTransformer
import logging
from pprint import pprint

logging.basicConfig(
    level=logging.INFO, 
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s", 
    datefmt="%Y-%m-%d %H:%M:%S"
)

logger=logging.getLogger(__name__)


urls=["https://feeds.bbci.co.uk/news/world/rss.xml"]



def main(urls:list):
    data=pars_news(urls)
    manager=DataBaseManager()
    manager.insert_raw_news(data)


    data=manager.get_all_new_news()

    if not data:
        logger.info("There is no new data")
        return
    
    transformer=NewsTransformer()

    news_and_country=[]
    for item in data:

        full_text=f"{item.get("title")}. {item.get("description")}"

        geo_data=transformer.extract_geo_data(full_text)
        if not geo_data:
            continue
        
        if not geo_data["countries"] and not geo_data["alliances"]:
            continue

        d={"news":full_text,"geo_data":geo_data}
        news_and_country.append(d)
    
    pprint(news_and_country,sort_dicts=False)
        

if __name__=="__main__":
    main(urls)