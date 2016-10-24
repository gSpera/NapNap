# coding=utf-8

from dependence import *

cfg = json.loads(open("private/config.json", "r").read())
lang = {}
for l in os.listdir("Langs"):
    lang[l[:-5]] = json.loads(open("Langs/"+l, "r").read())
langRe = re.compile("([a-zA-z\-]{0,}[^=\d](?=[,;]))")
app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = cfg["DB_URL"]
app.secret_key = cfg["SECRET_KEY"]
db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
Misaka(app,
       autolink=True,
       fenced_code=True,
       underline=True,
       highlight=True,
       strikethrough=True,
       superscript=True,
       tables=True,
       quote=True,
       space_headers=True
       )

HashtagRE = re.compile("#([^\#\s]+)", re.DOTALL)


@app.before_request
def selectLang():
    langList = request.headers.get("Accept-Language")
    langList = langRe.findall(langList)
    langList.append(cfg["Lang"])
    langDispo = os.listdir("Langs")
    for l in langList:
        if l+".json" in langDispo:
            g.Lang = l
            break


@app.route("/favicon.ico")
def Favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'),
                               'favicon.ico',
                               mimetype='image/vnd.microsoft.icon')


@app.route("/api/addPost", methods=["POST"])
def addPost():
    if current_user.is_anonymous:
        return "Not Logged"
    text = escape(request.form["text"])
    text = HashtagRE.sub("[#\g<1>](/search/HashTag\g<1>)", text)
    post = Post(current_user, text)
    db.session.add(post)
    db.session.commit()
    # Hashtag
    for tag in HashtagRE.findall(escape(request.form["text"])):
        tag = tag.upper()
        query = Hashtag.query.filter_by(name=tag).first()
        if query:
            csv = query.posts.split(",")
            csv.append(str(post.Id))
            query.posts = ",".join(csv)
            db.session.commit()
        else:
            hashTag = Hashtag(tag, str(post.Id))
            db.session.add(hashTag)
            db.session.commit()
    return "Ok"


@app.route("/api/addComment", methods=["POST"])
def addComment():
    if current_user.is_anonymous:
        return "Not Logged"
    text = escape(request.form["text"])
    Id = request.form["id"]
    comment = Comment(Id, current_user, text)
    db.session.add(comment)
    db.session.commit()
    return "Ok"


@app.route("/api/getPosts/<string:username>/<int:offset>")
def getPosts(username, offset):
    posts = Post.query.filter_by(author=username).order_by(
         Post.Id.desc()
        ).offset(offset).limit(cfg["PostLimit"]).all()
    result = []
    for post in posts:
        res = {
                "Id": post.Id,
                "author:": post.author,
                "text": post.text,
                "date": post.date.strftime("%c")
            }
        result.append(res)
    return json.dumps(result)


@app.route("/")
@login_required
def index():
    return homePage(current_user.UserId)


@app.route("/u/<string:Id>")
@app.route("/u/<string:Id>/<int:page>")
def homePage(Id=None, page=0):
    u = User.query.filter_by(UserId=Id).first()
    if u is None:
        return redirect("/search/"+Id)
    while True:
        posts = Post.query.filter_by(author=Id).order_by(
             Post.Id.desc()
            ).offset(page*cfg["PostLimit"]).limit(cfg["PostLimit"]).all()
        if len(posts) != 0:
            break
        page = page-1
    comments = Comment.query.order_by(Comment.Id.desc()).all()
    return render_template("HomePage.html",
                           lang=lang[g.Lang]["HomePage"],
                           user=u,
                           posts=posts,
                           cfg=cfg,
                           login=current_user,
                           comments=comments,
                           getName=getName,
                           getFollowN=getFollowN,
                           getFollowUsers=getFollowUsers,
                           follow=False,
                           notification=getNotification(),
                           pageN=page,
                           URL="/u/"+u.UserId+"/",
                           TopBar=lang[g.Lang]["TopBar"],
                           UserNav=lang[g.Lang]["UserNav"]
                           )


@app.route("/follow")
@app.route("/follow/<int:page>")
@login_required
def follow(page=0):
    users = current_user.follows.split(",")
    posts = []

    if users[0] == "":
        return render_template("NoFollow.html", cfg=cfg,
                               lang=lang[g.Lang]["NoFollow"]
                               )

    comments = Comment.query.order_by(Comment.Id.desc()).all()
    while True:
        posts = Post.query.filter(Post.author.in_(users)).order_by(
                                    Post.date.desc()
            ).offset(page*cfg["PostLimit"]).limit(cfg["PostLimit"]).all()
        if len(posts) != 0:
            break
        page = page-1
    return render_template("HomePage.html",
                           lang=lang[g.Lang]["HomePage"],
                           user=current_user,
                           posts=posts,
                           cfg=cfg,
                           login=current_user,
                           comments=comments,
                           getName=getName,
                           getFollowN=getFollowN,
                           getFollowUsers=getFollowUsers,
                           follow=True,
                           notification=getNotification(),
                           pageN=page,
                           URL="/follow/",
                           TopBar=lang[g.Lang]["TopBar"],
                           UserNav=lang[g.Lang]["UserNav"]
                           )


@app.route("/api/addFollowing/<string:followId>")
@login_required
def addFollow(followId=""):
    if followId == current_user.UserId:
        return "Can't follow yourself."

    if current_user.follows == "":
        u = User.query.filter_by(UserId=current_user.UserId).first()
        u.follows = followId
        db.session.commit()
        return "Ok,First Follow"

    follow = current_user.follows.split(",")
    if followId in follow:
        return "Alreading following this user."
    follow.append(followId)
    follow = ",".join(follow)
    current_user.follows = follow
    db.session.commit()
    return "Ok"


@app.route("/api/removeFollowing/<string:followId>")
@login_required
def removeFollow(followId=""):
    follow = current_user
    follow = follow.follows
    follow = follow.split(",")
    if followId not in follow:
        return "You don't follow "+followId
    follow.remove(followId)
    follow = ",".join(follow)
    current_user.follows = follow
    db.session.commit()
    return "Ok"


@app.route("/feed")
@login_required
def FeedPage():
    return render_template("Feed.html",
                           cfg=cfg,
                           lang=lang[g.Lang]["Feed"],
                           user=current_user,
                           )


@app.route("/rss/<string:Key>.xml")
def NotificationRSS(Key=""):
    user = User.query.filter_by(FeedKey=Key).first()
    followU = user.follows.split(",")
    # Ucfg = UserConfig.query.filter_by(UserId=user.UserId).first()
    follow = []

    follow = Post.query.filter(Post.author.in_(followU)).order_by(
        Post.date.desc()
    ).all()
    return Response(render_template("FeedRSS.xml",
                                    cfg=cfg,
                                    notification=follow,
                                    lang=lang[g.Lang]["Feed"]
                                    ),
                    mimetype="application/rss+xml"
                    )


@app.route("/atom/<string:Key>.xml")
def NotificationAtom(Key=""):
    user = User.query.filter_by(FeedKey=Key).first()
    followU = user.follows.split(",")
    # Ucfg = UserConfig.query.filter_by(UserId=user.UserId).first()
    follow = []

    follow = Post.query.filter(Post.author.in_(followU)).order_by(
        Post.date.desc()
    ).all()
    return Response(render_template("FeedAtom.xml",
                                    cfg=cfg,
                                    notification=follow,
                                    lang=lang[g.Lang]["Feed"]
                                    ),
                    mimetype="application/atom+xml"
                    )


# TODO: capire cosa fa questo schifo Notification
@app.route("/notification")
@login_required
def notification():
    return "Notification serve"
    # user = current_user
    # followU = user.follows.split(",")
    # # Ucfg = UserConfig.query.filter_by(UserId=user.UserId).first()
    # follow = []
    #
    # follow = Post.query.filter(Post.author.in_(followU)).order_by(
    #     Post.date.desc()
    # ).all()
    # return render_template("Notifiche.html",
    #                        cfg=cfg,
    #                        lang=lang[g.Lang]["Notification"],
    #                        user=current_user,
    #                        login=current_user,
    #                        notification=follow,
    #                        getName=getName,
    #                        getFollowN=getFollowN,
    #                        getFollowUsers=getFollowUsers,
    #                        follow=False,
    #                        )


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["UserName"]
        password = request.form["Password"]
        if User.query.filter_by(UserId=username).first() is None:
            flash("Questo Utente Non Esiste.")
            return redirect("/register")
        if checkLogin(username, password):
            user = User.query.filter_by(UserId=username).first()
            login_user(user, remember=request.form.get("remember"))
            return redirect("/")
        flash("Username o Password Errata.")
        return redirect("/login")
    return render_template("Login.html", cfg=cfg, lang=lang[g.Lang]["Login"])


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":

        username = request.form["username"]
        if User.query.filter_by(UserId=username).first() is not None:
            flash("NickName gia esistente", "error")
            return redirect("/register")

        name = request.form["name"]
        cognome = request.form["cognome"]
        password = request.form["password"]
        desc = request.form["desc"]

        user = User(name, cognome, username, password, desc)
        login_user(user)
        return redirect("/")
    return render_template("Register.html", cfg=cfg,
                           lang=lang[g.Lang]["Register"]
                           )


@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect("/login")


@app.route("/api/usernameExist/<string:username>")
def UserNameExist(username):
    if User.query.filter_by(UserId=username).first():
        return "Occupato"
    return "Ok"


@app.route("/search/")
@app.route("/search/<int:page>")
@app.route("/search/<string:Keyword>")
@app.route("/search/<string:Keyword>/<int:page>")
def search(Keyword="", page=0):
    Keyword = str(escape(Keyword))
    if len(Keyword) > 7 and Keyword[0:7] == "HashTag":
        return searchHashTag(Keyword, page)
    return searchUser(Keyword, page)


def searchUser(KeyWord="", page=0):
    users = User.query.filter(or_(
        User.UserId.ilike("%"+KeyWord+"%"),
        User.name.ilike("%"+KeyWord+"%"),
        User.cognome.ilike("%"+KeyWord+"%")
    )).offset(page*cfg["PostLimit"]).limit(cfg["PostLimit"]).all()
    URL = "/search/"+KeyWord+"/"
    if KeyWord == "":
        URL = "/search/"
    if len(users) == 0:
        return render_template("SearchNoResult.html",
                               cfg=cfg,
                               lang=lang[g.Lang]["Search"],
                               user=current_user,
                               login=current_user,
                               TopBar=lang[g.Lang]["TopBar"],
                               UserNav=lang[g.Lang]["UserNav"])
    return render_template("SearchUser.html",
                           cfg=cfg,
                           lang=lang[g.Lang]["Search"],
                           search=users,
                           user=current_user,
                           login=current_user,
                           pageN=page,
                           URL=URL,
                           TopBar=lang[g.Lang]["TopBar"],
                           UserNav=lang[g.Lang]["UserNav"]
                           )


def searchHashTag(Keyword="", page=0):
    tag = Hashtag.query.filter(Hashtag.name.ilike(Keyword[7:])).first()
    URL = "/search/"+Keyword+"/"
    if Keyword == "":
        URL = "/search/"
    if not tag:
        return render_template("SearchNoResult.html",
                               cfg=cfg,
                               lang=lang[g.Lang]["Search"],
                               user=current_user,
                               login=current_user,
                               TopBar=lang[g.Lang]["TopBar"],
                               UserNav=lang[g.Lang]["UserNav"])
    postsId = tag.posts.split(",")
    posts = Post.query.filter(Post.Id.in_(postsId))\
                .offset(page*cfg["PostLimit"])\
                .limit(cfg["PostLimit"]).all()

    return render_template("SearchHashTag.html",
                           cfg=cfg,
                           lang=lang[g.Lang]["Search"],
                           search=posts,
                           user=current_user,
                           login=current_user,
                           pageN=page,
                           URL=URL,
                           TopBar=lang[g.Lang]["TopBar"],
                           UserNav=lang[g.Lang]["UserNav"]
                           )


@app.route("/api/changeProfileImage", methods=["POST"])
@login_required
def changeProfileImage():
    form = request.files
    url = request.form["URL"] if request.form["URL"] else None
    if url:
        u = User.query.filter_by(UserId=current_user.UserId).first()
        u.img = url
        db.session.commit()
        return "Ok"
    fl = form["file"] if form["file"] else None
    if fl:
        u = User.query.filter_by(UserId=current_user.UserId).first()
        u.img = "data:image/png;base64,"+b64encode(
            fl.stream.read()
        )
        db.session.commit()
        return "Ok"
    return "Var not set"
    return "Error"


@app.route("/changePassword", methods=["GET", "POST"])
@login_required
def changePassword():
    if request.method == "GET":
        return render_template("ChangePassword.html", cfg=cfg,
                               lang=lang[g.Lang]["ChangePassword"]
                               )

    oldPass = request.form.get("oldPass")
    newPass = request.form.get("newPass")
    newPassCheck = request.form.get("newPassCheck")

    if newPass != newPassCheck:
        flash("Le password non sono identiche.")
        return render_template("ChangePassword.html", cfg=cfg,
                               lang=lang[g.Lang]["ChangePassword"]
                               )
    if checkLogin(current_user.UserId, oldPass):
        u = User.query.filter_by(UserId=current_user.UserId).first()
        u.Hash = bcrypt.hashpw(newPass.encode("utf-8", "ignore"),
                               ("$2a$12$"+u.Salt).encode("utf-8", "ignore")
                               )
        db.session.commit()
        return redirect("/")
    flash("Password Errata.")
    return render_template("ChangePassword.html", cfg=cfg,
                           lang=lang[g.Lang]["ChangePassword"]
                           )


@app.route("/api/editDesc", methods=["POST"])
@login_required
def editDesc():
    text = request.form["text"] \
        if request.form["text"] else "Nessuna Descrizione"
    if text:
        u = User.query.filter_by(UserId=current_user.UserId).first()
        u.desc = text
        db.session.commit()
        return "Ok"
    return "Error"


@login_manager.user_loader
def load_user(user_id):
    return User.query.filter_by(UserId=user_id).first()


@login_manager.unauthorized_handler
def unauthorized():
    return redirect("/login")


def getName(UserId):
    user = User.query.filter_by(UserId=UserId).first()
    return user.name+" "+user.cognome


def getUser(UserId):
    return User.query.filter_by(UserId=UserId).first()


def getFollowN(user):
    follow = user.follows
    arr = follow.split(",")
    if arr[0] == "":
        return 0
    return len(arr)


def getFollowUsers(user):
    follow = user.follows
    arr = follow.split(",")
    users = []
    if arr[0] == "":
        return []
    for u in arr:
        users.append(User.query.filter_by(UserId=u).first())
    return users


def getNotification(limit=5):
    follow = []
    if not current_user.is_anonymous:
        followU = current_user.follows.split(",")

        follow = Post.query.filter(Post.author.in_(followU)).order_by(
            Post.date.desc()
        ).limit(limit).all()
    return follow


def checkLogin(UserId, password):
        user = User.query.filter_by(
            UserId=UserId
        ).first()
        Hash = bcrypt.hashpw(password.encode("utf-8", "ignore"),
                             str("$2a$12$"+user.Salt)
                             )
        if str(Hash) == str(user.Hash):
            return True
        return False


def formatString(string):
    for i in cfg:
        string = string.replace("{{cfg."+i+"}}", str(cfg[i]))
    return string
app.jinja_env.filters['formatString'] = formatString

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=807, debug=True)
