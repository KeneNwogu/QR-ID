from flask_wtf import FlaskForm
from wtforms import StringField
from wtforms.validators import DataRequired, URL, Email


class ProfileForm(FlaskForm):
    name = StringField('name', validators=[DataRequired()])
    phone = StringField('phone', validators=[DataRequired()])
    email = StringField('email', validators=[DataRequired(), Email()])
    job_title = StringField('job title', validators=[DataRequired()])
    address = StringField('address', validators=[DataRequired()])
    website = StringField('website', validators=[DataRequired(), URL()])
    facebook = StringField('facebook', validators=[DataRequired(), URL()])
    linkedin = StringField('linkedin', validators=[DataRequired(), URL()])
    instagram = StringField('instagram', validators=[DataRequired(), URL()])
    twitter = StringField('twitter', validators=[DataRequired(), URL()])
