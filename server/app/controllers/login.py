from flask import render_template, abort, request, flash, redirect, url_for
from app import app
from flask_wtf import FlaskForm
from flask_login import current_user, login_user
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import InputRequired, Email, Length
from werkzeug.urls import url_parse
from app import app
from app.repository import Repository

class LoginForm(FlaskForm):
    username = StringField('Your login name', validators=[InputRequired(), Length(min=3, max=20)])
    password = PasswordField('Your password', validators=[InputRequired(), Length(min=5, max=80)])
    remember = BooleanField('Remember me')

    submit = SubmitField('Sign In')

@app.route('/login', methods=['GET', 'POST'])
def login():

    if current_user.is_authenticated:
        return redirect(url_for('index'))

    form = LoginForm()

    if form.validate_on_submit():
        print('Login requested for user %s, pass=%s, remember_me=%s' % (form.username.data, form.password.data, form.remember.data))

        repository = Repository()

        user = repository.read_user(username=form.username.data)
        if user is None:
            flash('Invalid username')
            return redirect(url_for('login'))
        if not user.check_password(form.password.data):
            flash('Invalid password')
            return redirect(url_for('login'))
        login_user(user, remember = form.remember.data)

        next_page = request.args.get('next')
        if not next_page or url_parse(next_page).netloc != '':
            next_page = url_for('index')
        return redirect(next_page)

    return render_template('login.html', form=form)

