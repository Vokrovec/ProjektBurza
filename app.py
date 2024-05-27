from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_apscheduler import APScheduler
app = Flask(__name__, template_folder='Templates')
app.secret_key="HovnoKleslo"
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///database.db"
db = SQLAlchemy(app)
scheduler = APScheduler()
scheduler.init_app(app)
from router import *

def start():
    scheduler.api_enabled = True
    with app.app_context():
        db.create_all()
    scheduler.start()
    app.run(debug=True)

if __name__ == "__main__":
    start()
