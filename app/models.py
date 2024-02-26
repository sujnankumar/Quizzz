from . import db
from flask_login import UserMixin
from datetime import datetime
import secrets
import uuid

def generate_random_link_uuid():
    return str(uuid.uuid4())

def generate_random_link_secrets():
    return secrets.token_urlsafe(8)

def generate_unique_quiz_link():
    while True:
        random_link = generate_random_link_secrets() 
        existing_quiz = Quiz.query.filter_by(link=random_link).first()
        if not existing_quiz:
            return random_link

attempt_questions = db.Table('attempt_questions',
    db.Column('attempt_id', db.Integer, db.ForeignKey('quizattempt.id'), primary_key=True),
    db.Column('question_id', db.Integer, db.ForeignKey('question.id'), primary_key=True)
)

class User(UserMixin, db.Model):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    usn = db.Column(db.String(10), unique=True, nullable=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(10), nullable=False, default='user')
    results = db.relationship('Result', back_populates='user') 
    attempts = db.relationship('QuizAttempt', back_populates='user')

class Question(db.Model):
    __tablename__ = 'question'
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.String(200), nullable=False)
    correct_answer = db.Column(db.String(200), nullable=False)
    quiz_id = db.Column(db.Integer, db.ForeignKey('quiz.id'), nullable=False)
    options = db.relationship('Option', backref='question', lazy=True, cascade="all, delete-orphan")
    points = db.Column(db.Integer, nullable=False, default=1)
    attempts = db.relationship('QuizAttempt', secondary=attempt_questions, back_populates='questions')
    
class Option(db.Model):
    __tablename__ = 'option'
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.String(200), nullable=False)
    question_id = db.Column(db.Integer, db.ForeignKey('question.id'), nullable=False)

class Quiz(db.Model):
    __tablename__ = 'quiz'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), nullable=False)
    time_limit = db.Column(db.Integer, nullable=True)
    num_questions_display = db.Column(db.Integer, nullable=False)
    link = db.Column(db.String(255), unique=True, nullable=False, default=generate_unique_quiz_link)
    admin_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    questions = db.relationship('Question', backref='quiz', lazy=True, cascade='all, delete-orphan')
    results = db.relationship('Result', back_populates='quiz')
    start_time = db.Column(db.DateTime, nullable=True)
    end_time = db.Column(db.DateTime, nullable=True)
    attempts = db.relationship('QuizAttempt', back_populates='quiz')

class Result(db.Model):
    __tablename__ = 'result'
    id = db.Column(db.Integer, primary_key=True)
    score = db.Column(db.Integer, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    quiz_id = db.Column(db.Integer, db.ForeignKey('quiz.id'), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    user = db.relationship('User', back_populates='results')  
    quiz = db.relationship('Quiz', back_populates='results') 
    attempted = db.Column(db.Boolean, default=False, nullable=False)

class UserAnswer(db.Model):
    __tablename__ = 'useranswer'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    quiz_id = db.Column(db.Integer, db.ForeignKey('quiz.id'), nullable=False)
    question_id = db.Column(db.Integer, db.ForeignKey('question.id'), nullable=False)
    option_id = db.Column(db.Integer, db.ForeignKey('option.id'), nullable=False)
    attempt_id = db.Column(db.Integer, db.ForeignKey('quizattempt.id'), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', backref='user_answers')
    quiz = db.relationship('Quiz', backref='quiz_answers')
    question = db.relationship('Question', backref='question_answers')
    option = db.relationship('Option', backref='option_answers')
    attempt = db.relationship('QuizAttempt', back_populates='user_answers') 

class QuizAttempt(db.Model):
    __tablename__ = 'quizattempt'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    quiz_id = db.Column(db.Integer, db.ForeignKey('quiz.id'), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    completed = db.Column(db.Boolean, default=False, nullable=False)
    user_answers = db.relationship('UserAnswer', back_populates='attempt') 
    user = db.relationship('User', back_populates='attempts')
    quiz = db.relationship('Quiz', back_populates='attempts')
    questions = db.relationship('Question', secondary=attempt_questions, back_populates='attempts')

