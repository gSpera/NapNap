import json
import datetime
from flask import *
from flask_sqlalchemy import *

cfg = json.loads(open("private/config.json", "r").read())
app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = cfg["DB_URL"]
db = SQLAlchemy(app)


class Comment():
    def __init__(self, text):
        self.text = text


class Post(db.Model):
    Id = db.Column(db.Integer, unique=True, primary_key=True)
    author = db.Column(db.String)
    text = db.Column(db.String)
    date = db.Column(db.Date)

    def __init__(self, author, text):
        self.author = author
        self.text = text
        self.date = datetime.datetime.now()


class User(db.Model):
    UserId = db.Column(db.String, unique=True, primary_key=True)
    name = db.Column(db.String(10))
    cognome = db.Column(db.String(10))
    img = db.Column(db.String)
    backImg = db.Column(db.String)
    desc = db.Column(db.String(255))

    def __init__(self, name, cognome, img, desc):
        lastId = User.query.filter_by(
                                    name=name,
                                    cognome=cognome
                                    ).order_by(
                                        User.UserId.desc()
                                        ).first()
        if lastId is None:
            lastId = "-1"
        else:
            lastId = lastId.UserId.replace("{name}.{cognome}.".format(
                        name=name,
                        cognome=cognome), "")
        lastId = int(lastId)
        lastId += 1
        app.logger.info(lastId)
        self.name = name
        self.cognome = cognome
        self.img = img
        self.desc = desc
        self.UserId = "{name}.{cognome}.{Id}".format(
                                                name=self.name,
                                                cognome=self.cognome,
                                                Id=lastId
                                                )

    def __repr__(self):
        return "<User {name}.{cognome}.{id}>".format(
                                                name=self.name,
                                                cognome=self.cognome,
                                                id=self.Id
                                            )


@app.route("/login")
def login():
    res = make_response(render_template("Login.html"))
    res.set_cookie("UserId", "Jack.Spera.0")
    return res


@app.route("/api/addPost", methods=["POST"])
def addPost():
    author = request.cookies.get("UserId")
    if author is None:
        return redirect("/login", code=302)
    text = request.form["text"]
    post = Post(author, text)
    db.session.add(post)
    db.session.commit()
    return "Ok"


@app.route("/")
def index():
    cookie = request.cookies.get("UserId")
    if cookie is None:
        return redirect("/login", code=302)
    return homePage(Id=cookie)


@app.route("/u/<string:Id>")
def homePage(Id=None):
    if Id is None:
        return redirect("/login", code=302)
    cookie = request.cookies.get("UserId")
    u = User.query.filter_by(UserId=Id).first()
    posts = Post.query.filter_by(author=Id).order_by(Post.Id.desc()).all()
    if cookie is None:
        cookie = "Login"
    return render_template("HomePage.html",
                           user=u,
                           posts=posts,
                           cfg=cfg,
                           Cookie=cookie,
                           login=cookie
                           )

if __name__ == "__main__":
    app.run(port=807, debug=True)
