from flask import render_template
from app import app

@app.route('/obslist/')
def obslist():
    return render_template('obslist.html')