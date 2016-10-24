from Social import app, cfg
import os
HEROKU=False

if HEROKU:
  app.run(host=cfg["Host"], port=int(os.environ.get("PORT")), debug=cfg["Debug"])
else:
  app.run(host=cfg["Host"], port=cfg["Port"], debug=cfg["Debug"])
