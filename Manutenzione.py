from flask import *

app=Flask("Manutenzione")

@app.route("/")
@app.route("/<path:Path>")
def Manutenzione(Path=None):
	return "<h1>ChangeLog</h1><br>Aggiunta l'opzione Segui su Mobile<br>Nuovo Sistema Commenti"

app.run(host="192.168.1.150",port=8080)
