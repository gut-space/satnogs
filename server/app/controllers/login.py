from flask import render_template, abort, request, flash, redirect, url_for
from app import app
from flask_wtf import FlaskForm
from flask_login import current_user, login_user, UserMixin, LoginManager

from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import InputRequired, Email, Length
from werkzeug.urls import url_parse
from werkzeug.security import generate_password_hash, check_password_hash

from app import app
from app.repository import Repository

class LoginForm(FlaskForm):
    username = StringField('Your login name', validators=[InputRequired(), Length(min=3, max=20)])
    password = PasswordField('Your password', validators=[InputRequired(), Length(min=5, max=80)])
    remember = BooleanField('Remember me')

    submit = SubmitField('Sign In')


class SatnogsUser(UserMixin):

    # The following fields are useful for Flask-login
    # It's basically a reimplementation of UserMixin

    def __init__(self, user):
        # I'm sure there's easier way to do it. There's some magic involving **...
        self.id = user['id']
        self.username = user['username']
        self.digest = user['digest']
        self.email = user['email']
        self.role = user['role']
        self.auth = False

    def check_digest(self, digest: str):
        self.auth = self.digest == digest
        return self.auth

    def check_password(self, passwd: str):
        print("### comparing hashes:")
        return check_password_hash(self.digest, passwd)

    def is_authenticated(self):
        return self.auth

    def is_anonymous(self):
        return not self.auth

    def get_id(self):
        return self.id


@app.route('/login', methods=['GET', 'POST'])
def login():

    if current_user.is_authenticated:
        return redirect(url_for('index'))

    form = LoginForm()

    if form.validate_on_submit():
        print('Login requested for user %s, pass=%s, remember_me=%s' % (form.username.data, form.password.data, form.remember.data))

        repository = Repository()

        user = repository.read_user(username=form.username.data)
        print('Retrieved from DB: %s' % repr(user))

        if user is None:
            print('Invalid username')
            flash('Invalid username')
            return redirect(url_for('login'))

        u = SatnogsUser(user)
        if not u.check_password(form.password.data):
            print('Invalid password')
            flash('Invalid password')
            return redirect(url_for('login'))

        print("Login success!")
        login_user(u, remember = form.remember.data)

        next_page = request.args.get('next')
        if not next_page or url_parse(next_page).netloc != '':
            next_page = url_for('index')
        return redirect(next_page)

    return render_template('login.html', form=form)

login = LoginManager(app)

@login.user_loader
def load_user(user_id):
    rep = Repository()
    u = rep.read_user(id=user_id)
    if u:
        return SatnogsUser(u)
    return None
