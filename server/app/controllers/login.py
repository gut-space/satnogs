from flask import render_template, abort
from app import app
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import InputRequired, Email, Length

class LoginForm(FlaskForm):
    username = StringField('username', validators=[InputRequired(), Length(min=3, max=20)])
    password = PasswordField('password', validators=[InputRequired(), Length(min=8, max=80)])
    remember = BooleanField('remember')
    # Don't understand why , label="Remember me!" doesn't work here. There's an exception about multiply defined labels

    submit = SubmitField('Sign In')

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        print('Login requested for user %s, pass=%s, remember_me=%s' % (form.username.data, form.password.data, form.remember.data))

    return render_template('login.html', form=form)
