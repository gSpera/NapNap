class Comment(db.Model):
    __tablename__ = "Comments"
    Id = db.Column(db.Integer, unique=True, primary_key=True)
    post = db.Column(db.Integer)
    author = db.Column(db.String(20))
    text = db.Column(db.String(500))
    date = db.Column(db.DateTime(25))

    def __init__(self, post, author, text):
        self.post = post
        self.text = text
        self.author = author.UserId
        self.date = datetime.datetime.now()


class Post(db.Model):
    __tablename__ = "Posts"
    Id = db.Column(db.Integer, unique=True, primary_key=True)
    author = db.Column(db.String(20))
    text = db.Column(db.String(500))
    date = db.Column(db.DateTime(25))

    def __init__(self, author, text):
        self.author = author.UserId
        self.text = text
        self.date = datetime.datetime.now()


class Hashtag(db.Model):
    __tablename__ = "Hashtag"
    Id = db.Column(db.Integer, unique=True, primary_key=True)
    name = db.Column(db.String(25))
    posts = db.Column(db.String(25))

    def __init__(self, name, FirstPost):
        self.name = name
        self.posts = FirstPost

    def __repr__(self):
        return "<Hashtag #"+self.name+">"


class User(db.Model):
    __tablename__ = "Users"
    UserId = db.Column(db.String(20), unique=True, primary_key=True)
    name = db.Column(db.String(10))
    cognome = db.Column(db.String(10))
    img = db.Column(db.String(255))
    desc = db.Column(db.String(255))
    Hash = db.Column(db.String(60))
    Salt = db.Column(db.String(100))
    follows = db.Column(db.String(1000))
    FeedKey = db.Column(db.String(70), unique=True)

    def __init__(self, name, cognome, UserName, password, desc):
        self.UserId = UserName
        self.name = name
        self.cognome = cognome
        self.img = "/static/NewUser.png"
        self.desc = desc
        self.Salt = bcrypt.gensalt()[7:]
        self.Hash = bcrypt.hashpw(str(password), "$2a$12$"+self.Salt)
        self.follows = ""
        self.FeedKey = bcrypt.hashpw(str(password+UserName), bcrypt.gensalt())
        db.session.add(self)
        db.session.commit()

    def __repr__(self):
        return "<User {id}>".format(id=self.UserId)

    @property
    def is_authenticated(self):
        return True

    @property
    def is_active(self):
        return True

    @property
    def is_anonymous(self):
        return False

    def get_id(self):
        return unicode(self.UserId)
