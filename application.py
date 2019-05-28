import os 
import sys
import math

from flask import Flask, session, render_template, request, redirect, url_for
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
	#generate dictionary, with pagination settings
	num_items = len(items)
	per_page = int(os.getenv("ITEMS_PER_PAGE"))
	total_pages = math.ceil(num_items/per_page)
	#print(query, file=sys.stderr)
	
	if not page:
		page = 1

	if page > total_pages or page < 1:
		return render_template("404.html", username=username)
		#page = 1
	#add check for TypeError

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
	print(pagination_settings, file=sys.stderr)
		
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
	if request.method == "GET": 
		query = request.args.get("q")
		if not query:
			return render_template("search.html", username = username)
		#print(query, file=sys.stderr)
		# ?TO DO handle multple words in q parameter in a separate function?
	elif request.method == "POST":
		if not request.form.get("search"):
			errorMessage = "Please enter book title, author or ISBN!"
			return render_template("search.html", username = username, errorMessage = errorMessage)
		query = url_for('search') + "?q=" + request.form.get("search") + "&page=1"
		return redirect(query)
		
	search_results = db.execute("SELECT title, author, isbn, year from books WHERE title ILIKE :query OR author ILIKE :query OR isbn ILIKE :query",
		{"query": "%" + query + "%"}).fetchall()
	#print(search_results, file=sys.stderr)

	#Show message if no results
	if search_results == []:
		errorMessage = f"No books found for your search \"{query}\""
		return render_template("search.html", username = username, errorMessage = errorMessage)

	return paginate(search_results, request.args.get('page', type=int), query=query)

@app.route("/book", methods=["POST", "GET"])
@app.route("/book/<string:isbn>", methods=["POST", "GET"])
@login_required
def book():
	if request.method == "GET":
		if not request.args.get("isbn"):
			return redirect("search")
	book_details = db.execute("SELECT title, author, isbn, year from books WHERE isbn = :isbn", 
			{"isbn": request.args.get("isbn")}).fetchone()
	#print(book_details, file=sys.stderr)
	if request.method == "POST":
		errorMessages = []
		if not request.form.get("rating"):
			errorMessages.append("Rating is required!")
		print(request.form.get("rating"), file=sys.stderr)
		if not request.form.get("review_text"):
			errorMessages.append("Review text is required!")
		if errorMessages != []:
			return render_template("book.html", username = username, book_details = book_details, errorMessages=errorMessages)
	return render_template("book.html", username = username, book_details = book_details)



	