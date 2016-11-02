from Social import *


@app.route("/favicon.ico")
def Favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'),
                               'favicon.ico',
                               mimetype='image/vnd.microsoft.icon')


@app.route("/")
@login_required
def index():
    return homePage(current_user.UserId)


@app.route("/u/<string:Id>")
@app.route("/u/<string:Id>/<int:page>")
def homePage(Id=None, page=0):
    u = User.query.filter_by(UserId=Id).first()
    posts = []
    if u is None:
        return redirect("/search/"+Id)
    while True:
        if not len(Post.query.filter_by(author=Id).all()):
            break
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
    users = Follows.query.filter_by(User=current_user.UserId).all()
    users = [u.Follow for u in users]
    posts = []

    if users == []:
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
        name = request.form["name"]
        cognome = request.form["cognome"]
        password = request.form["password"]
        desc = request.form["desc"]
        if len(username) > 20:
            flash("Username troppo lungo", "error")
            return redirect("/register")
        if len(name) > 10:
            flash("Nome troppo lungo", "error")
            return redirect("/register")
        if len(cognome) > 10:
            flash("Cognome troppo lungo", "error")
            return redirect("/register")
        if len(desc) > 255:
            flash("Descrizione troppo lunga", "error")
            return redirect("/register")
        if User.query.filter_by(UserId=username).first() is not None:
            flash("Nickname gia esistente", "error")
            return redirect("/register")
        if UserNameRE.search(username):
            flash("Nickname Non Valido", "error")
            return redirect("/register")
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


@app.route("/img/<string:name>.png")
def getProfileImage(name):
    return send_from_directory("img/",
                               name+".png",
                               mimetype='image/png')


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
