# forms.py
# wft forms classes defined in this file

from flask_wtf import FlaskForm
from wtforms import (StringField, DateField, FloatField,
    RadioField, TextAreaField
) # fields available at https://wtforms.readthedocs.io/en/3.0.x/fields/
from wtforms.validators import DataRequired, Optional, Length, AnyOf

class AddTripForm(FlaskForm): 
    destination = StringField('destination', validators=[DataRequired('Destination Required!'), Length(min=1, max=150, message='max 150 characters')])
    arr_date = DateField('arr_date', format='%d-%m-%Y', validators=[Optional()])
    ret_date = DateField('ret_date', format='%d-%m-%Y', validators=[Optional()])
    category = RadioField('category', choices=[('opt1','leisure'),('opt2','work')], default='opt1', validators=[DataRequired()])
    cost = FloatField('cost', validators=[Optional()])
    people = StringField('people', validators=[Optional()])
    accomodation = StringField('accomodation', validators=[Optional(), Length(max=50)])
    notes = TextAreaField('notes', validators=[Optional(), Length(max=200)])