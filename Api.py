from Social import *
import requests


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
    follows = Follows.query.filter_by(User=current_user.UserId)

    if follows.filter_by(Follow=followId).first() is not None:
        return "Alreading following this user."
    follow = Follows(current_user.UserId, followId)
    db.session.add(follow)
    db.session.commit()
    return "Ok"


@app.route("/api/removeFollowing/<string:followId>")
@login_required
def removeFollow(followId=""):
    follow = Follows.query.filter_by(User=current_user.UserId).filter_by(Follow=followId).first()
    if follow is None:
        return "You don't follow "+followId
    db.session.delete(follow)
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
    # Telegram Notification
    follower = Follows.query.filter_by(Follow=current_user.UserId).all()
    follower = [User.query.filter_by(UserId=ID.Follow).first() for ID in follower]
    for user in follower:
        requests.get(
                "https://api.telegram.org/bot{bot_token}/sendMessage?chat_id={chat_id}&text={fromU} ha scritto:%0A{text}&parse_mode=Markdown".format(
                 fromU=current_user.name+" "+current_user.cognome, bot_token=cfg["TelegramBotToken"], chat_id=user.TelegramChat, text=text
                ))
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


@app.route("/api/Telegram"+cfg["TelegramBotToken"], methods=["POST"])
def telegramApi():
    def sendMsg(chat_id, msg):
        print chat_id
        requests.get("https://api.telegram.org/bot{bot_id}/sendMessage?chat_id={chat_id}&text={msg}&parse_mode=Markdown".format(
                bot_id=cfg["TelegramBotToken"],
                chat_id=chat_id,
                msg=msg
                )
            )

    data = request.get_data()
    data = json.loads(data)
    print str(data)
    chat_id = data["message"]["chat"]["id"]
    user = User.query.filter_by(TelegramChat=chat_id).all()
    text = data["message"]["text"]
    if text.startswith("/connect"):
        param = text.split(" ")
        if len(param) != 3:
            sendMsg(chat_id, "Utilizzo: `/connect @UserId Password`")
            return "Connect Command Usage"
        if param[1].startswith("@"):
            param[1] = param[1][1:]
        user = User.query.filter_by(UserId=param[1]).first()
        if user is None:
            sendMsg(chat_id, "Questo utente non esiste")
            return "Not Exist user"
        salt = user.Salt
        Hash = user.Hash
        if bcrypt.hashpw(str(param[2]), "$2a$12$"+salt) == Hash:
            user.TelegramChat = chat_id
            db.session.commit()
            sendMsg(chat_id, "Connesso")
            return "Connected"
        else:
            sendMsg(chat_id, "Password Errata")
            return "Password Errata"
    if text.startswith("/remove"):
        param = text.split(" ")
        if len(param) != 2:
            sendMsg(chat_id, "Utilizzo: `/remove @UserId`")
            return "Remove Command Usage"
        if param[1].startswith("@"):
            param[1] = param[1][1:]
        user = User.query.filter_by(UserId=param[1]).first()
        if user is None:
            sendMsg(chat_id, "Utente non collegato.")
            return "Not Connected user"
        if user.TelegramChat == chat_id:
            user.TelegramChat = 0
            db.session.commit()
            sendMsg(chat_id, "Utente Scolleggato")
            return "Disconnected"
        else:
            sendMsg(chat_id, "Utente non collegato.")
            return "Not Connected user"
    if user == []:
        sendMsg(chat_id, "Non sei collegato con nessun account:%0AScrivi `/connect @UserName Password` per connetterti")
        return "Not Connected"
    res = "Sei gia connesso con:%0A"
    for i in user:
        res += "@"+i.UserId+" "+i.name+" "+i.cognome+"%0A"
    res += "%0AUtilizzo:%0AConnetti Utente:`/connect @UserId Password `%0ARimuovi Utente:`/remove @UserId`"
    sendMsg(chat_id, res)
    return "Non Implementato"

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
    langList = request.headers.get("Accept-Language")
    if langList is None:
            g.Lang = cfg["Lang"]
            return
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
    return len(Follows.query.filter_by(User=user.UserId).all())


def getFollowUsers(user):
    res = Follows.query.filter_by(User=user.UserId).all()
    for i in range(len(res)):
        res[i] = User.query.filter_by(UserId=res[i].Follow).first()
    return res


def getNotification(limit=5):
    follow = []
    if not current_user.is_anonymous:
        followU = Follows.query.filter_by(User=current_user.UserId).all()
        followU = [f.Follow for f in followU]
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
