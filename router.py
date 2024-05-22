from flask import render_template, request, redirect, url_for, session, flash
from database import User, Stock, StockSell
from app import app, db
from hashlib import sha256

with open("adminpassword.txt", "r") as f:
    adminPassword = f.read()
@app.route("/")
def home():
    if "user" in session:
        logged = True
    else:
        logged = False
    return render_template("main.html", logged=logged)

@app.route("/login", methods=["POST", "GET"])
def login():
    if request.method == "POST":
        name = request.form["username"]
        password = bytes(request.form["password"], "utf-8")
        user = User.query.filter_by(name=name).first()
        if user:
            session["user"] = user.name
            if user.password == sha256(password).hexdigest():
                return redirect(url_for("user"))
            else:
                flash("Špatné heslo.", "error")
                return render_template("login.html")
        else:
            flash("Uživatelské jméno neexistuje.", "error")
            return render_template("login.html", logged=False)
    elif request.method == "GET":
        return render_template("login.html", logged=False)
    
    
@app.route("/user")
def user():
    if "user" in session:
        user = session["user"]
        stocks = Stock.query.filter_by(owner=user).all()
        return render_template("user.html", usr=user, logged=True, stocks=stocks)
    else:
        return redirect(url_for("home"))
    

@app.route("/logout")
def logout():
    if "user" in session:
        user = session["user"]
        session.pop("user", None)
        flash(f"Bylo ti odhlášeno, {user}.", "info")
    return redirect(url_for("home"))

@app.route("/adminLogin", methods=["POST", "GET"])
def adminLogin():
    if request.method == "POST":
        password = bytes(request.form["password"], "utf-8")
        if sha256(password).hexdigest() == adminPassword:
            session["adminLogin"] = True
            return redirect(url_for("admin"))
        else:
            flash("Ty asi nebudeš admin, tak bych se tam moc nehrnul...")
            return redirect(url_for("home"))
    return render_template("adminLogin.html", logged=False)

@app.route("/admin")
def admin():
    if "adminLogin" in session:
        users = User.query.all()
        return render_template("admin.html", users=users)
    else:
        return redirect(url_for("adminLogin"))

@app.route("/admin/addUser", methods=["GET", "POST"])
def adminAddUser():
    
    if "adminLogin" in session:
        users = User.query.all()
        return render_template("adminAddUser.html", users=users, logged=False)
    return redirect(url_for("adminLogin"))

@app.route("/addUser", methods=['POST'])    
def addUser():
    name = request.form["username"]
    password = sha256(bytes(request.form["password"], "utf-8")).hexdigest()
    try:
        money = int(request.form["money"])
    except:
        flash("Peníze musí být pouze číslo.", "error")
        return redirect(url_for("adminAddUser"))
    user = User(name=name, password=password, money=money)
    db.session.add(user)
    stock = Stock(owner=name, name=name, percentage=100)
    db.session.add(stock)
    db.session.commit()
    return redirect(url_for("adminAddUser"))

@app.route("/del/<userId>", methods=["POST", "GET"])
def delete(userId):
    if request.method == "POST" and "adminLogin" in session:
        usr = User.query.filter_by(_id=userId).first()
        stocks = Stock.query.filter_by(owner=usr.name).all()
        db.session.delete(usr)
        for s in stocks: db.session.delete(s)
        db.session.commit()
        return redirect(url_for("adminAddUser"))
    else:
        return "<h1>Tohleto se opravdu nedělá!</h1>"
    
@app.route("/admin/addMoney", methods=["GET"])
@app.route("/admin/addMoney/<userId>", methods=["POST"])
def addMoney(userId=0):
    if request.method == "GET":
        users = User.query.all()
        if "adminLogin" in session:
            return render_template("addUserMoney.html", users=users)
        else:
            return redirect(url_for("adminLogin"))
    elif request.method == "POST":
        if "adminLogin" in session:
            usr = User.query.filter_by(_id=userId).first()
            try:
                amount = int(request.form["amount"])
            except Exception as e:
                flash(f"{e}")
                return redirect("/admin/addMoney")
            usr.money += amount
            db.session.commit()
            return redirect("/admin/addMoney")
    
@app.route("/admin/logout")
def adminLogout():
    if "adminLogin" in session:
        session.pop("adminLogin", None)
    return redirect(url_for("adminLogin"))

@app.route("/sell", methods=["GET"])
@app.route("/sell/<stock_id>", methods=["GET", "POST"])
def sellStock(stock_id=-1):
    if "user" in session:
        if (request.method == "GET") and (int(stock_id) < 0):
            stocks = Stock.query.filter_by(owner=session["user"]).all()
            return render_template("sell.html", stocks=stocks, logged=True)
        elif (request.method == "GET") and (int(stock_id) >= 0):
            stock = Stock.query.filter_by(_id=stock_id).first()
            stocks = Stock.query.all()
            print(stocks)
            if stock.owner == session["user"]:
                return render_template("stockSell.html", stock=stock, logged=True)
            else:
                flash("Tuto akcii nevlastníš!")
                return redirect(url_for("home"))
        elif (request.method == "POST") and (int(stock_id) >= 0):
            stock = Stock.query.filter_by(_id=stock_id).first()
            if stock.owner == session["user"]:
                per = int(request.form["amount"])
                cost = int(request.form["price"])
                old_stock = Stock.query.filter_by(_id=stock_id).first()
                if per <= old_stock.percentage:
                    old_stock.percentage -= per
                    new_stock = Stock(owner=session["user"], name=old_stock.name, percentage=per)
                    db.session.add(new_stock)
                    db.session.flush()
                    db.session.refresh(new_stock)
                    if old_stock.percentage == 0:
                        db.session.delete(old_stock)
                    stock_sell = StockSell(old_owner=new_stock.owner, new_owner=None, stockID=new_stock._id, cost=cost)
                    db.session.add(stock_sell)
                    db.session.commit()
                    return redirect(url_for("user"))
                    
            else:
                flash("Tuto akcii nevlastníš!")
                return redirect(url_for("home"))
    else:
        return redirect(url_for("login"))

@app.route("/buy")
def buy():
    stockSells = StockSell.query.all()
    stock_sells = []
    for s in stockSells:
        print(s, s.stockID)
        stock = Stock.query.filter_by(_id=s.stockID).first()
        stock_sells.append((stock.name, s.old_owner, stock.percentage, s.cost))
    if "user" in session:
        return render_template("buy.html", stock_sells=stock_sells, logged=True)
    else:
        return redirect(url_for("login"))
