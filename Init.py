from Social import app, cfg
import os
HEROKU=False

application=app
if __name__=="__main__":
  app.run(host=cfg["Host"], port=cfg["Port"], debug=cfg["Debug"])
