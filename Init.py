from Social import app, cfg
import os

app.run(host=cfg["Host"], port=int(os.environ.get("PORT")), debug=cfg["Debug"])
