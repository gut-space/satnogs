from app import app

@app.route('/')
@app.route('/index')
def index():
    return "New SATNOGS-GDN webpage. Pure awesomeness coming soon. Be patient..."