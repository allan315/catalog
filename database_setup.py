from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy import create_engine


Base = declarative_base()


class User(Base):
    __tablename__ = 'user'

    id = Column(Integer, primary_key=True)
    user_name = Column(String(250))
    user_email = Column(String(250))

    #  Add a property decorator to serialize information from this database

    @property
    def serialize(self):
        return {
            'user_name': self.user_name,
            'user_email': self.user_email,
            'id': self.id
            }
    

class Categories(Base):
    __tablename__ = 'categories'

    id = Column(Integer, primary_key=True)
    cat_name = Column(String(250))
    user_id = Column(Integer, ForeignKey('user.id'))
    user = relationship(User)

    #  Add a property decorator to serialize information from this database

    @property
    def serialize(self):
        return {
            'cat_name': self.cat_name,
            'id': self.id
            }
    

class Items(Base):
    __tablename__ = 'items'
    id = Column(Integer, primary_key=True)
    item_name = Column(String)
    item_link = Column(String)
    item_description = Column(String)
    item_image = Column(String)
    item_category_id = Column(Integer, ForeignKey('categories.id'))
    cat = relationship(Categories)
    user_id = Column(Integer, ForeignKey('user.id'))
    user = relationship(User)

    #  Add a property decorator to serialize information from this database

    @property
    def serialize(self):
        return {
            'item_name': self.item_name,
            'item_link': self.item_link,
            'item_image': self.item_image,
            'item_description': self.item_description,
            'item_category': self.item_category_id,
            'id': self.id
            }

engine = create_engine('sqlite:///items.db')
Base.metadata.create_all(engine)

