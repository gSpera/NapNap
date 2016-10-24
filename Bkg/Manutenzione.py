from flask import *

app=Flask("Manutenzione")

@app.route("/")
@app.route("/<path:Path>")
def Manutenzione(Path=None):
	return "<h1>Manutenzione</h1>"

app.run(host="192.168.1.150",port=8080)
