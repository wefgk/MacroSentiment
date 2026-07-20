import logging
from datetime import datetime
from email.utils import parsedate_to_datetime
from typing import Dict, Any

from sqlalchemy import String, Text, Boolean, DateTime, Float, ForeignKey, select, update
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.dialects.postgresql import insert

logger=logging.getLogger(__name__)

class Base(DeclarativeBase):
    pass

class RawNews(Base):
    __tablename__="raw_news"

    id: Mapped[int] = mapped_column(primary_key=True,autoincrement=True)
    title: Mapped[str] = mapped_column(Text,nullable=False)
    description: Mapped[str] = mapped_column(Text,nullable=False)
    link: Mapped[str] = mapped_column(Text,unique=True,nullable=False)
    pub_date: Mapped[datetime] = mapped_column(DateTime,nullable=False)

    is_analyzed: Mapped[bool] = mapped_column(Boolean,default=False, server_default="false")
    has_geo: Mapped[bool] = mapped_column(Boolean,default=True, server_default="true")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, server_default="now()")

class CountryRating(Base):
    __tablename__ = "country_ratings"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    news_id: Mapped[int] = mapped_column(ForeignKey("raw_news.id", ondelete="CASCADE"), nullable=False)
    country: Mapped[str] = mapped_column(String(100), nullable=False)
    sentiment_score: Mapped[float] = mapped_column(Float, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, server_default="now()")

class DataBaseManager:
    def __init__(self,db_url:str)->None:
        self.engine=create_async_engine(db_url,echo=False, pool_pre_ping=True)
        self.session_factory=async_sessionmaker(bind=self.engine,
                                                class_=AsyncSession,
                                                expire_on_commit=False)
    
    async def init_db(self)->None:
        try:
            async with self.engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
                logger.info("PostgreSQL tables verified/created successfully")
        except Exception as e:
            logger.critical(f"Failed to initialize PostgreSQL tables: {e}")
            raise
    
    def _clean_date(self,raw_date:str)->datetime:
        if not raw_date:
            return datetime.utcnow()
        try:    
            dt = parsedate_to_datetime(raw_date)
            return dt.replace(tzinfo=None)
        except Exception as e:
            logger.warning(f"Failed to parse date string '{raw_date}': {e}")
            return datetime.utcnow()

    async def insert_raw_news(self,news_list:list[dict[str,Any]])->None:
        if not news_list:
            logger.warning("The news list is empty")
            return
        
        async with self.session_factory() as session:
            try:
                for item in news_list:
                    insert_data = {"title": item.get("title"),
                        "link": item.get("link"),
                        "description": item.get("description"),
                        "pub_date": self._clean_date(item.get("date", ""))}
                    
                    instr=insert(RawNews).values(**insert_data).on_conflict_do_nothing(index_elements=["link"])
                    await session.execute(instr)
                await session.commit()
                logger.info(f"Successfully processed and inserted {len(news_list)} raw news items")
            except Exception as e:
                await session.rollback()
                logger.error(f"Error inserting raw news: {e}")


    async def get_all_new_news(self)->list[dict[str,Any]]:
        async with self.session_factory() as session:
            try:
                command=select(RawNews).where(RawNews.is_analyzed==False,RawNews.has_geo==True)
                result= await session.execute(command)
                news_rows=result.scalars().all()

                return [{
                        "id": row.id,
                        "title": row.title,
                        "description": row.description,
                        "link": row.link
                        }for row in news_rows]
            except Exception as e:
                logger.error(f"Error fetching unanalyzed news: {e}")
                return []
            

    async def mark_news_if_no_geo(self,news_id:int)->None:
        async with self.session_factory() as session:
            try:
                command = update(RawNews).where(RawNews.id == news_id).values(has_geo=False)
                await session.execute(command)
                await session.commit()
                logger.info(f"News ID {news_id} marked as has_geo=False")
            except Exception as e:
                await session.rollback()
                logger.error(f"Failed to update geo status for news ID {news_id}: {e}")


    async def save_analysis_results(self, news_id: int, ratings: Dict[str, float]) -> None:
        async with self.session_factory() as session:
            try:
                for country, score in ratings.items():
                    rating_record = CountryRating(
                        news_id=news_id,
                        country=country,
                        sentiment_score=score
                    )
                    session.add(rating_record)
                
                command = update(RawNews).where(RawNews.id == news_id).values(is_analyzed=True)
                await session.execute(command)
                
                await session.commit()
                logger.info(f"Analysis results saved and status updated for News ID {news_id}")
            except Exception as e:
                await session.rollback()
                logger.error(f"Failed to save analysis results for news ID {news_id}: {e}")



