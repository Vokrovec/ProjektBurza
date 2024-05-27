from app import db


class User(db.Model):
    _id = db.Column("id", db.Integer, primary_key=True)
    name = db.Column(db.String(40))
    money = db.Column(db.Integer)
    password = db.Column(db.String(70))
    def __init__(self, name, money,password):
        self.name = name
        self.money = money
        self.password = password

class Stock(db.Model):
    _id = db.Column("id", db.Integer, primary_key=True)
    owner = db.Column(db.String(40))
    name = db.Column(db.String(40))
    percentage = db.Column(db.Integer)
    isSelling = db.Column(db.Boolean)
    def __init__(self, owner, name, percentage):
        self.owner = owner
        self.name = name
        self.percentage = percentage
        self.isSelling = False
        
class StockSell(db.Model):
    _id = db.Column("id", db.Integer, primary_key=True)
    old_owner = db.Column(db.String(40))
    new_owner = db.Column(db.String(40))
    cost = db.Column(db.Integer)
    stockID = db.Column(db.Integer)
    sell_end = db.Column(db.DateTime)
    def __init__(self, old_owner, new_owner, stockID, cost, sell_end):
        self.old_owner = old_owner
        self.new_owner = new_owner
        self.stockID = stockID
        self.cost = cost
        self.sell_end = sell_end