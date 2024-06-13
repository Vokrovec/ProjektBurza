from flask import render_template, request, redirect, url_for, session, flash
from database import User, Stock, StockSell
from app import app, db, scheduler
from hashlib import sha256
import datetime
from pytz import timezone

TIMEZONE = timezone("Europe/Prague")
with open("adminpassword.txt", "r") as f:
    adminPassword = f.read()
@app.route("/")
def home():
    if "user" in session:
        logged = True
    else:
        logged = False
    print("spusteno home")    
    return render_template("home.html", logged=logged)

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
        usr = session["user"]
        user = User.query.filter_by(name=usr).first()
        stocks = Stock.query.filter_by(owner=usr).all()
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
    stock = Stock(owner=name, name=name, percentage=10, dividend=0)
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
        flash("Tohleto se opravdu nedělá!")
        return redirect(url_for("home"))
    
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
    if not "user" in session:
        return redirect(url_for("login"))
    if (request.method == "GET") and (int(stock_id) < 0):
        stocks = Stock.query.filter_by(owner=session["user"]).all()
        return render_template("sell.html", stocks=stocks, logged=True)
    elif (request.method == "GET") and (int(stock_id) >= 0):
        stock = Stock.query.filter_by(_id=stock_id).first()
        stocks = Stock.query.all()
        if stock.owner == session["user"]:
            return render_template("stockSell.html", stock=stock, logged=True)
        else:
            flash("Tuto akcii nevlastníš!")
            return redirect(url_for("home"))
    elif (request.method == "POST") and (int(stock_id) >= 0):
        stock = Stock.query.filter_by(_id=stock_id).first()
        if stock.owner != session["user"]:
            flash("Tuto akcii nevlastníš!")
            return redirect(url_for("home"))
            
        elif stock.isSelling:
            flash("Akcie je již v aukci.")
            return redirect(url_for("home"))
        elif request.form["percent"].isdigit() and request.form["price"].isdigit():
            per = int(request.form["percent"])
            cost = int(request.form["price"])
        else:
            flash("Cena a množství musí být číslo.")
            return redirect(url_for("home"))
        minutes = int(request.form["minutes"])
        old_stock = Stock.query.filter_by(_id=stock_id).first()
        if per > old_stock.percentage:
            flash("Tolik akcie nevlastníš.")
            return redirect(url_for("home"))
        elif per <= 0:
            flash("Zadej kladné číslo.")
            return redirect(url_for("home"))
        endTime = datetime.datetime.now(TIMEZONE) + datetime.timedelta(minutes=minutes)
        old_stock.percentage -= per
        new_stock = Stock(owner=session["user"], name=old_stock.name, percentage=per, dividend=stock.dividend)
        new_stock.isSelling = True
        db.session.add(new_stock)
        db.session.flush()
        db.session.refresh(new_stock)
        if old_stock.percentage == 0:
            db.session.delete(old_stock)
        stock_sell = StockSell(old_owner=new_stock.owner, new_owner=None, stockID=new_stock._id, cost=cost, sell_end=endTime)
        db.session.add(stock_sell)
        db.session.commit()
        return redirect(url_for("user"))
            
        

@app.route("/buy")
def buy():
    checkStockSellsEnd()
    stockSells = StockSell.query.all()
    stock_sells = []
    for s in stockSells:
        stock = Stock.query.filter_by(_id=s.stockID).first()
        end_time = f"{s.sell_end.hour}:{s.sell_end.minute}"
        stock_sells.append((stock.name, s.old_owner, stock.percentage, s.cost, s._id, end_time, stock.dividend))
    stock_sells.sort(key=lambda a: a[6])
    if "user" in session:
        return render_template("buy.html", stock_sells=stock_sells, logged=True)
    else:
        return redirect(url_for("login"))

@app.route("/buy/<stockBuyID>", methods=["POST", "GET"])
def stockBuy(stockBuyID):
    checkStockSellsEnd()
    if  not "user" in session:
        return redirect(url_for("login"))
    stockSell = StockSell.query.filter_by(_id=stockBuyID).all()
    if not stockSell:
        flash("Aukce již skončila")
        return redirect(url_for("buy"))
    stockSell = stockSell[0]
    stock = Stock.query.filter_by(_id=stockSell.stockID).first()
    stock_sell = [stock.name, stockSell.old_owner, stock.percentage, stockSell.cost, stock.dividend]
    if request.method == "GET":
        return render_template("stockBuy.html", stock_sell=stock_sell, logged=True)
    elif request.method == "POST":
        user = User.query.filter_by(name=session["user"]).first()
        if not request.form["amount"].isdigit():
            flash("Zadej cenu jako cislo!")
            return redirect(url_for("home"))
        new_price = int(request.form["amount"])
        if new_price > user.money:
            flash("Nemáš dostatek peněz.")
            return redirect(url_for("home"))
        elif datetime.datetime.now(TIMEZONE).replace(tzinfo=None) > stockSell.sell_end:
            flash("Čas vypršel...")
            checkStockSellsEnd()
            db.session.commit()
            return redirect(url_for("home"))
        elif session["user"] == stockSell.old_owner:
            flash("Nemůžeš koupit svoji akcii.")
            return redirect(url_for("home"))
        elif new_price <= stockSell.cost:
            flash("Nemůžeš přihodit méně, než je aktuální cena.")
            return redirect(url_for("home"))
        if  stockSell.new_owner:
            old_new_owner = User.query.filter_by(name=stockSell.new_owner).first()
            old_new_owner.money += stockSell.cost
        stockSell.new_owner = session["user"]
        user = User.query.filter_by(name=stockSell.new_owner).first()
        user.money -= new_price
        stockSell.cost = new_price
        db.session.commit()
        return redirect(f"/buy/{stockBuyID}")

@scheduler.task('interval', id='do_job_1', seconds=60)
def checkStockSellsEnd():
    with app.app_context():
        stockSells = StockSell.query.all()
        for stockSell in stockSells:
            if datetime.datetime.now(TIMEZONE).replace(tzinfo=None) < stockSell.sell_end:
                break
            stock = Stock.query.filter_by(_id=stockSell.stockID).first()
            if stockSell.new_owner:
                oldUser = User.query.filter_by(name=stockSell.old_owner).first()
                userStocks = Stock.query.filter_by(owner=stockSell.new_owner).all()
                for s in userStocks:
                    if stock.name == s.name and not s.isSelling:
                        s.percentage += stock.percentage
                        db.session.delete(stock)
                        break
                else:
                    stock.owner = stockSell.new_owner
                    stock.isSelling = False
                oldUser.money += stockSell.cost
            else:
                userStocks = Stock.query.filter_by(owner=stockSell.old_owner).all()
                for s in userStocks:
                    if stock.name == s.name and not s.isSelling:
                        s.percentage += stock.percentage
                        db.session.delete(stock)
                        break
                else:
                    stock.owner = stockSell.old_owner
            db.session.delete(stockSell)
        db.session.commit()
@app.route("/players")
@app.route("/stocks/<username>")
def player_stocks(username=None):
    players = User.query.all()
    if not username:
        return render_template("players.html", users=players)
    player_stocks = Stock.query.filter_by(owner=username).all()
    return render_template("userStocks.html", stocks=player_stocks)

@app.route("/paydividend", methods=["POST"])
def pay_dividend():
    if "adminLogin" not in session:
        flash("Nejsi admin.")
        return redirect(url_for("home"))
    stocks = Stock.query.all()
    users = User.query.all()
    for stock in stocks:
        company = User.query.filter_by(name=stock.name).first()
        for user in users:
            if user.name != stock.owner:
                continue
            user.money += stock.dividend * (stock.percentage)
            company.money -= stock.dividend * (stock.percentage)
            break
    db.session.commit()
    flash("Dividendy vyplaceny úspěšně.")
    return redirect(url_for("admin"))

@app.route("/changedividend", methods=["POST"])
def change_dividend():
    if not "user" in session:
        flash("Nejsi přihlášen!")
        return redirect(url_for("user"))
    if not request.form["dividend"].isdigit():
        flash("Zadej kladné číslo, jakožto dividendu, kteroužto chceš vypláceti.")
        return redirect(url_for("user"))
    stocks =  Stock.query.all()
    for stock in stocks:
        if stock.name != session["user"]:
            continue        
        stock.dividend = request.form["dividend"]
        print("dividend changed")
        print(stock.dividend)
    db.session.commit()
    return redirect(url_for("user"))

@app.errorhandler(Exception)
def error_site(e):
    flash(str(e))
    return redirect(url_for("home"))