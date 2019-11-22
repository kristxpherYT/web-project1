from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from application import db
from flask import json
from flask_sqlalchemy import SQLAlchemy
from serializer import BaseModel

class User(BaseModel, UserMixin):

    __tablename__ = 'users'
    __table_args__ = {'extend_existing': True}

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    email = db.Column(db.String(256), unique=True, nullable=False)
    password = db.Column(db.String(128), nullable=False)
    reviews = db.relationship('Review', lazy='select', backref=db.backref('user', lazy='joined'))

    def set_password(self, password):
        self.password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password, password)

    def __repr__(self):
        return f"<User {self.email}>"

    def save(self):
        if not self.id:
            db.session.add(self)
        db.session.commit()

    @staticmethod
    def get_by_id(id):
        return User.query.get(id)

    @staticmethod
    def get_by_email(email):
        return User.query.filter_by(email=email).first()

class Book(BaseModel):

    __tablename__ = 'books'
    __table_args__ = {'extend_existing': True}

    id = db.Column(db.Integer, primary_key=True)
    isbn = db.Column(db.String(10), unique=True, nullable=False)
    title = db.Column(db.String(120), nullable=False)
    author = db.Column(db.String(80), nullable=False)
    publication_year = db.Column(db.String(10), nullable=True)
    reviews = db.relationship('Review', lazy='select', backref=db.backref('books', lazy='joined'))

    _default_fields = [
        "isbn",
        "title",
        "author",
        "publication_year",
    ]

    def save(self):
        if not self.id:
            db.session.add(self)
        db.session.commit()

    def __repr__(self):
        return f"<Book {self.title}"

    @staticmethod
    def get_by_id(id):
        return Book.query.get(id)

    @staticmethod
    def get_by_isbn(isbn):
        return Book.query.filter_by(isbn=isbn).first()

    @staticmethod
    def get_all_filtered(filter):
        filter = f"{filter}%"
        return Book.query.filter(db.or_(db.cast(Book.isbn, db.String).like(filter), Book.title.like(filter), Book.author.like(filter)))

    @staticmethod
    def books():
        return json.dumps([book.to_dict() for book in Book.query.all()])

class Review(BaseModel):

    __tablename__ = 'reviews'

    id = db.Column(db.Integer, primary_key=True)
    book_id = db.Column(db.Integer, db.ForeignKey('books.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    text = db.Column(db.String(120), nullable=False)
    rating = db.Column(db.Integer, nullable=False)

    __table_args__ = (db.UniqueConstraint('book_id', 'user_id', name="_book_user_uc"), )

    def save(self):
        if not self.id:
            db.session.add(self)
        db.session.commit()

    def get_user(self, user_id):
        return User.get_by_id(user_id)

    @staticmethod
    def get_all():
        return Review.query.all()

    def __repr__(self):
        return f"<Review {self.id}"