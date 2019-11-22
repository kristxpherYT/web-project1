import os
import json
import requests
from os.path import join, dirname
from flask import Flask, session, render_template, request, redirect, url_for, escape
from flask_session import Session
from flask_login import LoginManager, current_user, login_user, logout_user, login_required
from flask_sqlalchemy import SQLAlchemy
from forms import SignupForm, LoginForm
from werkzeug.urls import url_parse
from dotenv import load_dotenv
from sqlalchemy.exc import IntegrityError

dotenv_path = join(dirname(__file__), '.env')  # Path to .env file
load_dotenv(dotenv_path)

app = Flask(__name__)

# Configure the Secret Key
app.config["SECRET_KEY"] = '5539120bd430c586079963dca949ce796e58cce5192f90feeed6dc48446736fd11149876d44a4b4cc3f7abd3cc7969161ef774cf1816d0b8a1b4e2ab59560ab317d78570d02582bc9cbc8b3d7276a3e6'

# Configure session to use filesystem
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure the Login Manager
login_manager = LoginManager(app)
login_manager.login_view = "login"

# Set up database
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get("DATABASE_URL")
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

from models import User, Book, Review

@app.route("/")
def index():
    error = session.get('error', None)
    session.pop('error', None)
    books = None
    if current_user.is_authenticated:
        books = Book.books()
    return render_template("index.html", books=books, error=error)

@app.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.get_by_email(form.email.data)
        if user is not None and user.check_password(form.password.data):
            login_user(user, remember=form.remember_me.data)
            next_page = request.args.get('next')
            if not next_page or url_for(next_page).netloc != '':
                next_page = url_for('index')
            return redirect(next_page)
    return render_template('forms/login_form.html', form=form)

@app.route("/signup", methods=["GET", "POST"])
def sign_up():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = SignupForm()
    error = None
    if form.validate_on_submit():
        name = form.name.data
        email = form.email.data
        password = form.password.data

        # Check if the user exists
        user = User.get_by_email(email)
        if user is not None:
            error = f'The email {email} is already used!'
        else:

            # Create user and save it
            user = User(name=name, email=email)
            user.set_password(password)
            user.save()

            # Log the user in
            login_user(user, remember=True)
            next_page = request.args.get('next', None)
            if not next_page or url_parse(next_page).netloc != '':
                next_page = url_for('index')
            return redirect(next_page)
    return render_template("forms/signup_form.html", form=form, error=error)

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/books', methods=["GET", "POST"])
@login_required
def book_details():
    if request.method == "GET":
        book_id = request.args.get('id')
        book = Book.get_by_id(book_id)
        reviews = book.reviews
        goodreads_response = requests.get("https://www.goodreads.com/book/review_counts.json",
            params={"key": "4wE5OwZaU4jqtXcwTICtPg", "isbns": book.isbn})
        if (goodreads_response):
            goodreads_response = goodreads_response.json()["books"][0]
            goodreads_response['average_rating'] = float(goodreads_response['average_rating'])   
            goodreads_response['ratings_count'] = int(goodreads_response['ratings_count'])
        
        return render_template("book_details.html", book=book, reviews=reviews, goodreads_response=goodreads_response)
    else:
        book_id = request.form['book_id']
        text = request.form['review_text']
        rating = request.form['rating']
        review = Review(book_id=book_id, user_id=current_user.id, text=text, rating=rating)

        try:
            review.save()
        except IntegrityError:
            db.session.rollback()
            session['error'] = "You have already posted a review on the book: <b>" + Book.get_by_id(book_id).title + "</b>!"

        return redirect(url_for('index'))

@app.route('/api/<string:isbn>')
def api_access(isbn):
    book = Book.get_by_isbn(isbn)
    
    review_count = len(book.reviews)
    
    sum = 0
    for review in book.reviews:
        sum += review.rating
    
    average_score = sum / review_count

    response = {
        "title": book.title,
        "author": book.author,
        "year": book.publication_year,
        "isbn": isbn,
        "review_count": review_count,
        "average_score": average_score
    }

    return response

@login_manager.user_loader
def load_user(user_id):
    return User.get_by_id(int(user_id))