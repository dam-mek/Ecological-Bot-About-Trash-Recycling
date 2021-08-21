from db import db


def add_new_client(telegram_id):
    with db.session_scope() as session:
        user = session.query(db.Client).filter(db.Client.telegram_id == telegram_id).first()
        if user is None:
            session.add(db.Client(telegram_id=telegram_id))
        eballs = session.query(db.Eballs).filter(db.Eballs.client_telegram_id == telegram_id).first()
        if eballs is None:
            session.add(db.Eballs(client_telegram_id=telegram_id, amount=0))


def get_clients():
    # with db.session_scope() as session:
    clients = db.current_session.query(db.Client)
    return clients.all()


def get_eballs(telegram_id):
    eballs = db.current_session.query(db.Eballs).filter(db.Eballs.client_telegram_id == telegram_id).first()
    return eballs.amount


def get_all_taken_trashes(telegram_id):
    taken_trashes = db.current_session.query(db.Taken_Trash).filter(db.Taken_Trash.client_telegram_id == telegram_id)
    d = []
    for trash in taken_trashes.all():
        d.append((db.current_session.query(db.Category).filter(db.Category.id == trash.category_id).first(), trash.weight))
    return d

