from db import db


def get_categories():
    # with db.session_scope() as session:
    categories = db.current_session.query(db.Category)
    return categories.all()


def add_taken_trash(telegram_id, category, weight):
    with db.session_scope() as session:
        category = session.query(db.Category).filter(db.Category.name == category).first()
        session.add(
            db.Taken_Trash(client_telegram_id=telegram_id,
                           category_id=category.id,
                           weight=weight)
        )


def add_eballs(telegram_id, category, weight):
    with db.session_scope() as session:
        category = session.query(db.Category).filter(db.Category.name == category).first()
        eballs = session.query(db.Eballs).filter(db.Eballs.client_telegram_id == telegram_id).first()
        difference = round(category.price_koef * weight)
        eballs.amount += difference
        return eballs.amount, difference


def minus_eballs(telegram_id, product_name):
    with db.session_scope() as session:
        eballs = session.query(db.Eballs).filter(db.Eballs.client_telegram_id == telegram_id).first()
        product = session.query(db.Product).filter(db.Product.name == product_name).first()
        eballs.amount -= product.price

