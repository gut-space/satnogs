from flask import Flask

app = Flask(__name__, template_folder='../templates')

from app import routes
