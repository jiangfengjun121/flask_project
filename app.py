import os
from flask import (
    Flask, flash, render_template,
    redirect, request, session, url_for)
from flask_pymongo import PyMongo
from bson.objectid import ObjectId
from werkzeug.security import generate_password_hash, check_password_hash
import time
import math
if os.path.exists("env.py"):
    import env

APP_ROOT = os.path.dirname(os.path.abspath(__file__))

os.environ.setdefault("IP", "0.0.0.0")
os.environ.setdefault("PORT", "5000")
os.environ.setdefault("SECRET_KEY", "=dLIHjX@V4J>C[uVEG[v8!{dB3+Xrq")
os.environ.setdefault("MONGO_URI", "mongodb+srv://root:User78@cluster0.ubune.mongodb.net/fix_managers?retryWrites=true&w=majority")
os.environ.setdefault("MONGO_DBNAME", "fix_managers")

app = Flask(__name__)

app.config["MONGO_DBNAME"] = os.environ.get("MONGO_DBNAME")
app.config["MONGO_URI"] = os.environ.get("MONGO_URI")
app.secret_key = os.environ.get("SECRET_KEY")

mongo = PyMongo(app)


@app.route("/")
@app.route("/get_tips")
def get_tips():
    tips = list(mongo.db.tips.find())
    return render_template("tips.html", tips=tips)

@app.route("/search", methods=["GET", "POST"])
def search():
    query = request.form.get("query")
    tips = list(mongo.db.tips.find({"$text": {"$search": query}}))
    return render_template("tips.html", tips=tips)


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        # To check if username already exist in DB
        existing_user = mongo.db.users.find_one(
            {"username": request.form.get("username").lower()})

        if existing_user:
            flash("Username Exists Already")
            return redirect(url_for("register"))

        register = {
            "username": request.form.get("username").lower(),
            "password": generate_password_hash(request.form.get("password"))
        } 
        mongo.db.users.insert_one(register) 

        # New user 'Session' cookie
        session["user"] = request.form.get("username").lower()
        flash("Registration Successful!")
        return redirect(url_for("profile", username=session["user"]))

    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        # confirm if username exists in db
        existing_user = mongo.db.users.find_one(
            {"username": request.form.get("username").lower()})

        if existing_user:
            # confirm hashed password matches user input
            if check_password_hash(
                existing_user["password"], request.form.get("password")):
                    session["user"] = request.form.get("username").lower()
                    flash("Hello, {}".format
                      (request.form.get("username")))
                    return redirect(url_for
                      ("profile", username=session["user"]))
            else:
                # wrong password match
                flash("Wrong Username and/or Password")
                return redirect(url_for("login"))

        else:
            # username doesn't exist
            flash("Wrong Username and/or Password")
            return redirect(url_for("login"))

    return render_template("login.html")

@app.route("/profile/<username>", methods=["GET", "POST"])
def profile(username):
    # To get the session user's username from db
    username = mongo.db.users.find_one(
        {"username": session["user"]})["username"]

    if session["user"]:
        return render_template("profile.html", username=username)

    return redirect(url_for("login"))


@app.route("/logout")
def logout():
    # To get user from session cookie
    flash("You have logged out")
    session.pop("user")
    return redirect(url_for("login"))
    

@app.route("/add_tip", methods=["GET", "POST"])
def add_tip():
    if request.method == "POST":

        target = os.path.join(APP_ROOT, 'static/uploads/')
        if not os.path.isdir(target):
            os.mkdir(target)


        tips_image_arr = []
        for img in request.files.getlist("tips_image"):
            filename = img.filename
            curtime = math.floor(time.time())

            namearr = filename.split(".")
            realfilename = ""
            for i in range(0, len(namearr)):
                realfilename += namearr[i]

                if (i == len(namearr) - 2):
                    realfilename += "_" + str(curtime) + "."
                elif (i < len(namearr) - 2):
                    realfilename += "."

            destination = "/".join([target, realfilename])
            img.save(destination)
            realPath = "/static/uploads/" + realfilename;
            tips_image_arr.append(realPath);

        tip = {
            "category_name": request.form.get("category_name"),
            "tips_name": request.form.get("tips_name"),
            "tips_description": request.form.get("tips_description"),
            "tips_date": request.form.get("tips_date"),
            "created_by": session["user"]
        }

        if len(tips_image_arr) > 0:
            tip["tips_image_array"] = tips_image_arr

        mongo.db.tips.insert_one(tip)
        flash("Tips Added Successfully ")
        return redirect(url_for("get_tips"))


    categories = mongo.db.categories.find().sort("category_name", 1)
    return render_template("add_tip.html", categories=categories)


@app.route("/edit_tip/<tip_id>", methods=["GET", "POST"])
def edit_tip(tip_id):
    if request.method == "POST":
        submit = {
            "category_name": request.form.get("category_name"),
            "tips_name": request.form.get("tips_name"),
            "tips_description": request.form.get("tips_description"),
            "tips_date": request.form.get("tips_date"),
            "created_by": session["user"]
        }
        mongo.db.tips.update({"_id": ObjectId(tip_id)}, submit)
        flash("Tips Updated Successfully ")


    tip = mongo.db.tips.find_one({"_id": ObjectId(tip_id)})
    categories = mongo.db.categories.find().sort("category_name", 1)
    return render_template("edit_tips.html", tip=tip, categories=categories)


@app.route("/delete_tip/<tip_id>")
def delete_tip(tip_id):
    mongo.db.tips.remove({"_id": ObjectId(tip_id)})
    flash("Tips Deleted Succesfully")
    return redirect(url_for("get_tips"))


@app.route("/get_categories")
def get_categories():
    categories = list(mongo.db.categories.find().sort("category_name", 1))
    return render_template("categories.html", categories=categories)


@app.route("/add_category", methods=["GET", "POST"])
def add_category():
    if request.method == "POST":
        category = {
            "category_name": request.form.get("category_name")
        }
        mongo.db.categories.insert_one(category)
        flash("New Category Added")
        return redirect(url_for("get_categories"))

    return render_template("add_categories.html")

@app.route("/edit_category/<category_id>",methods=["GET", "POST"])
def edit_category(category_id):
    if request.method == "POST":
        submit = {
            "category_name": request.form.get("category_name")
        }
        mongo.db.categories.update({"_id": ObjectId(category_id)}, submit)
        flash("Category Updated Successfully")
        return redirect(url_for("get_categories"))

    category = mongo.db.categories.find_one({"_id": ObjectId(category_id)})
    return render_template("edit_category.html", category=category)

@app.route("/delete_category/<category_id>")
def delete_category(category_id):
    
    mongo.db.categories.remove({"_id": ObjectId(category_id)})
    flash("Category Successfully Deleted")
    return redirect(url_for("get_categories"))    


if __name__ == "__main__":
    app.run(host=os.environ.get("IP"),
            port=int(os.environ.get("PORT")),
            debug=True)