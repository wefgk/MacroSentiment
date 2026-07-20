import httpx
from httpx import RequestError,HTTPStatusError
import logging
from bs4 import BeautifulSoup
import asyncio
from tenacity import retry,stop_after_attempt,wait_exponential,retry_if_exception_type,before_sleep_log

logger=logging.getLogger(__name__)

@retry(stop=stop_after_attempt(3),
       wait=wait_exponential(multiplier=1,min=1,max=10),
       retry=retry_if_exception_type((RequestError,HTTPStatusError)),
       before_sleep=before_sleep_log(logger,logging.WARNING),
       retry_error_callback=lambda retry_state: [])
async def _pars_news(client:httpx.AsyncClient, url:str)->list[dict[str,str]]:

    news_list=[]
    response=await client.get(url,timeout=7)

    soup= await asyncio.to_thread(BeautifulSoup,response.text,"xml")

    items=soup.find_all("item")
        
    for item in items:
        title=item.find("title")
        link=item.find("link")
        date=item.find("pubDate")
        description=item.find("description")

        news_dict={
            "title":title.text.strip() if title else "No title",
            "link":link.text.strip() if link else "No link",
            "date":date.text.strip() if date else "No date",
            "description":description.text.strip() if description else "No discription",
        }
        
        news_list.append(news_dict)
    
    return news_list

async def pars_news(RSS_urls:list)->list[dict[str:str]]:
    if not RSS_urls:
        logger.warning("The list of URLs is empty")
        return []
    
    async with httpx.AsyncClient() as client:
        tasks=[_pars_news(client,url) for url in RSS_urls]

        results=await asyncio.gather(*tasks)
    
    news_list=[news for sublist in results for news in sublist]

    logger.info("collected articles : %d" ,len(news_list))

    return news_list

