# powershell: create virtualenvironment, start it and navigate to folder, then run
# install everything (flask, gunicorn, pandas ...)
# pip freeze > requirements.txt

import pandas as pd
import datetime
from flask import Flask, render_template, redirect, url_for, request, flash
from flask_login import LoginManager, login_user
from flask_sqlalchemy import SQLAlchemy
from flask import Flask, Blueprint, render_template, redirect, url_for, request, flash
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SelectField
from wtforms.validators import InputRequired
from werkzeug.security import check_password_hash, generate_password_hash, generate_password_hash, check_password_hash

from app import App
from app import models
from config import Config
from app.models import User

db = SQLAlchemy()
df = App.get_values()
list_of_foods = App.list(df)
app = Flask(__name__)


def create():
    global app
    app.config.from_object(Config)
    app.config['SECRET_KEY'] = Config.SECRET_KEY
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///db.sqlite'
    db.init_app(app)
    login_manager = LoginManager()
    login_manager.login_view = 'auth.login'
    login_manager.init_app(app)
    from models import User
    @login_manager.user_loader
    def load_user(user_id):
        # since the user_id is just the primary key of our user table, use it in the query for the user
        return User.query.get(int(user_id))

    from auth import auth as auth_blueprint
    app.register_blueprint(auth_blueprint)

    # blueprint for non-auth parts of app

    return app


class AddFoodForm(FlaskForm):
    new_food = SelectField('Food', validators=[InputRequired()])
    plastic = SelectField("Plastic")

@app.route("/",  methods=["POST", "GET"])
@app.route('/login')
def login():
    return render_template('login.html')

@app.route('/sign-up')
def signup():
    return render_template('signup.html')

@app.route("/Home", methods=["POST", "GET"])
def home():
    thisweek = App.totals()
    form = AddFoodForm()
    return render_template("Home.html", thisweek_CO2=thisweek["CO2"], thisweek_water=thisweek["water"], thisweek_plastic=thisweek["plastic"], form=form)


@app.route("/Add_Food", methods=["POST", "GET"])
def add_food():
    form = AddFoodForm()
    form.new_food.choices = list_of_foods
    form.plastic.choices = [0, 1, 2, 3]
    if form.validate_on_submit():
        new_food = form.new_food.data
        plastic = form.plastic.data
        food = df[df["Food product"] == new_food]
        App.get_footprints(food, plastic)
        CO2 = float(food["CO2"] / 10)
        water = float(food["Water"] / 10)
        return render_template("added_Food.html", new_food=new_food, CO2=CO2, water=water, plastic=plastic)
    return render_template("Add_Food.html", form=form)


@app.route("/Statistics")
def stats():
    import pandas as pd
    App.last_weeks(pd.read_csv("data/history.csv", index_col=[0]))
    data = App.sort_for_stats(pd.read_csv("data/week_1.csv", index_col=[0]))
    weeks = App.compare_weeks()
    CO2_max = App.largest_table(pd.read_csv("data/history.csv", index_col=[0]))[1]
    CO2_max_table = CO2_max.to_html()
    water_max = App.largest_table(pd.read_csv("data/history.csv", index_col=[0]))[0]
    water_max_table = water_max.to_html()
    return render_template("Statistics.html", labels=data[0], CO2_values=data[1], water_values=data[2], plastic_values=data[3], labels_weeks=weeks[0], CO2_weeks=weeks[1], water_weeks=weeks[2], message1=weeks[3], message2=weeks[4], tables=[CO2_max_table, water_max_table], titles=["CO2 Maximum", "Water Maximum"])

@app.route("/Tips")
def Tips():
    return render_template("Tips.html")


@app.route("/Me", methods=["POST", "GET"])
def Me():
    from auth import loggedInUser as liu
    if liu is None:
        return redirect(url_for('auth.login'))
    return render_template("Me.html")


@app.route("/User")
def User():
    from auth import loggedInUser as liu
    if liu is not None:
        return render_template("User.html")
    return redirect(url_for('auth.login'))


@app.route("/usernameChange", methods=["POST"])
def user_change():
    username = request.form.get("username")
    password_current = request.form.get("password")
    from auth import loggedInUser as liu
    if not check_password_hash(liu.password, password_current):
        flash('Current password is incorrect')
        return redirect(url_for('User'))
    if liu is not None:
        user = models.User().query.filter_by(id=liu.id).first()
        user.name = username
        liu.name = username
        db.session.commit()
        return redirect(url_for('Me'))
    else:
        return redirect(url_for('auth.login'))


@app.route("/Password")
def Password():
    from auth import loggedInUser as liu
    if liu is not None:
        return render_template("password_change.html")
    return redirect(url_for('auth.login'))


@app.route("/passwordChange", methods=["POST"])
def password_change():
    password_again = request.form.get("again_password")
    password_new = request.form.get("new_password")
    password_current = request.form.get("current_password")
    if password_new != password_again:
        flash('Passwords do not match')
        return redirect(url_for('Password'))
    from auth import loggedInUser as liu
    if not check_password_hash(liu.password, password_current):
        flash('Current password is incorrect')
        return redirect(url_for('Password'))
    if liu is not None:

        user = models.User().query.filter_by(id=liu.id).first()
        user.password = generate_password_hash(password_new, method='sha256')
        liu.password = generate_password_hash(password_new, method='sha256')
        db.session.commit()
        return redirect(url_for('Me'))
    else:
        return redirect(url_for('auth.login'))

@app.route('/signup', methods=['POST'])
def signup_post():
    email = request.form.get('email')
    name = request.form.get('name')
    password = request.form.get('password')

    user = User.query.filter_by(email=email).first()  # if this returns a user, then the email already exists in database
    if user:  # if a user is found, we want to redirect back to signup page so user can try again
        flash('Email address already exists')
        return redirect(url_for('main.signup'))

    # create a new user with the form data. Hash the password so the plaintext version isn't saved.
    new_user = User(email=email, name=name, password=generate_password_hash(password, method='sha256'))

    # add the new user to the database
    db.session.add(new_user)
    db.session.commit()

    return redirect(url_for('main.login'))


@app.route('/login', methods=['POST'])
def login_post():
    email = request.form.get('email')
    password = request.form.get('password')
    remember = True if request.form.get('remember') else False

    user = User.query.filter_by(email=email).first()

    # check if the user actually exists
    # take the user-supplied password, hash it, and compare it to the hashed password in the database
    if not user or not check_password_hash(user.password, password):
        flash('Please check your login details and try again.')
        return redirect(url_for('app.login'))  # if the user doesn't exist or password is wrong, reload the page
    login_user(user, remember=remember)
    global loggedInUser
    loggedInUser = user
    return redirect(url_for('main.home'))
