import os, requests

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

@app.route("/", methods=["GET"])
def landing():
    if session.get("user") is None:
        session["user"] = ""
    return render_template("landingPage.html")


@app.route("/success", methods=["POST"])
def success():
#registration functionality
    email = request.form.get("email")
    password = request.form.get("password")
    firstName = request.form.get("firstName")
    lastName = request.form.get("lastName")
    if email is "" or password is "" or firstName is "" or lastName is "":
        return render_template("error.html")
    else:
        db.execute("INSERT INTO users (email, password, firstName, lastName) VALUES (:email, :password, :firstName, :lastName)", {"email":email, "password":password, "firstName":firstName, "lastName":lastName})
        db.commit()
        return render_template("success.html", email=email, password=password)


@app.route("/logIn", methods=["GET", "POST"])
def logIn():
    if session.get("book_id") != None:
        session["book_id"] = None

    if session.get("user") is None:
        session["user"] = ""

    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")
        user = db.execute("SELECT * FROM users WHERE users.email=:email AND users.password=:password", {"email":email, "password":password}).fetchone()

        if user is None:
            loggedIn = False
            user = "notFound"
            return render_template("LogIn.html", loggedIn=loggedIn, user=user)

        user = db.execute("SELECT id FROM users WHERE users.email=:email AND users.password=:password", {"email":email, "password":password}).fetchone()[0]
        session["user"] = user
        loggedIn = True
        return render_template("logIn.html", loggedIn=loggedIn, user=email)
    elif request.method == "GET":
        loggedIn=False
        user=None
        session["user"] = ""
        return render_template("logIn.html", loggedIn=loggedIn, user=user)
    else:
        loggedIn=False
        user=None
        return render_template("logIn.html", loggedIn=loggedIn, user=user)


@app.route("/search", methods=["GET", "POST"])
def search():
    if session.get("book_id") != None:
        session["book_id"] = None
    if request.method == "POST":
        if session.get("user") is None:
            session["user"] = ""
            return render_template("logIn.html")
        elif session.get("user") == "":
            return render_template("logIn.html")
    return render_template("search.html")


@app.route("/bookPage", methods=["POST"])
def book():
#search functionality
    isbnNum = request.form.get("isbn")
    bookAuth = request.form.get("author")
    bookTitle = request.form.get("title")
    #get data via isbn
    if isbnNum != "":
        try:
            book = db.execute("SELECT * FROM books WHERE books.isbn=CAST(:isbnNum AS VARCHAR)", {"isbnNum":isbnNum}).fetchall()
            if book is None:
                    return render_template("notFound.html")
            bookTitle = db.execute("SELECT title FROM books WHERE books.isbn=CAST(:isbnNum AS VARCHAR)", {"isbnNum":isbnNum}).fetchone()[0]
            bookAuthor = db.execute("SELECT author FROM books WHERE books.isbn=CAST(:isbnNum AS VARCHAR)", {"isbnNum":isbnNum}).fetchone()[0]
        except:
            return render_template("error.html")
    #get data via bookTitle (if title and author given)
    elif bookAuth != "" and bookTitle != "":
        try:
            book = db.execute("SELECT * FROM books WHERE books.title=CAST(:bookTitle AS VARCHAR)", {"bookTitle":bookTitle}).fetchall()
            if book is None:
                return render_template("notFound.html")
            isbnNum = db.execute("SELECT isbn FROM books WHERE books.title=CAST(:bookTitle AS VARCHAR)", {"bookTitle":bookTitle}).fetchone()[0]
            bookAuthor = db.execute("SELECT author FROM books WHERE books.title=CAST(:bookTitle AS VARCHAR)", {"bookTitle":bookTitle}).fetchone()[0]
        except:
            return render_template("error.html")
    #get data via bookTitle (just title given)
    elif bookTitle != "":
        try:
            book = db.execute("SELECT * FROM books WHERE books.title=CAST(:bookTitle AS VARCHAR)", {"bookTitle":bookTitle}).fetchall()
            if book is None:
                return render_template("notFound.html")
            isbnNum = db.execute("SELECT isbn FROM books WHERE books.title=CAST(:bookTitle AS VARCHAR)", {"bookTitle":bookTitle}).fetchone()[0]
            bookAuthor = db.execute("SELECT author FROM books WHERE books.title=CAST(:bookTitle AS VARCHAR)", {"bookTitle":bookTitle}).fetchone()[0]
        except:
            return render_template("error.html")
    #get data via author, returns multiple results
    elif bookAuth!= "":
        try:
            book = db.execute("SELECT * FROM books WHERE books.author=CAST(:bookAuth AS VARCHAR)", {"bookAuth":bookAuth}).fetchall()
            if book is None:
                return render_template("notFound.html")
            else:
                return render_template("manyResults.html", books=book)
        except:
            return render_template("error.html")
    #returns book not found
    else:
        return render_template("notFound.html")
    book_id = db.execute("SELECT id FROM books WHERE books.title=CAST(:bookTitle AS VARCHAR)", {"bookTitle":bookTitle}).fetchone()[0]
    session["book_id"] = book_id

    reviewCount = db.execute("SELECT COUNT(*) FROM reviews WHERE book_id=:book_id", {"book_id":str(book_id)})
    session["reviews"] = db.execute("SELECT score, textreview FROM reviews WHERE book_id=:book_id", {"book_id":str(book_id)}).fetchall()
    year = db.execute("SELECT year FROM books WHERE id=:id", {"id":str(book_id)}).fetchone()[0]

    #take away ability to give a second review
    db.commit()
    return render_template("bookPage.html", bookTitle=bookTitle, bookAuthor=bookAuthor, isbnNum=isbnNum, reviews=session["reviews"], year=year)

@app.route("/reviewed", methods=["POST"])
def postReview():

    numberReview = request.form.get("rating")
    textReview = request.form.get("textReview")
    user_id = session.get("user")
    book_id = session.get("book_id")
    #test Print
    #print(f"numberReview:{numberReview}\n textReview:{textReview}\n user_id:{user_id}\n book_id:{book_id}")
    try:
        db.execute("INSERT INTO reviews (user_id, book_id, score, textreview) VALUES (:user_id , :book_id, :score, :textreview)", {"user_id":user_id, "book_id":book_id, "score":numberReview, "textreview":textReview})
        return render_template("postReview.html")
        db.commit()
    except:
        return render_template("error.html")
