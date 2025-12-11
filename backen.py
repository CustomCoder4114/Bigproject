from flask import Flask, render_template

app = Flask(__name__)

@app.route('/intro')
def intro():
    return render_template('intro.html')
@app.route('/')
def learn():
     return render_template('learn.html')
@app.route('/register')
def register():
    return render_template('register.html')
@app.route('/Login')
def login():
    return render_template('Login.html')
@app.route('/career')
def career():
    return render_template('career.html')
@app.route('/earn')
def earn():
    return render_template('earn.html')
@app.route('/aboutus')
def aboutus():
    return render_template('aboutus.html')
@app.route('/services')
def services():
    return render_template('services.html')
@app.route('/contact')
def contact():
    return render_template('contact.html')
@app.route('/help')
def help():
    return render_template('help.html')

if __name__ == '__main__':
    app.run(debug=True)
