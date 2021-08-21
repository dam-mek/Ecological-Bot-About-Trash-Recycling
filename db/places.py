from db import db


def get_places():
    places = db.current_session.query(db.Place)
    return places.all()
