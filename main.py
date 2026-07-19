from database.db_manager import DataBaseManager
from extractors.news_parser import pars_news
from transforms.news_cleaner import NewsTransformer
from transforms.AI_analyzer import AIAnalyzer
import logging
from pprint import pprint
import time
import asyncio

logging.basicConfig(
    level=logging.INFO, 
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s", 
    datefmt="%Y-%m-%d %H:%M:%S"
)

logger=logging.getLogger(__name__)


urls=["https://feeds.bbci.co.uk/news/world/rss.xml"]



async def main(urls: list, AI_url:str,api_hey:str):
    pipeline_start=time.perf_counter()

    #raw_data = await pars_news(urls)
    db = DataBaseManager()
    #db.insert_raw_news(raw_data)

    unanalyzed_news = db.get_all_new_news()

    if not unanalyzed_news:
        logger.info("There is no new data for analysis")
        return
    
    scrap_and_ins_time=time.perf_counter()-pipeline_start
    logger.info(f"Found {len(unanalyzed_news)} raw news in DB")

    transformer = NewsTransformer()
    ai = AIAnalyzer(url = AI_url, api_key = api_hey)

    processed_logs = []
    skiped_news=0
    batch_size=3

    AI_execution_start_time=time.perf_counter()

    #unanalyzed_news=unanalyzed_news[:15]
    for i in range(0,len(unanalyzed_news),batch_size):
        batch=unanalyzed_news[i:i+batch_size]

        tasks=[]
        batch_meta=[]

        for item in batch:

            news_id = item.get("id")
            title = item.get("title")
            description = item.get("description")
            full_text = f"{title}. {description}"

            geo_data = transformer.extract_geo_data(full_text)
            all_entities = geo_data["countries"] + geo_data["alliances"]

            if not all_entities:
                logger.info("=" * 50)
                logger.info(f"News item with ID {news_id} doest contain geo")
                
                skiped_news+=1
                continue


            task = ai.analyze_sentiment(full_text, all_entities)
            tasks.append(task)
        

            batch_meta.append({
                "news_id": news_id,
                "title": title,
                "geo_data": geo_data
            })

        if not tasks:
            continue

        batch_results= await asyncio.gather(*tasks)

        for meta, sentiment_ratings in zip(batch_meta,batch_results):
            if not sentiment_ratings:
                logger.warning(f"[SKIPPED] News ID - {meta['news_id']} failed due to API error")
                continue

            processed_logs.append({
                "news_id": meta["news_id"],
                "title": meta["title"],
                "geo_data": meta["geo_data"],
                "ai_ratings": sentiment_ratings
            })
            logger.info(f"[SUCCESS] News ID - {meta["news_id"]}. Scores - {sentiment_ratings} \n") 


    AI_execution_time=time.perf_counter()-AI_execution_start_time
    pipeline_time=time.perf_counter()-pipeline_start

    #print("\n=== PIPELINE SUCCESSFUL RESULTS ===")
    #pprint(processed_logs, sort_dicts=False)

    logger.info("=" * 50)
    logger.info("PERFORMANCE & METRICS REPORT")
    logger.info("=" * 50)
    logger.info(f"Total pipeline execution time : {pipeline_time:.2f} seconds")
    logger.info(f"Total AI execution time       : {AI_execution_time:.2f} seconds")
    logger.info(f"Average time per news item    : {pipeline_time/max(len(processed_logs),1):.2f} seconds")
    logger.info(f"collecting and inserting time : {scrap_and_ins_time:.2} seconds")
    logger.info(f"Successfully processed items  : {len(processed_logs)}")
    logger.info(f"Skipped (no geo entities)     : {skiped_news}")

        

if __name__=="__main__":
    asyncio.run(main(urls,"http://localhost:1234/v1","lm-studio"))