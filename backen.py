from flask import Flask, render_template

app = Flask(__name__)

@app.route('/learn')
def learn():
     return render_template('learn.html')
@app.route('/intro')
def intro():
    return render_template('intro.html')
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


if __name__ == '__main__':
    app.run(debug=True)







