#!/usr/bin/env python3
from app import app

app.config['SECRET_KEY'] = 'the earth is flat'

if __name__ == '__main__':
    app.run(debug=True, port=5000)
