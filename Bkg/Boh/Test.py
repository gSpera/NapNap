from flask import *

app = Flask("Test")
@app.route("/")
def index():
    # if request.cookies.get("username")==None:
    #     app.logger.debug("Usi Il GET")
    #     name=request.args.get("name","NoGET")
    #     res=make_response(render_template('Titolo.html',name=name))
    #     if(name=="NoGET"):
    #         app.logger.debug("Non hai Inserito il GET")
    #         res=make_response(render_template('Titolo.html',name="Non hai inserito il Nome"))
    #     else:
    #         app.logger.debug("Inserito il GET")
    #         res.set_cookie("username",request.args.get("name","NoGET"))
    #     return res
    # else:
    #     app.logger.debug("Usi i cookie")
    #     return render_template('Titolo.html',name=request.cookies.get("username"))
    return render_template("Titolo.html",name=request.args.get("name","NoGET"))
    #return "<h1>Index</h1>"
@app.route("/u/")
@app.route("/u/<string:Username>")
def userPage(Username="NoName"):
    return "<h2>"+Username+"</h2>"

@app.route("/private/")
def errorPrivate():
    return render_template("Errore403.html")
if __name__ == "__main__":
    app.run(port=8080)
