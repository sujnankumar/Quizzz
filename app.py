from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import secrets
import random
from datetime import datetime
import re

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///quiz.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['ADMIN_REGISTRATION_KEY'] = 'admin_key'

db = SQLAlchemy(app)
migrate = Migrate(app, db)

login_manager = LoginManager(app)
login_manager.init_app(app)
login_manager.login_view = 'login'


def generate_unique_quiz_link():
    return secrets.token_urlsafe(10)

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    usn = db.Column(db.String(10), unique=True, nullable=True)  # Allow null for admins
    username = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(10), nullable=False, default='user')
    results = db.relationship('Result', backref='user', lazy=True)

class Question(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.String(200), nullable=False)
    correct_answer = db.Column(db.String(200), nullable=False)
    quiz_id = db.Column(db.Integer, db.ForeignKey('quiz.id'), nullable=False)
    options = db.relationship('Option', backref='question', lazy=True)

class Option(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.String(200), nullable=False)
    question_id = db.Column(db.Integer, db.ForeignKey('question.id'), nullable=False)

class Quiz(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), nullable=False)
    time_limit = db.Column(db.Integer, nullable=True)  # Time limit in minutes
    num_questions_display = db.Column(db.Integer, nullable=False)
    link = db.Column(db.String(255), unique=True, nullable=False, default=generate_unique_quiz_link)
    admin_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    questions = db.relationship('Question', backref='quiz', lazy=True)
    results = db.relationship('Result', backref='quiz', lazy=True)

class Result(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    score = db.Column(db.Integer, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    quiz_id = db.Column(db.Integer, db.ForeignKey('quiz.id'), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/')
def home():
    print("Hllo")
    print(app.config['SQLALCHEMY_DATABASE_URI'])
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        
        if user and check_password_hash(user.password, password):
            login_user(user)
            if user.role == 'admin':
                return redirect(url_for('admin_dashboard'))  # Redirect admin to admin dashboard
            else:
                return redirect(url_for('dashboard'))  # Redirect regular user to dashboard
        else:
            flash('Invalid username or password.')
    
    return render_template('login.html')  # Render the login template

@app.route('/admin/register', methods=['GET', 'POST'])
def admin_register():

    if request.method == 'POST':
        name = request.form['name']
        username = request.form['username']
        password = request.form['password']
        registration_key = request.form.get('registration_key')

        if registration_key != app.config['ADMIN_REGISTRATION_KEY']:
            flash('Invalid registration key.')
            return redirect(url_for('admin_register'))

        user_exists = User.query.filter_by(username=username).first()
        if user_exists:
            flash('Username already exists.')
            return redirect(url_for('admin_register'))

        hashed_password = generate_password_hash(password)
        new_admin = User(name=name, username=username, password=hashed_password, role='admin', usn=None)  # Explicitly set usn to None for admins
        db.session.add(new_admin)
        db.session.commit()
        login_user(new_admin)

        flash('New admin created successfully.')
        return redirect(url_for('admin_dashboard'))

    return render_template('admin_register.html')


@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        # Ensure that only users with admin role can login through this route
        admin_user = User.query.filter_by(username=username, role='admin').first()

        if admin_user and check_password_hash(admin_user.password, password):
            login_user(admin_user)
            flash('You have been successfully logged in as admin.', 'success')
            return redirect(url_for('admin_dashboard'))
        else:
            flash('Invalid username or password.', 'error')

    return render_template('admin_login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        usn = request.form.get('usn').upper()  # Ensure USN is uppercase
        username = request.form['username']
        password = request.form['password']
        
        # Validate USN format
        if not re.match(r"4MT\d\d[A-Z][A-Z]\d\d\d", usn):
            flash('USN must be in the format 4MT**$$***.')
            return render_template('register.html')
        
        # Check if the USN already exists
        user_exists = User.query.filter_by(usn=usn).first()
        if user_exists:
            flash('USN already exists')
            return render_template('register.html')
        username_exists = User.query.filter_by(username=username).first()
        if username_exists:
            flash('Username already exists')
            return render_template('register.html')
        hashed_password = generate_password_hash(password)
        new_user = User(name=name, usn=usn, username=username, password=hashed_password)
        try:
            db.session.add(new_user)
            db.session.commit()
            flash('Registration successful!')
            return redirect(url_for('login'))
        except Exception as e:
            db.session.rollback()
            flash('Registration failed. Error: {}'.format(str(e)))

        flash('Registration successful!')
        return redirect(url_for('login'))

    return render_template('register.html')

@app.route('/admin/dashboard')
@login_required
def admin_dashboard():
    if current_user.role != 'admin':
        flash('Access denied: Admins only.', 'error')
        return redirect(url_for('login'))  # Redirect to a general user login page or homepage
    return render_template('admin_dashboard.html')

@app.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/admin/logout')
@login_required
def admin_logout():
    if current_user.role == 'admin':
        logout_user()
        flash('You have been logged out.', 'success')
        return redirect(url_for('admin_login'))  # Redirect specifically to the admin login page
    else:
        flash('Unauthorized access.', 'error')
        return redirect(url_for('login'))  # Fallback for non-admins trying to access the admin logout

@app.route('/add_quiz', methods=['GET', 'POST'])
@login_required
def add_quiz():
    if request.method == 'POST':
        quiz_title = request.form.get('quiz_title')
        quiz_time = request.form.get('quiz_time')
        num_questions_display = int(request.form.get('num_questions_display'))
        
        # Assuming you have a function to generate a unique quiz link
        quiz_link = generate_unique_quiz_link()

        # Create the quiz with the provided details
        new_quiz = Quiz(title=quiz_title, time_limit=quiz_time, link=quiz_link, admin_id=current_user.id)
        db.session.add(new_quiz)
        db.session.flush()  # To get the new_quiz.id for further use before committing
        
        # Here you should also process the added questions and options
        # For simplicity, this step is not shown. You would parse the questions and options
        # from the form, create Question and Option objects, and link them to the new_quiz.
        
        db.session.commit()
        
        # Optionally, redirect to a page showing the quiz details, including the link
        return redirect(url_for('quiz_details', quiz_id=new_quiz.id))
    return render_template('add_quiz.html')

@app.route('/view_results')
@login_required
def view_results():
    # Fetch quiz results from the database
    results = []  # Replace this with your actual logic to fetch results
    return render_template('view_results.html', results=results)  # You need to create this template

@app.route('/quiz/<quiz_link>')
def take_quiz(quiz_link):
    quiz = Quiz.query.filter_by(link=quiz_link).first_or_404()
    
    # Fetch all questions for the quiz
    questions = quiz.questions  # Assuming a relationship is set up in your models
    
    # Randomly select the specified number of questions
    displayed_questions = random.sample(questions, min(len(questions), quiz.num_questions_display))
    
    # Render a template to display these questions
    return render_template('take_quiz.html', questions=displayed_questions, quiz=quiz)

with app.app_context():
    db.create_all()  # Creates the tables if they don't exist yet

if __name__ == '__main__':
    app.run(debug=True)
