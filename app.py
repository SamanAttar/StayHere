from flask import Flask, request, render_template, flash, redirect, url_for, session, logging
import os
import time
from flask_mysqldb import MySQL
from wtforms import Form, StringField, TextAreaField, PasswordField, validators, RadioField
from passlib.hash import sha256_crypt
from propertyData import Properties
from RegisterForm import RegisterForm
from PropertyForm import PropertyForm
from functools import wraps
from werkzeug.utils import secure_filename
# TODO: Look into secure_filename for extra protection
# http://flask.pocoo.org/docs/0.12/patterns/fileuploads/

app = Flask('__name__')
mysql  = MySQL()

UPLOAD_FOLDER = ''

# Prevents XSS -> so they arent able to upload HTML files
# Also make sure to disallow .php files if the server executes them, but who has PHP installed on their server, right? :)
ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg'])
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

#config mySQL
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'CS4389isCool!'
app.config['MYSQL_DB'] = 'StayHereDB'
app.config['MYSQL_CURSORCLASS'] = 'DictCursor' #lets us treat the query as a dictionary, by default treats it as a tuple
mysql.init_app(app)

MAX_LOGIN_ATTEMPTS = 5
INACTIVITY_DUARTION = 120   # log user out after this many seconds of inactivity


#app = Flask(__name__) #placeholder for app.py

Properties = Properties()

def getgroupType():
    if 'username' in session:
        username = session['username']

        cur = mysql.connection.cursor()

        # Get user by username
        groupTypeResult = cur.execute("SELECT groupType FROM users WHERE username = %s", [username])
        groupTypeResult = str(cur.fetchall())

        #check the value in the database
        # DB stores as "GuestButton" or "HostButton"
        if 'GuestButton' in groupTypeResult:

            session["groupType"] = "guestUser"
            session['iAmAGuest'] = True
        else:
            session["groupType"] = "hostUser"
            session['iAmAGuest'] = False
        return groupTypeResult
    else:
        session["groupType"] = "void"
    return "void"

# Check to see if user is logged in
def is_logged_in(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'logged_in' in session:
            if 'last_operation_time' in session and time.time() - session['last_operation_time'] < INACTIVITY_DUARTION:
                return f(*args, **kwargs)
            else:
                session.clear()
                flash('Your session has expired, Please login', 'danger')
                return redirect(url_for('login'))
        else:
            flash('Unauhtorized, Please login', 'danger')
            return redirect(url_for('login'))
    return wrap

# Check to see if user is a guest in
def guestRole(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        #myString = 'I am logged in as a ' +  str(session['groupType'])
        #flash(myString, 'danger')
        if 'groupType' in str(session):
            if session['groupType']:
                session['iAmAGuest'] = True
                return f(*args, **kwargs)
            else:
                session['iAmAGuest'] = False
                flash('Unauthorized. Only a Guest can access this!', 'danger')
                return redirect(url_for('dashboard'))
        else:
            session['groupType'] = "User Not Signed In"
            session['iAmAGuest'] = False
        return redirect(url_for('dashboard'))
    return wrap

# Check to see if user is a host
def hostRole(f):
    @wraps(f)
    def wrap(*args, **kwargs):
    #myString = 'I am logged in as a ' +  str(session['groupType'])
        #flash(myString, 'danger')

        if session['groupType']:
            session['iAmAGuest'] = False
            return f(*args, **kwargs)
        else:
            session['iAmAGuest'] = True
            flash('Unauthorized. Only a Host can access this!', 'danger')
            return redirect(url_for('dashboard'))
    return wrap

@app.route('/')
def index():
    if 'last_operation_time' in session and time.time() - session['last_operation_time'] < INACTIVITY_DUARTION:
        session['last_operation_time'] = time.time()
    return render_template('home.html')

@app.route('/about')
def about():
    if 'last_operation_time' in session and time.time() - session['last_operation_time'] < INACTIVITY_DUARTION:
        session['last_operation_time'] = time.time()
    return render_template('about.html')

@app.route('/signinbad', methods=['GET', 'POST'])
def signinbad():
    if request.method == 'POST':
        # Get Form Fields
        username = request.form['username']
        password_candidate = request.form['password']
        tempPermission = request.form.get("permission","")

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
                #session['groupType'] = True
                session['last_operation_time'] = time.time()

                flash('You are now logged in', 'success')
                return redirect(url_for('dashboard'))
            elif tempPermission == "yes":
                #Passed
                session['logged_in'] = True
                session['username'] = username
                session['last_operation_time'] = time.time()
                flash('You are now logged in', 'success')
                return redirect(url_for('dashboard'))
            else:
                error = 'Invalid login'
                return render_template('signinbad.html', error=error)
            # Close connection
            cur.close()
        elif tempPermission == "yes":
            #Passed
            session['logged_in'] = True
            session['username'] = username
            session['last_operation_time'] = time.time()
            flash('You are now logged in', 'success')
            return redirect(url_for('dashboard'))
        else:
            error = 'Username not found'
            return render_template('signinbad.html', error=error)

    return render_template('signinbad.html')

@app.route('/properties')
@guestRole
@is_logged_in
def properties():
    if 'last_operation_time' in session:
        session['last_operation_time'] = time.time()
    return render_template('properties.html', properties = Properties)

@app.route('/property/<string:id>')
def property(id):
    if 'last_operation_time' in session and time.time() - session['last_operation_time'] < INACTIVITY_DUARTION:
        session['last_operation_time'] = time.time()
    return render_template('property.html', id=id)

# User login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':

        # check if user is locked out
        if 'bad_login_count' in session and session['bad_login_count'] >= MAX_LOGIN_ATTEMPTS:
            error = 'You are currently locked out.  Try again tomorrow.'
            return render_template('login.html', error=error)

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
                session.pop('bad_login_count', None)
                #session['groupType'] = True
                session['last_operation_time'] = time.time()

                flash('You are now logged in', 'success')
                return redirect(url_for('dashboard'))
            else:
                if increment_bad_login_count():
                    error = 'Invalid login.  You are now locked out.'
                else:
                    error = 'Invalid login'
                return render_template('login.html', error=error)
            # Close connection
            cur.close()
        else:
            if increment_bad_login_count():
                error = 'Username not found. You are now locked out.'
            else:
                error = 'Username not found'
            return render_template('login.html', error=error)

    return render_template('login.html')

def increment_bad_login_count():
    if 'bad_login_count' not in session:
        session['bad_login_count'] = 1
    else:
        session['bad_login_count'] += 1
    return session['bad_login_count'] >= MAX_LOGIN_ATTEMPTS


@app.route('/logout')
@is_logged_in
def logout():
    session.clear()
    return render_template('logout.html')

@app.route('/dashboard')
@is_logged_in
def dashboard():
    if 'last_operation_time' in session:
        session['last_operation_time'] = time.time()
    # Verify the Group Type to see if host or guest
    str = getgroupType()
    return render_template('dashboard.html')


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    session.clear()
    form = RegisterForm(request.form)
    if request.method == 'POST' and form.validate():
        name = form.name.data
        email = form.email.data
        username = form.username.data
        password = sha256_crypt.encrypt(str(form.password.data))
        groupType = form.groupType.data


        cur = mysql.connection.cursor()

        cur.execute("INSERT INTO users(name, email, username, password, groupType) VALUES(%s, %s, %s, %s, %s)", (name, email, username, password, groupType))

        mysql.connection.commit()

        flash('You are now registered!', 'success')
        cur.close()
        #con.close()
        return redirect(url_for('login'))
    return render_template('signup.html', form = form)

@app.route('/propertySearch', methods = ['POST'])
def propertySearch():
    if 'last_operation_time' in session and time.time() - session['last_operation_time'] < INACTIVITY_DUARTION:
        session['last_operation_time'] = time.time()
    # eventually query db on location, guests, and maybe checkin and checkout dates
    results = Properties
    searchLocation = request.form['location']
    if searchLocation is not None and searchLocation != '':
        results = list(filter(lambda x: searchLocation.lower() in x['location'].lower(), results))
    if (request.form['guests'] == ''):
        searchGuests = 0
    else:
        searchGuests = int(request.form['guests'])
    results = list(filter(lambda x: x['guests'] >= searchGuests, results))
    if (not 'logged_in' in session and len(results) > 0):
        del results[1:]
        return render_template('properties_notLogin.html', properties = results)
    elif (len(results) == 0):
        return render_template('no_property.html')
    else:
        return render_template('properties.html', properties = results)

@app.route('/searchProperties', methods=['GET', 'POST'])
def searchProperties():
    if 'last_operation_time' in session and time.time() - session['last_operation_time'] < INACTIVITY_DUARTION:
        session['last_operation_time'] = time.time()
    return render_template('property_search.html')


@app.route('/add_property', methods=['GET', 'POST'])
@is_logged_in
@hostRole
def add_property():
    if 'last_operation_time' in session:
        session['last_operation_time'] = time.time()
    form = PropertyForm(request.form)
    if request.method == 'POST' and form.validate():
        title = form.title.data
        body = form.body.data
        cur = mysql.connection.cursor()
        user_id = cur.execute("SELECT id from users WHERE username = %s", session['username'])
        user_id = cur.fetchone()
        cur.close()
        print("From add propety Id")
        print (user_id)

        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO Properties(title, body, user_id) VALUES(%s, %s, %s)", (title, body, user_id))
        mysql.connection.commit()
        cur.close()
        flash('Property Created', 'success')

        return redirect(url_for('dashboard'))
    return render_template('add_property.html', form=form)

@app.route('/view_property', methods=['GET', 'POST'])
@hostRole
def view_files():

    # TODO either encrypt and create a new session token every few minutes
    userName = session['username']
    print ("User name is")
    print (userName)

    cur = mysql.connection.cursor()
    userId = cur.execute("SELECT id from users WHERE username = %s", userName)
    userId = cur.fetchone()
    cur.close()

    print ("User ID is")
    print (userId)


    cur = mysql.connection.cursor()
    result = cur.execute("SELECT title, property_description from Properties WHERE user_id = %s", [userId])
    rows = cur.fetchall()
    cur.close()
    return render_template('view_property.html', rows=rows)

@app.route('/profile', methods=['GET', 'POST'])
def profile():
    if 'last_operation_time' in session and time.time() - session['last_operation_time'] < INACTIVITY_DUARTION:
        session['last_operation_time'] = time.time()
    currentUserId = session['username']
    cur = mysql.connection.cursor()
    result = cur.execute("SELECT name, email, username FROM users WHERE id = %s", [currentUserId])
    result = cur.fetchone()
    cur.close()

    with app.open_resource('./static/json/particleJSON.json') as f:
        json_data = json.load(f)
    return render_template('profile.html', result=result, json_data=json_data)

@app.route('/upload', methods=['GET', 'POST'])
def upload():
    if 'last_operation_time' in session and time.time() - session['last_operation_time'] < INACTIVITY_DUARTION:
        session['last_operation_time'] = time.time()
    if request.method == 'POST':

        # check if the post request has the file part
        if 'file' not in request.files:
            flash('No file part', 'danger')
            return redirect(request.url)

        file = request.files['file']

        # if user does not select file, browser also
        # submit a empty part without filename
        if file.filename == '':
            flash('No selected file', 'danger')
            return redirect(request.url)

        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            flash('Yo, File saved!', 'success')
            return redirect(url_for('dashboard', filename=filename))
    return(redirect(url_for('dashboard')))

# Verfiy filename is allowed
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

if __name__ == '__main__':
    app.secret_key = 'CS4389isCool!'
    app.run(host="0.0.0.0", port =5000, debug=True)
