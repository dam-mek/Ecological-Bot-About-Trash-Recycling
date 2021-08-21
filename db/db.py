import os
from datetime import date
from contextlib import contextmanager

from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine, MetaData
from db.tables import Base
from db.tables import Client, Eballs, Category, Product, Taken_Trash, Bought_Product, Place

# PSQL_PASSWORD = os.environ['PASSWORDPSQL']
# DATABASE_NAME = 'goodbottest'
# engine = create_engine(f'postgresql+psycopg2://postgres:{PSQL_PASSWORD}@localhost/{DATABASE_NAME}', echo=False)
DATABASE_URL = os.environ['DATABASE_URL']
# engine = create_engine(f'postgresql+psycopg2://{DATABASE_URL}', echo=False)
engine = create_engine(DATABASE_URL.replace('postgres', 'postgresql+psycopg2'), echo=False)
Session = sessionmaker(bind=engine)
current_session = Session()


@contextmanager
def session_scope():
    """Provide a transactional scope around a series of operations."""
    session = Session()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def recreate_db():
    meta = MetaData()
    meta.reflect(bind=engine)
    meta.drop_all(bind=engine)

    Base.metadata.create_all(engine)


def _init_db_():
    # print('1')
    recreate_db()
    # print('2')

    # 285942176 Тёмыч
    # 761271004 Егорыч
    # 469379644 Никитос
    # 1911412025 pavel
    tyoma = Client(telegram_id=285942176, is_master=True)
    egor = Client(telegram_id=761271004)
    nikitos = Client(telegram_id=469379644)

    with session_scope() as session:
        session.add(tyoma)
        session.add(egor)
        session.add(nikitos)
        session.add(Eballs(client_telegram_id=285942176))
        session.add(Eballs(client_telegram_id=761271004))
        session.add(Eballs(client_telegram_id=469379644, amount=100))

        session.add_all([
            Category(name='Металл', icon='🔗', price_koef=0.05),
            Category(name='Стекло', icon='🔍', price_koef=0.02),
            Category(name='Пластик', icon='🛍', price_koef=0.03),
            Category(name='Макулатура', icon='📄', price_koef=0.01),
            Category(name='Неперерабатываемые', icon='💀', price_koef=0.008)
        ])

        session.add_all([
            Place(address='Строителей, 42'),
            Place(address='Ноградская, 34'),
        ])

        session.add_all([
            Product(name='Квас деревенский', price=15),
            Product(name='Шашлык свинной', price=75),
            Product(name='Печенье «Домашнее»', price=20)
        ])


# _init_db_()


# async def get_client_settings(telegram_user_id: id) -> ClientSettings:
#     client_settings = current_session.query(ClientSettings).filter(ClientSettings.telegram_id == telegram_user_id)
#     return client_settings.first()
    # with session_scope() as session:
    #     client_settings = session.query(ClientSettings).filter(ClientSettings.telegram_id == telegram_user_id).first()
    #     return client_settings

# meta = MetaData()
#
# print('start connection')
# meta.reflect(bind=engine)
# print('connection success')
#
# # meta.drop_all(bind=engine)
#
# for table in reversed(meta.sorted_tables):
#     print(table)
#     # engine.execute(table.drop(engine))
