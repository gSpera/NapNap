# coding=utf-8

import json
import datetime
import os
import bcrypt
import re
from base64 import *
from flask import *
from flask_sqlalchemy import *
from sqlalchemy import or_
from flaskext.markdown import Markdown
from flask_login import (LoginManager,
                         login_required,
                         login_user,
                         current_user,
                         logout_user
                         )

cfg = json.loads(open("private/config.json", "r").read())
lang = {}
for l in os.listdir("Langs"):
    lang[l[:-5]] = json.loads(open("Langs/"+l, "r").read())
langRe = re.compile("([a-zA-z\-]{0,}[^=\d](?=[,;]))")
app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = cfg["DB_URL"]
app.config["MAX_CONTENT_LENGTH"] = cfg["UploadMaxSize"]
app.secret_key = cfg["SECRET_KEY"]
db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
Markdown(app,sage_mode=True)
#Misaka(app,
#       autolink=True,
#       fenced_code=True,
#       underline=True,
#       highlight=True,
#       strikethrough=True,
#       superscript=True,
#       tables=True,
#       quote=True,
#       space_headers=True
#       )

HashtagRE = re.compile("#([^\#\s]+)", re.DOTALL)
UserNameRE = re.compile("[^a-zA-Z0-9_\&]")


# ------------Model------------ #
from Models import *
# ------------END Model------------ #

# ------------API------------ #
from Api import *
# ------------END Utils------------ #

# ------------Route------------ #
from Route import *
# ------------END Route------------ #



if __name__ == "__main__":
    app.run(host=cfg["Host"], port=cfg["Port"], debug=cfg["Debug"])
