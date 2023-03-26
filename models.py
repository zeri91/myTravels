from sqlalchemy import Column, ForeignKey, Table, CheckConstraint, func
from sqlalchemy.orm import relationship, backref
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.types import Integer, Float, String, Date, DateTime, Text, Enum
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin

db = SQLAlchemy()

class User(UserMixin, db.Model):
    __tablename__ = "user"
    id = Column(String, primary_key=True)
    name = Column(Text(50), nullable=False)
    email = Column(String(50), nullable=False, unique=True)
    profile_pic = Column(String)
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    trips = relationship("Trip", backref=backref("user"))

    def __repr__(self):
        return f'<User {self.name}>'

class Trip(UserMixin, db.Model):
    __tablename__ = "trip"
    trip_id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String, ForeignKey("user.id"), nullable=False)
    country = Column(Text(30), nullable=False)
    city = Column(String(30))
    arr_date = Column(Date)
    dep_date = Column(Date)
    category = Column(Enum('leisure', 'work'), default='leisure', nullable=False)
    people = Column(String, nullable=False)
    accomodation = Column(String(200))
    cost = Column(Float)
    notes = Column(String)

    def __repr__(self):
        return f'<Trip {self.trip_id}>'