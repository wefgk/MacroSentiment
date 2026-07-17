import spacy
import sqlite3
import logging

logger=logging.getLogger(__name__)

class NewsTransformer:
    def __init__(self,db_path:str="relationships.db")->None:
        self.db_path=db_path
        self.nlp=spacy.load("en_core_web_sm")
        logger.info("SpaCy model loaded successfully")
        self.mapping_cache=self._load_relationships_in_memory()

    def _load_relationships_in_memory(self)->dict[str,str]:
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor=conn.cursor()
                cursor.execute("SELECT key, country FROM entity_mapping")
                logger.info("The relationships database loaded in memory")
                return dict(cursor.fetchall())
        except sqlite3.Error as e:
            logger.error(e)
            return {}
        
    def _find_country(self, object:str):
        return self.mapping_cache.get(object.lower().strip())
    
    

    def extract_countries(self,text:str)->list[str]:
        doc=self.nlp(text)
        countries=set()

        for ent in doc.ents:
            if ent.label_ in ("GPE", "PERSON", "ORG"):
                matched_country=self._find_country(ent.text)
                if matched_country:
                    countries.add(matched_country)
                elif ent.label_=="GPE":
                    countries.add(ent.text)
        return list(countries)