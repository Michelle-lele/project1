import os
import sys

from flask import Flask, session, render_template, request
from flask_session import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

app = Flask(__name__)

# Check for environment variable
if not os.getenv("DATABASE_URL"):
    raise RuntimeError("DATABASE_URL is not set")

# Configure session to use filesystem
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Set up database
engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))


@app.route("/", methods=["POST", "GET"])
def index():


	if request.method == "POST":
		errorMessages= []
		#ensure required fields are submitted
		if not request.form.get("username"):
			errorMessages.append("Username is required!")
		
		if not request.form.get("password"):
			errorMessages.append("Password is required!")

		if not request.form.get("confirm_password"):
			errorMessages.append("Confirm Password is required!")

		if errorMessages != []:
			return render_template("signup.html", errorMessages=errorMessages)

		#ensure passwords match
		if request.form.get("password") != request.form.get("confirm_password"):
			errorMessages.append("Passwords don't match!")
			return render_template("signup.html", errorMessages=errorMessages)

		#ToDo password validation

		#ensure username doesn't exist
		NewUserName = request.form.get("username")
		usernames= db.execute("SELECT username From users").fetchall()
		#print(usernames, file=sys.stderr)
		for i in range(len(usernames)):
			#print(NewUserName, file=sys.stderr)
			#print(usernames[i][0], file=sys.stderr)
			if NewUserName == usernames[i][0]:
				errorMessages.append("Username already exists!")
				return render_template("signup.html", errorMessages=errorMessages)
		
		#create new user in db
		NewUser = db.execute("INSERT INTO users (username, password, name) VALUES (:username,:password, :name)", 
			{"username": request.form.get("username"), "password": request.form.get("password"), "name": request.form.get("name")})
		db.commit()
		#return render_template("index.html")
		
	return render_template("signup.html")

 