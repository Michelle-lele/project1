import os 
import sys
import math
import requests

from flask import Flask, session, render_template, request, redirect, url_for, jsonify,g
from flask_session import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from werkzeug.security import check_password_hash, generate_password_hash
from datetime import timedelta
from functools import wraps

app = Flask(__name__)
app.config.from_envvar('APP_SETTINGS')

# Check for environment variable
if not os.getenv("DATABASE_URL"):
	raise RuntimeError("DATABASE_URL is not set")

# Configure session to use filesystem
app.config["SESSION_PERMANENT"] = True
app.config["SESSION_TYPE"] = "filesystem"
app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(minutes=60)
Session(app)

# Set up database
engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))


# TO DO 404 function & page
def login_required(f):
    """
    Decorate routes to require login.
    http://flask.pocoo.org/docs/0.12/patterns/viewdecorators/
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/login")
        global username
        username = session.get("username")
        return f(*args, **kwargs)
    return decorated_function

def paginate(items, page, query):
	#TODO change the paging implementation to use LIMIT & OFFSET before using in on another places.
	#generate dictionary, with pagination settings
	num_items = len(items)
	per_page = int(os.getenv("ITEMS_PER_PAGE"))
	total_pages = math.ceil(num_items/per_page)
	#print(query, file=sys.stderr)
	
	if not page:
		page = 1

	if page > total_pages or page < 1:
		return render_template("404.html", username=username),404	
		#page = 1
	#TODO add check for TypeError

	if page > 1:
		previous_page = page - 1
	else: 
		previous_page = None

	if page == total_pages:
		next_page = None
	else:
		next_page = page + 1

	pagination_settings = {}
	pagination_settings["page"] = page
	pagination_settings["num_items"] = num_items
	pagination_settings["per_page"] = per_page
	pagination_settings["total_pages"] = total_pages
	pagination_settings["previous_page"] = previous_page
	pagination_settings["next_page"] = next_page
	# print(pagination_settings, file=sys.stderr)
		
	# generate a list of the items on the current page
	first_item_index = (page - 1)* per_page
	if page*per_page > num_items:
		last_item_index = first_item_index + (num_items % per_page) - 1
	else:
		last_item_index= (page*per_page) -1

	page_items = []
	while first_item_index <= last_item_index:
		page_items.append(items[first_item_index])
		first_item_index += 1	
		
	template = request.endpoint + ".html"
	return render_template(template, username=username, page_items=page_items, pagination_settings=pagination_settings, query=query)

@app.route("/", methods=["POST", "GET"])
def index():
	return redirect(url_for('login'))

@app.route("/signup", methods=["POST","GET"])
def signup():
	if session.get('user_id'):
		return redirect(url_for('search'))

	if request.method == "POST":
		errorMessages= []
		#ensure required fields are submitted
		if not request.form.get("username"):
			#print(errorMessages, file=sys.stderr)
			errorMessages.append("Username is required!")
		
		if not request.form.get("password"):
			errorMessages.append("Password is required!")

		if not request.form.get("confirm_password"):
			errorMessages.append("Confirm Password is required!")

		if errorMessages != []:
			return render_template("signup.html", errorMessages=errorMessages)
			
		'''TO DO validate that special characters are not provided in username
		#ensure name is alphanumeric
		if not isalnum(request.form.get("name")):
			errorMessages.append("Username should not contain spaces!")
		'''

		#ensure username has no spaces
		if ' ' in request.form.get("username"):
			errorMessages.append("Username should not contain spaces!")

		#ensure passwords match
		if request.form.get("password") != request.form.get("confirm_password"):
			errorMessages.append("Passwords don't match!")

		if errorMessages != []:
			return render_template("signup.html", errorMessages=errorMessages)

		#ensure password has minimum 8 characters, including characters & numbers
		if len(request.form.get("password")) < 8:
			errorMessages.append("Password should be at least 8 symbols!")
		if not request.form.get("password").isalnum():
			errorMessages.append("Password should contain at least 1 letter or digit!")

		if errorMessages != []:
			return render_template("signup.html", errorMessages=errorMessages)

		#ensure username doesn't exist
		username= db.execute("SELECT * FROM users WHERE username = :username", {"username": request.form.get("username")}).fetchall()
		#print(usernames, file=sys.stderr)
		if len(username) != 0:
			errorMessages.append("Username already exists!")
			return render_template("signup.html", errorMessages=errorMessages)

		
		#create new user in db
		NewUser = db.execute("INSERT INTO users (username, password, name) VALUES (:username,:password, :name)", 
			{"username": request.form.get("username"), "password": generate_password_hash(request.form.get("password")), 
			"name": request.form.get("name")})
		db.commit()
		successMessage = "Registration successful!"
		#print(successMessage, file=sys.stderr)
		return render_template("login.html", successMessage=successMessage)
	return render_template("signup.html")

@app.route("/login", methods=["POST","GET"])
def login():
	if session.get('user_id'):
		return redirect(url_for('search'))

	if request.method == "POST":
		errorMessages= []
		#ensure required fields are submitted
		if not request.form.get("username"):
			#print(errorMessages, file=sys.stderr)
			errorMessages.append("Username is required!")
		
		if not request.form.get("password"):
			errorMessages.append("Password is required!")

		if errorMessages != []:
			return render_template("login.html", errorMessages=errorMessages)

		# Query database for username
		users = db.execute("SELECT * FROM users WHERE username = :username",
						{"username": request.form.get("username")}).fetchall()

		# Ensure username exists and password is correct
		if len(users) != 1 or not check_password_hash(users[0]["password"], request.form.get("password")):
			errorMessages.append("Invalid username and/or password")

		if errorMessages != []:
			return render_template("login.html", errorMessages=errorMessages)

		# Remember which user has logged in
		session["user_id"] = users[0]["user_id"]
		session["username"] = users[0]["username"]

		# Redirect user to search page
		return redirect(url_for('search'))

	# User reached route via GET (as by clicking a link or via redirect)
	else:
		return render_template("login.html")

@app.route("/logout")
def logout():
	session.clear()
	return redirect("/login")

@app.route("/search", methods=["POST", "GET"])
@app.route("/search/<string:query>/<int:page>", methods=["POST", "GET"])
@login_required
def search():
	errorMessage = ""
	top_rated_books = db.execute("SELECT AVG(rating), title,author,isbn, year, cover_img from books JOIN reviews ON books_isbn = isbn GROUP BY isbn ORDER BY AVG(rating) DESC LIMIT 3").fetchall()
	latest_reviews = db.execute("SELECT username, rating, review_text, user_id from users JOIN reviews ON users_user_id = user_id ORDER BY date_created DESC LIMIT 3").fetchall()
	if request.method == "GET":
		query = request.args.get("q")
		if not query:
			return render_template("search.html", username = username, top_rated_books=top_rated_books, latest_reviews=latest_reviews)
		#print(query, file=sys.stderr)
		# ?TO DO handle multple words in q parameter in a separate function?
	elif request.method == "POST":
		if not request.form.get("search"):
			errorMessage = "Please enter book title, author or ISBN!"
			return render_template("search.html", username = username, errorMessage = errorMessage, top_rated_books=top_rated_books, latest_reviews=latest_reviews)
		query = url_for('search') + "?q=" + request.form.get("search") + "&page=1"
		return redirect(query)
		
	search_results = db.execute("SELECT title, author, isbn, year, cover_img from books WHERE title ILIKE :query OR author ILIKE :query OR isbn ILIKE :query ORDER BY title ASC",
		{"query": "%" + query + "%"}).fetchall()
	#print(search_results, file=sys.stderr)

	#Show message if no results
	if search_results == []:
		errorMessage = f"No books found for your search \"{query}\""
		return render_template("search.html", username = username, errorMessage = errorMessage, top_rated_books=top_rated_books, latest_reviews=latest_reviews)

	return paginate(search_results, request.args.get('page', type=int), query=query)

@app.route("/book", methods=["POST", "GET"])
@app.route("/book/<string:isbn>", methods=["POST", "GET"])
@login_required
def book():
	'''
	#TODO back to search results in a cookie
	#TODO paginating reviews
	#TODO have the user review on top
	'''
	if not request.args.get("isbn"):
		return redirect("search")

	#flask.g.isbn= request.args.get("isbn")
	isbn= request.args.get("isbn")
	url= url_for('book')+"?isbn=" + isbn

	book_details = db.execute("SELECT title, author, isbn, year, cover_img, CAST(AVG(rating) as numeric(10,2)), COUNT(rating) from books LEFT JOIN reviews ON isbn = books_isbn WHERE isbn = :isbn GROUP BY isbn", 
			{"isbn": isbn}).fetchone()

	#check if such book exists
	if book_details == None:
		return render_template("404.html", username=username),404
	print(book_details, file=sys.stderr)
	user_reviews = db.execute("SELECT username, rating, review_text, user_id from users JOIN reviews ON users_user_id = user_id WHERE books_isbn = :isbn AND user_id != :user_id ORDER BY date_created DESC",
		{"isbn": isbn, "user_id": session.get("user_id")}).fetchall()

	#check if user has already left a review
	#TODO that in more normal way :D
	user_left_review = db.execute("SELECT username, rating, review_text, user_id from users JOIN reviews ON users_user_id = user_id WHERE books_isbn = :isbn AND user_id = :user_id ORDER BY date_created DESC",
		{"isbn": isbn, "user_id": session.get("user_id")}).fetchall()
	'''
	UserLeftReview = False
	i = 0
	for user in user_reviews:
		if user_reviews[i][3] == session.get("user_id"):
				UserLeftReview = True
		i+=1
	'''
	
	# Get GoodReads average rating and ratings count
	GetBookReviewCounts = requests.get("https://www.goodreads.com/book/review_counts.json?isbns=" + isbn)
	if GetBookReviewCounts.status_code != 200:
		GetBookReviewCounts == None
	else:
		GetBookReviewCounts = GetBookReviewCounts.json()

	if request.method == "POST":
		errorMessages = []
		if not request.form.get("rating"):
			errorMessages.append("Rating is required!")
		if not request.form.get("review_text"):
			errorMessages.append("Review text is required!")
		'''
		#check if user has already left a review
		UserReview = db.execute("SELECT COUNT(*) from reviews WHERE users_user_id = :user_id AND books_isbn = :isbn",
			{"user_id": session.get("user_id"), "isbn": isbn}).fetchall()
		
		if UserReview[0][0] > 0: 
			UserLeftReview = True
			errorMessages.append("You have already left a review!")
		'''

		if errorMessages != []:
			return render_template("book.html", username = username, book_details = book_details, 
				user_reviews=user_reviews, user_left_review=user_left_review, errorMessages=errorMessages,
				GetBookReviewCounts=GetBookReviewCounts)
		
		NewReview = db.execute("INSERT INTO reviews (users_user_id, books_isbn, rating, review_text) VALUES (:user_id, :isbn, :rating, :review_text)", 
			{"user_id": session.get("user_id"), "isbn": isbn, 
			"rating": request.form.get("rating"), "review_text": request.form.get("review_text")})
		db.commit()
		return redirect(url)

	return render_template("book.html", username = username, book_details = book_details, 
		user_reviews=user_reviews, user_left_review=user_left_review, isbn = isbn,
		GetBookReviewCounts=GetBookReviewCounts)

@app.route("/api")
@app.route("/api/<isbn>", methods=['GET'])
def api(isbn):
	#TODO how to return 404 instead of error if isbn is missing
	if not isbn:
		return jsonify(isbn= isbn, error="Book not found!", status = 404), 404

	book_details = db.execute("SELECT title, author, year, isbn from books WHERE isbn = :isbn", 
			{"isbn": isbn}).fetchone()

	#check if such book exists
	if book_details == None:
		return jsonify(isbn= isbn, error="Book not found!", status = 404), 404
			
	title = book_details['title']
	author = book_details['author']
	year = book_details['year']

	review_count = db.execute("SELECT COUNT(*) from reviews WHERE books_isbn = :isbn",
		{"isbn": isbn}).fetchall()
	review_count = review_count[0][0]
	if review_count > 0:
		average_rating = db.execute("SELECT AVG(rating) from reviews WHERE books_isbn = :isbn",
			{"isbn": isbn}).fetchall()
		average_rating = float(average_rating[0][0])
	else: 
		average_rating = None

	return jsonify(title = title, author = author, year=year, isbn=isbn, review_count= review_count, 
		average_rating=average_rating)
