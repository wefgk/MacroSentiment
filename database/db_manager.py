import sqlite3
import logging
from datetime import datetime
from email.utils import parsedate_to_datetime

logger=logging.getLogger(__name__)

class DataBaseManager:
    def __init__(self,db_path:str="news.db")->None:
        self.db_path=db_path
        self._create_tables()

    def _get_conn(self):
        return sqlite3.connect(self.db_path)
    

    def _create_tables(self):
        try:
            with self._get_conn() as conn:
                cursor=conn.cursor()

                cursor.execute("""CREATE TABLE IF NOT EXISTS raw_news(
                               id INTEGER PRIMARY KEY AUTOINCREMENT,
                                title TEXT NOT NULL,
                                link TEXT UNIQUE NOT NULL,
                                description TEXT NOT NULL,
                                pub_date TEXT,
                                is_analyzed INTEGER DEFAULT 0,
                                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)""")
                
                cursor.execute("""CREATE TABLE IF NOT EXISTS country_ratings (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            news_id INTEGER,
                            country TEXT NOT NULL,
                            sentiment_score REAL NOT NULL,
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            FOREIGN KEY (news_id) REFERENCES raw_news (id) ON DELETE CASCADE)""")
                
                conn.commit()
                logger.info("DB tables verifed/created successfully")
        except sqlite3.Error as e:
            logger.critical("Failed to initialize database tables: %s", e)
            raise
            

    def _clean_date(self, raw_date_str: str) -> str:

        if not raw_date_str:
            return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                
        try:
            dt = parsedate_to_datetime(raw_date_str)
            return dt.strftime("%Y-%m-%d %H:%M:%S")
        
        except Exception as e:
            logger.warning("Failed to parse date string '%s': %s", raw_date_str, e)
            return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def insert_raw_news(self, news_list: list[dict[str,str]]):
        if not news_list:
            logger.warning("The news list is empty")
            return
        
        cleaned_news=[]
        for item in news_list:
            cleaned_item=item.copy()
            cleaned_item["date"]=self._clean_date(item.get("date",""))
            cleaned_news.append(cleaned_item)
        
        try:
            with self._get_conn() as conn:
                cursor=conn.cursor()
                cursor.executemany("""INSERT OR IGNORE INTO raw_news (title, link, description, pub_date)
                                        VALUES (:title, :link, :description, :date);""",cleaned_news)
                
                logger.info("Successfully inserted")
        except sqlite3.Error as e:
            logger.error(e)
            return
        
    def get_all_new_news(self)->list[dict]:
        try:
            with self._get_conn() as conn:
                conn.row_factory=sqlite3.Row
                cursor=conn.cursor()
                cursor.execute("SELECT id, title,description,link FROM raw_news WHERE is_analyzed = 0")

                return [dict(row) for row in cursor.fetchall()]
        except sqlite3.Error as e:
            logger.error(e)
            return []

                    