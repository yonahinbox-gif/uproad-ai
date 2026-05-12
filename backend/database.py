from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

ENGINE = create_engine("sqlite:///./uproad.sqlite", connect_args={"check_same_thread": False})
Session = sessionmaker(bind=ENGINE)
Base = declarative_base()
