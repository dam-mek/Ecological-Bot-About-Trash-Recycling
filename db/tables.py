from sqlalchemy import Column, ForeignKey, Integer, String, Float, Text, Date, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


class Client(Base):
    __tablename__ = 'clients'

    telegram_id = Column(Integer, primary_key=True)
    is_master = Column(Boolean, nullable=False, default=False)

    taken_trashes = relationship('Taken_Trash')
    bought_products = relationship('Bought_Product')
    eballs = relationship('Eballs', back_populates='client')

    def __repr__(self):
        return f'Client(telegram_id={self.telegram_id} is_master={self.is_master})'


class Eballs(Base):
    __tablename__ = 'eballs'

    amount = Column(Integer, default=0)
    client_telegram_id = Column(Integer, ForeignKey(Client.telegram_id), primary_key=True)
    client = relationship('Client', back_populates='eballs')


class Category(Base):
    __tablename__ = 'categories'

    id = Column(Integer, primary_key=True)
    name = Column(String(128), nullable=False, unique=True)
    icon = Column(String(32), nullable=True)
    price_koef = Column(Float, nullable=False)
    taken_trashes = relationship('Taken_Trash')

    def __repr__(self):
        return f'Category(name={self.name})'


class Product(Base):
    __tablename__ = 'products'

    id = Column(Integer, primary_key=True)
    name = Column(String(128), nullable=False, unique=True)
    price = Column(Integer, nullable=False)
    bought_products = relationship('Bought_Product')


class Taken_Trash(Base):
    __tablename__ = 'taken trashes'

    id = Column(Integer, primary_key=True)
    weight = Column(Integer, nullable=False)
    date = Column(Date, nullable=True)

    category_id = Column(Integer, ForeignKey(Category.id))
    client_telegram_id = Column(Integer, ForeignKey(Client.telegram_id))

    def __repr__(self):
        return f'Taken_Trash(weight={self.weight} category_id={self.category_id} client_telegram_id={self.client_telegram_id})'


class Bought_Product(Base):
    __tablename__ = 'bought products'

    id = Column(Integer, primary_key=True)
    client_telegram_id = Column(Integer, ForeignKey(Client.telegram_id))
    product_id = Column(Integer, ForeignKey(Product.id))
    is_taken = Column(Boolean, nullable=False, default=False)

    def __repr__(self):
        return f'Bought Product(asking_label={self.asking_label} ' \
               f'asking_place={self.asking_place} asking_description={self.asking_description})'


class Place(Base):
    __tablename__ = 'places'

    id = Column(Integer, primary_key=True)
    address = Column(Text)
