from flask import Flask, render_template
from propertyData import Properties

app = Flask(__name__) #placeholder for app.py

Properties = Properties()

@app.route('/')
def index():
    return render_template('home.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/signin')
def signin():
    return render_template('signin.html')

@app.route('/signinbad')
def signinbad():
    return render_template('signinbad.html')

@app.route('/signup')
def signup():
    return render_template('signup.html')

@app.route('/properties')
def properties():
    return render_template('properties.html', properties = Properties)

@app.route('/property/<string:id>')
def property(id):
    return render_template('property.html', id=id)





if __name__ == '__main__':
    app.run(debug=True)
