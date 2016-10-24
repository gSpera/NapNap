from Social import app, cfg

app.run(host=cfg["Host"], port=cfg["Port"], debug=cfg["Debug"])
