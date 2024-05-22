from flask import Flask
from flask_sqlalchemy import SQLAlchemy
app = Flask(__name__)
app.secret_key="HovnoKleslo"
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///database.db"
db = SQLAlchemy(app)
from router import *


if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)