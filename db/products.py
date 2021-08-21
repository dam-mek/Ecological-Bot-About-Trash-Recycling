from db import db


def get_products():
    products = db.current_session.query(db.Product)
    return products.all()


def add_product(name, price):
    with db.session_scope() as session:
        session.add(
            db.Product(name=name,
                       price=price)
        )


def add_bought_product(telegram_id, product, place):
    with db.session_scope() as session:
        product = session.query(db.Product).filter(db.Product.name == product).first()
        session.add(
            db.Bought_Product(client_telegram_id=telegram_id,
                              product_id=product.id)
        )
