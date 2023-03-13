# our User class, which will store and retrieve information from the database. 
# The name, email, and profile picture will all be retrieved from Google

from flask_login import UserMixin

from db import get_db

class User(UserMixin):
    def __init__(self, id_, name, email, profile_pic, timestamp=None):
        self.id = id_
        self.name = name
        self.email = email
        self.profile_pic = profile_pic
        self.timestamp = timestamp

    @staticmethod
    def get(user_id):
        db = get_db()
        user = db.execute(
            "SELECT * FROM user WHERE id = ?", (user_id,)
        ).fetchone()
        if not user:
            return None

        user = User(
            id_=user[0], name=user[1], email=user[2], profile_pic=user[3], timestamp=user[4]
        )
        return user

    @staticmethod
    def create(id_, name, email, profile_pic):
        db = get_db()
        db.execute(
            "INSERT INTO user (id, name, email, profile_pic) "
            "VALUES (?, ?, ?, ?)",
            (id_, name, email, profile_pic),
        )
        db.commit()

    @staticmethod
    def get_user_locations(user_id):
        db = get_db()
        locations = db.execute(
            "SELECT * FROM locations WHERE user_id=?", (user_id,)
        ).fetchall()
        
        if len(locations) == 0:
            return []
        return locations     