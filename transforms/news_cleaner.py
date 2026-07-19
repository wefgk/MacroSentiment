import spacy
import sqlite3
import logging

logger=logging.getLogger(__name__)

class NewsTransformer:
    def __init__(self,db_path:str="relationships.db")->None:
        self.db_path=db_path
        self.nlp=spacy.load("en_core_web_md")
        logger.info("SpaCy model loaded successfully")
        self.mapping_cache=self._load_relationships_in_memory()
        self.countries_whitelist=self._load_whitelist_in_memory()
        self.alliences_whitelist=self._load_alliances_whitelist()
        logger.info("All data for the cleaner loaded into memory")

    def _load_relationships_in_memory(self)->dict[str,str]:
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor=conn.cursor()
                cursor.execute("SELECT key, country FROM entity_mapping")
                return dict(cursor.fetchall())
        except sqlite3.Error as e:
            logger.error(e)
            return {}
    
    def _load_whitelist_in_memory(self)->dict[str,str]:
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor=conn.cursor()
                cursor.execute("SELECT country_name FROM countries_whitelist")
                return {row[0] for row in cursor.fetchall()}
        except sqlite3.Error as e:
            logger.error(e)
            return set()
            
    def _load_alliances_whitelist(self) -> set[str]:
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT alliance_name FROM alliances_whitelist")
                return {row[0] for row in cursor.fetchall()}
        except sqlite3.Error as e:
            logger.error(e)
            return set()
        
    def _find_country(self, object:str):
        return self.mapping_cache.get(object.lower().strip())
    
    

    def extract_geo_data(self,text:str)->list[str]:
        doc=self.nlp(text)
        countries=set()
        alliances=set()

        for ent in doc.ents:
            if ent.label_ in ("GPE", "PERSON", "ORG"):
                matched_country=self._find_country(ent.text)
                if matched_country in self.countries_whitelist:
                    countries.add(matched_country)
                elif matched_country in self.alliences_whitelist:
                    countries.add(ent.text)
            else:
                potential_name = ent.text.strip()
                    
                    
                if potential_name in self.countries_whitelist:
                    countries.add(potential_name)
                elif potential_name in self.alliences_whitelist:
                    alliances.add(potential_name)
        return {"countries":list(countries),
                "alliances":list(alliances)}