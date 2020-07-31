import os
from flask import Flask, render_template, url_for, request, flash, redirect, send_from_directory, session
from flask_sqlalchemy import SQLAlchemy 
from flask_bootstrap import Bootstrap 
from werkzeug.security import generate_password_hash , check_password_hash
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_mail import Mail,Message
from itsdangerous import URLSafeTimedSerializer,SignatureExpired ,BadTimeSignature
app = Flask(__name__)

ALLOWED_EXTENSIONS = set(['pdf', 'png', 'jpg'])

app.config.update(
    MAIL_SERVER='smtp.gmail.com',    
    MAIL_PORT=465,    
    MAIL_USE_SSL=True,    
    MAIL_USERNAME = 'coupledal007@gmail.com',    
    MAIL_PASSWORD = 'happycouple@'
)
mail = Mail(app)
s = URLSafeTimedSerializer('DontTellAnyone') 
app.config['UPLOAD_FOLDER'] = '/home/salil/test/static/images/'
app.config['SECRET_KEY'] = 'DontTellAnyone'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////home/salil/test/database.db'

db = SQLAlchemy(app)

Bootstrap(app)

class User(db.Model):
	
	id = db.Column(db.Integer, primary_key=True)	
	username = db.Column(db.String(100), unique=True)	
	name  = db.Column(db.String(100))	
	lover_name = db.Column(db.String(100))	
	email = db.Column(db.String(100))	
	lover_email = db.Column(db.String(100))
	email_confirm = db.Column(db.String(20))
	lover_email_confirm = db.Column(db.String(20))
	password = db.Column(db.String(100))	
	filename = db.Column(db.String(100))

	def __init__(self, username,name,lover_name,email,lover_email,email_confirm,lover_email_confirm, password, filename):	
		self.username = username		
		self.name = name
		self.lover_name = lover_name
		self.email = email
		self.email_confirm = "False"
		self.lover_email_confirm = "False"
		self.lover_email = email 
		self.password = password
		self.filename = filename


class Activities(db.Model):   
   id = db.Column(db.Integer, primary_key = True)
   activity = db.Column(db.String(1000))
   place = db.Column(db.String(500)) 
   time = db.Column(db.String(20)) 
   date = db.Column(db.String(20))
 
   def __init__(self, activity, place, time, date):      
      self.activity = activity      
      self.place = place
      self.time = time
      self.date = date

class Restaurants(db.Model):  
   id = db.Column(db.Integer, primary_key = True)   
   restaurant_name = db.Column(db.String(1000))
   rating = db.Column(db.Integer)  
   total_users = db.Column(db.Integer) 

   def __init__(self,restaurant_name,rating,total_users):
   	self.restaurant_name = restaurant_name
   	self.rating = rating
   	self.total_users = total_users
   

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
	if 'username' in session:	
		username = session['username']
		user = User.query.filter_by(username=username).first()
		return redirect(url_for('dashboard', user = user.username))
	return render_template('index.html')


@app.route('/register/', methods = ['GET', 'POST'])
def register():
	if 'username' in session:
		username = session['username']
		user = User.query.filter_by(username=username).first()
		return redirect(url_for('dashboard', user = user.username))
	if request.method == 'POST':
		if not request.form['username'] or not request.form['name'] or not request.form['lover_name'] or not request.form['email'] or not request.form['lover_email'] or not request.form['password'] or not request.form['confirm_password']:
			return render_template('register.html', error ="Please enter all the details")

		if 'file' not in request.files:
			return render_template('register.html', error = "No File Part")
		
		if request.form['password'] != request.form['confirm_password']:
			return render_template('register.html', error="Passwords do not match")
		
		f = request.files['file']

		if f.filename == '':
			flash('No Selected file')
			return render_template('register.html', error = "No Selected File" )

		users = User.query.all()
		
		for i in users:
			if request.form['username'] == i.username:
				return render_template('register.html', error="Username already taken.")
	
		if f and allowed_file(f.filename):
			f.filename = request.form['username']+ f.filename[-4:-1] + f.filename[-1]	
			hashed_password = generate_password_hash(request.form['password'], method='sha256')
			new_user = User(request.form['username'],request.form['name'], request.form['lover_name'], request.form['email'], request.form['lover_email'],"False","False",hashed_password, f.filename)
			emails = []
			tokens = []
    		emails.append(request.form['email'])
    		emails.append(request.form['lover_email'])
    		tokens.append(s.dumps(emails[0] , salt='email-confirm'))
    		tokens.append(s.dumps(emails[1] , salt='email-confirm'))
    		msg = Message('Confirmation Email' , sender='coupledal007@gmail.com',recipients=[emails[0]])
    		link = url_for('confirm_email', token=tokens[0],username=request.form['username'],email=emails[0],_external=True)
    		msg.body = 'Welcome to the Couple Family, confirm your email account to signup and enjoy : {}'.format(link)
    		mail.send(msg)
    		msg = Message('Confirmation Email' , sender='coupledal007@gmail.com',recipients=[emails[1]])
    		link = url_for('confirm_email', token=tokens[1],username=request.form['username'],email=emails[1],_external=True)
    		msg.body = 'Welcome to the Couple Family, confirm your email account to signup and enjoy : {}'.format(link)
    		mail.send(msg)
    		f.save(os.path.join(app.config['UPLOAD_FOLDER'], (f.filename)))

    		db.session.add(new_user)

    		db.session.commit()

    		return redirect(url_for('login'))
    	else:

    		return render_template('register.html', error ="Allowed Extensions:('pdf', 'png', 'jpg')")



	return render_template('register.html')

@app.route('/confirm_email/<email>/<username>/<token>')

def confirm_email(email,username,token):
    
    try:
        email = s.loads(token, salt='email-confirm',max_age=3600) 
        user = User.query.filter_by(username=username).first()   
        if ((user.email) == email):
        	user.email_confirm = "True" 
        else:
        	user.lover_email_confirm = "True"
        db.session.commit()
        return redirect(url_for('login'))

    except:
    	return 'the token is wrong!!'  


@app.route('/login/', methods = ['GET', 'POST'])
def login():
	if 'username' in session:
		username = session['username']
		user = User.query.filter_by(username=username).first()	
		return redirect(url_for('dashboard', user = user.username))

	if request.method == 'POST':
		if not request.form['username'] or not request.form['password']:
			return render_template('login.html', error ="Please enter all the details")	
		
		user = User.query.filter_by(username=request.form['username']).first()
		
		if user:	
			if check_password_hash(user.password,request.form['password']):
				if ((user.email_confirm == "False") or (user.lover_email_confirm == "False")):
					return render_template('login.html', error = "Please confirm your and your partener's email id!!")
				session['username'] = request.form['username']
				return redirect(url_for('dashboard',user = user.username))
			else:
				return render_template("login.html", error="Invalid username or password")
		else:
			return render_template("login.html", error="Invalid username or password")
	return render_template('login.html')


@app.route('/<user>/')

def dashboard(user):
	if 'username' in session:
		user = User.query.filter_by(username=user).first()
		return render_template('dashboard.html',user = user.username,filename=user.filename)
	else:
		return redirect(url_for('index'))




@app.route('/show_all/')
def show_all():
	if 'username' not in session:
		return redirect(url_for('index'))

	return render_template('show_all.html', activities = Activities.query.all() )



@app.route('/show_all1/',methods=['GET','POST'])
def show_all1():
	if 'username' not in session:
		return redirect(url_for('index'))
	return render_template('show_all1.html', restaurants = Restaurants.query.all() )



@app.route('/new/', methods = ['GET', 'POST'])
def new():
	if 'username'  not in session:
		return redirect(url_for('index'))
	if request.method == 'POST':
		if not request.form['activity'] or not request.form['place'] or not request.form['time'] or not request.form['date']:
			flash('Please enter all the details', 'error')
			return render_template('new.html')
		else:
			new_activity = Activities(request.form['activity'], request.form['place'], request.form['time'], request.form['date'])
			db.session.add(new_activity)
        	db.session.commit()
        	flash('Bajrang Dal activity successfully added.!')
        	return redirect(url_for('show_all'))
	return render_template('new.html')

@app.route('/new1/', methods = ['GET', 'POST'])
def new1():
	if 'username'  not in session:
		return redirect(url_for('index'))
	if request.method == 'POST':
		if not request.form['restaurant_name'] or not request.form['rating']:
			print "hey"
			flash('Please enter all the details', 'error')
			return render_template('new1.html')
		else:
			new_restaurant = Restaurants(request.form['restaurant_name'], request.form['rating'],1)
			db.session.add(new_restaurant)
			db.session.commit()
			flash('Information successfully updated!')
			return redirect(url_for('show_all1'))
	return render_template('new1.html')

@app.route('/logout/')
def logout():
	session.pop('username', None)
	return redirect(url_for('index'))

if __name__ == '__main__':
	db.create_all()
	app.run( debug = True )