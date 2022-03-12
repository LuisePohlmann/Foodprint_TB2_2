from flask_wtf import FlaskForm as Form
from wtforms import RadioField
from wtforms.validators import ValidationError
from random import randrange

points = 0


class CorrectAnswer(object):
    def __init__(self, answer):
        self.answer = answer

    def __call__(self, form, field):
        message = 'Incorrect answer.'
        if field.data != self.answer:
            raise ValidationError(message)
        global points
        points+=1

questions = 2
quiz_achieve = .4
class PopQuiz(Form):
    class Meta:
        csrf = False

    q1 = RadioField(
        "Where should you store Tomatoes?",
        choices=[('In the fridge.'), ('At room temperature.')],
        validators=[CorrectAnswer('In the fridge.')]
    )
    q2 = RadioField(
        "What is in season in late January?",
        choices=[('Beets'), ("Tomatoes"), ("Blackberries")],
        validators=[CorrectAnswer('Beets')]
    )
