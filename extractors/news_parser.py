import httpx
import logging
from bs4 import BeautifulSoup
import asyncio

logger=logging.getLogger(__name__)

async def _pars_news(client:httpx.AsyncClient, url:str)->list[dict[str,str]]:

    news_list=[]
    try:
        response=await client.get(url,timeout=7)
        response.raise_for_status()
    except httpx.HTTPStatusError as e:
        logger.error(f"HTTP error occurred while fetching RSS from {url}: {e}")
        return []
    except httpx.RequestError as e:
        logger.error(f"An error occurred while requesting {url}: {e}")
        return []


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

