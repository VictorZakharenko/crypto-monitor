from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, TextAreaField
from wtforms.validators import ValidationError, DataRequired, Email, Length
from app.models import User, Company
from flask import request

class SearchForm(FlaskForm):
    q = StringField('Search', validators=[DataRequired()])

    def __init__(self, *args, **kwargs):
        if 'formdata' not in kwargs:
            kwargs['formdata'] = request.args
        if 'csrf_enabled' not in kwargs:
            kwargs['csrf_enabled'] = False
        super(SearchForm, self).__init__(*args, **kwargs)

class EditProfileForm(FlaskForm):
    about_me = TextAreaField('About me', validators=[Length(min=0, max=140)])
    submit = SubmitField('Submit')


class CompanyForm(FlaskForm):
    crypto = StringField('Add new crypto here:', validators=[DataRequired(), Length(min=1, max=20)])
    submit = SubmitField('Submit')

    def validate_crypto(self, crypto):
        crypto = Company.query.filter_by(crypto=self.crypto.data).first()
        if crypto is not None:
            raise ValidationError("Look's like this crypto is already exists")


class UserForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    api_key = StringField('api key:', validators=[DataRequired(), Length(min=3, max=34)])
    submit = SubmitField('Submit User for company')

    def validate_email(self, email):
        user = User.query.filter_by(email=self.email.data).first()
        if user is not None:
            raise ValidationError('Please use a different email.')

    def validate_api_key(self, api_key):
        key = User.query.filter_by(api_key=self.api_key.data).first()
        if key is not None:
            raise ValidationError('Please use a different key.')