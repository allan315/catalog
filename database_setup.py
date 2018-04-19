from sqlalchemy import Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy import create_engine


Base = declarative_base()


class Items(Base):
    __tablename__ = 'items'
    id = Column(Integer, primary_key=True)
    item_name = Column(String)
    item_link = Column(String)
    item_description = Column(String)
    item_image = Column(String)

    #  Add a property decorator to serialize information from this database

    @property
    def serialize(self):
        return {
            'item_name': self.item_name,
            'item_link': self.item_link,
            'item_image': self.item_image,
            'item_description': self.item_description,
            'id': self.id
            }

engine = create_engine('sqlite:///items.db')
Base.metadata.create_all(engine)

