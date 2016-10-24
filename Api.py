@app.route("/api/usernameExist/<string:username>")
def UserNameExist(username):
    if User.query.filter_by(UserId=username).first():
        return "Occupato"
    return "Ok"


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
        fl.save("img/"+u.UserId+".png")
        u.img = "/img/"+u.UserId+".png"
        db.session.commit()
        return "Ok"
    return "Var not set"
    return "Error"


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
    if len(text) <= 3:
        return "Too Short"
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
# ------------END API------------ #


# ------------Utils------------ #
@login_manager.user_loader
def load_user(user_id):
    return User.query.filter_by(UserId=user_id).first()


@login_manager.unauthorized_handler
def unauthorized():
    return redirect("/login")


@app.before_request
def selectLang():
    if request.headers.get("X-Forwarded-Proto", "http") != "https":
        return redirect(request.url.replace("http://", "https://", 1), 301)

    langList = request.headers.get("Accept-Language")
    langList = langRe.findall(langList)
    langList.append(cfg["Lang"])
    langDispo = os.listdir("Langs")
    for l in langList:
        if l+".json" in langDispo:
            g.Lang = l
            break


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
