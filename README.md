CS50Wx Web Programming with Python and JavaScript

Project 1 Book reviews website- Python, Flask, PostrgesSQL, SQLAlchemy
https://docs.cs50.net/web/2018/x/projects/1/project1.html

Files

requirements.txt- required packages to run the project

.env- app configurations, ignored in repo- FLASK_APP, FLASK_ENV, FLASK_RUN_PORT, WERKZEUG_DEBUG_PIN, GOODREADS_API_KEY, GOODREADS_SECRET, DATABASE_URL, ITEMS_PER_PAGE (used for pagination)

application.py - application functionality
import.py- script for importing books.csv to database; it will also create the books table in the database
images_import.py- script calling GoodReads API to store in database book covers image urls

books.csv 

static>

styles.css

media>

templates>

404.html - Page not found, custom page. 

book.html - When users click on a book from the results of the search page, they are taken to the book page, with details about the book: its title, author, publication year, ISBN number. 

The page also shows any reviews that users have left for the book on your website and on GoodReads API. In case average ratings are not available from GoodReads API or on the website, the relevant section will not be visible on the page. 

Users are able to submit review on the book page. Once a review is submitted the submission form is hidden and instead the current user review is shown on top of the page. 

index.html - general site layout template

login.html - Users, once registered, are able to log in on the login page and log out on any other page

signup.html - Users are able to register with username, password and optional display name

search.html - Once a user has logged in, they are taken to this page where they can search for a book by ISBN, title and author. 



