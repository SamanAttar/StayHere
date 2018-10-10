from flask import Flask, request, render_template, flash, redirect, url_for, session, logging
from flask_mysqldb import MySQL
from wtforms import Form, StringField, TextAreaField, PasswordField, validators, RadioField
from passlib.hash import sha256_crypt
from propertyData import Properties
from RegisterForm import RegisterForm
from PropertyForm import PropertyForm
from functools import wraps


app = Flask('__name__')
mysql  = MySQL()

#config mySQL
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'stayhereuser'
app.config['MYSQL_PASSWORD'] = 'CS4389isCool!'
app.config['MYSQL_DB'] = 'StayHere'
app.config['MYSQL_CURSORCLASS'] = 'DictCursor' #lets us treat the query as a dictionary, by default treats it as a tuple
mysql.init_app(app)


#app = Flask(__name__) #placeholder for app.py

Properties = Properties()

# Check to see if user is logged in
def is_logged_in(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'logged_in' in session:
            return f(*args, **kwargs)
        else:
            flash('Unauhtorized, Please login', 'danger')
            return redirect(url_for('login'))
    return wrap


@app.route('/')
def index():
    return render_template('home.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/signinbad')
def signinbad():
    return render_template('signinbad.html')

@app.route('/properties')
def properties():
    return render_template('properties.html', properties = Properties)

@app.route('/property/<string:id>')
def property(id):
    return render_template('property.html', id=id)

# User login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # Get Form Fields
        username = request.form['username']
        password_candidate = request.form['password']

        # Create cursor
        cur = mysql.connection.cursor()

        # Get user by username
        result = cur.execute("SELECT * FROM users WHERE username = %s", [username])

        if result > 0:
            # Get stored hash
            data = cur.fetchone()
            password = data['password']

            # Compare Passwords
            if sha256_crypt.verify(password_candidate, password):
                # Passed
                session['logged_in'] = True
                session['username'] = username

                flash('You are now logged in', 'success')
                return redirect(url_for('dashboard'))
            else:
                error = 'Invalid login'
                return render_template('login.html', error=error)
            # Close connection
            cur.close()
        else:
            error = 'Username not found'
            return render_template('login.html', error=error)

    return render_template('login.html')

@app.route('/logout')
@is_logged_in
def logout():
    session.clear()
    # flash('You are now logged out', 'success') TODO: this doesnt work
    return render_template('logout.html')


@app.route('/dashboard')
@is_logged_in
def dashboard():
    return render_template('dashboard.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    form = RegisterForm(request.form)
    if request.method == 'POST' and form.validate():
        name = form.name.data
        email = form.email.data
        username = form.username.data
        password = sha256_crypt.encrypt(str(form.password.data))

        cur = mysql.connection.cursor()

        cur.execute("INSERT INTO users(name, email, username, password) VALUES(%s, %s, %s, %s)", (name, email, username, password))

        mysql.connection.commit()

        flash('You are now registered!', 'success')
        cur.close()
        #con.close()
        return redirect(url_for('login'))
    return render_template('signup.html', form = form)

@app.route('/propertySearch', methods = ['POST'])
def searchProperties():
    # eventually query db on location, guests, and maybe checkin and checkout dates
    results = Properties
    searchLocation = request.form['location']
    if searchLocation is not None and searchLocation != '':
        results = list(filter(lambda x: searchLocation.lower() in x['location'].lower(), results))
    searchGuests = int(request.form['guests'])
    results = list(filter(lambda x: x['guests'] >= searchGuests, results))
    return render_template('properties.html', properties = results)


@app.route('/add_property', methods=['GET', 'POST'])
@is_logged_in
def add_property():
    form = PropertyForm(request.form)
    if request.method == 'POST' and form.validate():
        title = form.title.data
        body = form.body.data

        #create cur cursor

        #execute cur cursor into articles table with title, body, author

        #commit to DB:
        #close connection

        #flash message
        flash('Article Created', 'success')

        return redirect(url_for('dashboard'))
    return render_template('add_property.html', form=form)



if __name__ == '__main__':
    app.secret_key = 'CS4389isCool!'
    app.run(port =5050, debug=True)
