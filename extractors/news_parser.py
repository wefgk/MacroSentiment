import requests
import logging
from bs4 import BeautifulSoup

logger=logging.getLogger(__name__)

def pars_news(RSS_urls:list)->list[dict[str,str]]:
    if not RSS_urls:
        logger.warning("The List of URLs is empty")
        return []

    news_list=[]

    for url in RSS_urls:
        try:
            response=requests.get(url,timeout=7)
            response.raise_for_status()
        except requests.RequestException as e:
            logger.exception("failed to fetch RSS from %s: %s",url,e)
            continue

        soup=BeautifulSoup(response.text,"xml")

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
    logger.info("collected articles %d",len(news_list))
    
    return news_list

