from flask import *

app = Flask("Test")


@app.route("/")
def index():
    return "Index"


@app.route("/#<string:hashtag>")
def hash(hashtag):
    return "Hash:"+hashtag
if __name__ == "__main__":
    app.run(port=8080)
