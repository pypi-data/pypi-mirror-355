from .session import Base, engine
import logging

def init_db():
    logging.info("Creating tables:", Base.metadata.tables.keys())  
    Base.metadata.create_all(bind=engine) 