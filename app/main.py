#powershell: create virtualenvironment, start it and navigate to folder, then run
#install everything (flask, gunicorn, pandas ...)
#pip freeze > requirements.txt

from flask import Flask, render_template, request, flash
from flask_login import login_user, login_required, logout_user
from flask_wtf import FlaskForm
from config import Config
from wtforms import StringField, PasswordField, SelectField
from wtforms.validators import InputRequired
import app.App as App
import pandas as pd
import datetime
from app.quiz import PopQuiz
from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_user, login_manager
from werkzeug.security import generate_password_hash, check_password_hash
# from app.models import User

from flask import Blueprint
from . import db

main = Blueprint('main', __name__)

df = App.get_values()
list_of_foods = App.list(df)

class AddFoodForm(FlaskForm):
    new_food = SelectField('Food', validators=[InputRequired() ])
    plastic = SelectField("Plastic")

@main.route("/",  methods=["POST", "GET"])
@main.route('/login')
def login():
    return render_template('login.html')

@main.route('/sign-up')
def signup():
    App.create_history()
    return render_template('signup.html')

@main.route("/home", methods=["POST", "GET"])
def home():
    thisweek = App.totals()
    form = AddFoodForm()
    return render_template("home.html", thisweek_CO2 = round(thisweek["CO2"],2), thisweek_water = round(thisweek["water"],2), thisweek_plastic = round(thisweek["plastic"],2), form = form)

@main.route("/Add_Food", methods=["POST", "GET"])
def add_food():
    form = AddFoodForm()
    form.new_food.choices = list_of_foods
    form.plastic.choices = [0,1,2,3]
    if form.validate_on_submit():
        new_food = form.new_food.data
        plastic = form.plastic.data
        food = df[df["Food product"]==new_food]
        App.get_footprints(food, plastic)
        CO2 = float(food["CO2"]/10)
        water = float(food["Water"]/10)
        return render_template("added_Food.html", new_food = new_food, CO2=CO2, water=water, plastic = plastic)
    return render_template("Add_Food.html", form = form)

@main.route("/Statistics",  methods=["POST", "GET"])
def stats():
    import pandas as pd
    App.last_weeks(pd.read_csv("data/example_history.csv", index_col=[0]))
    data = App.sort_for_stats(pd.read_csv("data/week_1.csv", index_col=[0]))
    weeks = App.compare_weeks()
    CO2_max = App.largest_table(pd.read_csv("data/example_history.csv", index_col=[0]))[1]
    CO2_max_table = CO2_max.to_html()
    water_max = App.largest_table(pd.read_csv("data/example_history.csv",index_col=[0]))[0]
    water_max_table = water_max.to_html()
    return render_template("Statistics.html", labels = data[0], CO2_values = data[1], water_values = data[2], plastic_values = data[3], labels_weeks = weeks[0], CO2_weeks = weeks[1], water_weeks = weeks[2], message1 = weeks[3], message2 = weeks[4], tables=[CO2_max_table, water_max_table], titles=["CO2 Maximum", "Water Maximum"])

@main.route("/Tips",  methods=["POST", "GET"])
def Tips():
    return render_template("Tips.html")

@main.route("/seasonal")
def seasonal():
    return redirect("https://www.seasonalfoodguide.org/")


@main.route("/quiz", methods=["GET", "POST"])
def wtf_quiz():
    form = PopQuiz()
    form.validate_on_submit()
    from app.quiz import points, questions, quiz_achieve
    if points / questions >= quiz_achieve:
        return render_template("passed.html", value=f"Youve gotten {(points / questions) * 100}% of the questions right")

    return render_template("quiz.html", form=form)

@main.route("/passed")
def passed():
    return render_template("passed.html")

@main.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('auth.login'))

@main.route("/Me",  methods=["POST", "GET"])
def Me():
    return render_template("Me.html")
