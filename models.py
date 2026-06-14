from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

class User(db.Model, UserMixin):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    
    # Personal Info
    full_name = db.Column(db.String(100), nullable=True)
    college = db.Column(db.String(200), nullable=True)
    degree = db.Column(db.String(100), nullable=True)
    grad_year = db.Column(db.Integer, nullable=True)
    city = db.Column(db.String(100), nullable=True)
    country = db.Column(db.String(100), nullable=True)
    
    # Professional Profile
    skills = db.Column(db.Text, nullable=True, default='')  # Comma-separated (e.g. "Python,React,UI UX")
    experience_level = db.Column(db.String(50), nullable=True, default='Beginner')  # Beginner, Intermediate, Advanced
    availability = db.Column(db.String(50), nullable=True, default='Weekends')  # Weekdays, Weekends, Full Time
    hackathons_attended = db.Column(db.Integer, default=0)
    hackathons_won = db.Column(db.Integer, default=0)
    bio = db.Column(db.Text, nullable=True, default='')
    profile_image = db.Column(db.String(200), nullable=True)  # Gravatar or local filename
    
    # Links
    github_url = db.Column(db.String(200), nullable=True)
    linkedin_url = db.Column(db.String(200), nullable=True)
    portfolio_url = db.Column(db.String(200), nullable=True)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    notifications = db.relationship('Notification', backref='user', lazy=True, cascade="all, delete-orphan")
    ratings = db.relationship('Rating', backref='user', lazy=True, cascade="all, delete-orphan")

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
        
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
        
    def get_skills_list(self):
        if not self.skills:
            return []
        return [s.strip() for s in self.skills.split(',') if s.strip()]

    def get_badge(self):
        """Returns the badge name based on achievements."""
        if self.hackathons_won > 3:
            return "Hackathon Veteran"
        elif "AI" in self.get_skills_list() or "Machine Learning" in self.get_skills_list():
            return "AI Wizard"
        elif "UI UX" in self.get_skills_list() or "Figma" in self.get_skills_list():
            return "Design Pro"
        elif self.hackathons_attended >= 5:
            return "Team Builder"
        return "Hackathon Novice"

class Match(db.Model):
    __tablename__ = 'matches'
    
    id = db.Column(db.Integer, primary_key=True)
    user_one_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    user_two_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    status = db.Column(db.String(20), nullable=False)  # pending, connected, passed, super_liked
    action_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)  # user who swiped
    match_score = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Team(db.Model):
    __tablename__ = 'teams'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.Text, nullable=True)
    creator_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    members = db.relationship('TeamMember', backref='team', lazy=True, cascade="all, delete-orphan")
    projects = db.relationship('Project', backref='team', lazy=True, cascade="all, delete-orphan")

class TeamMember(db.Model):
    __tablename__ = 'team_members'
    
    id = db.Column(db.Integer, primary_key=True)
    team_id = db.Column(db.Integer, db.ForeignKey('teams.id', ondelete='CASCADE'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    role = db.Column(db.String(50), nullable=False, default='Frontend')  # Frontend, Backend, Design, AI, Security
    status = db.Column(db.String(25), nullable=False, default='active')  # active, invited, pending_approval
    joined_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    user = db.relationship('User', backref=db.backref('team_memberships', lazy=True))

class Message(db.Model):
    __tablename__ = 'messages'
    
    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    receiver_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=True)  # NULL for team messages
    team_id = db.Column(db.Integer, db.ForeignKey('teams.id', ondelete='CASCADE'), nullable=True)      # NULL for direct messages
    content = db.Column(db.Text, nullable=False)
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    sender = db.relationship('User', foreign_keys=[sender_id], backref='sent_messages')
    receiver = db.relationship('User', foreign_keys=[receiver_id], backref='received_messages')

class Project(db.Model):
    __tablename__ = 'projects'
    
    id = db.Column(db.Integer, primary_key=True)
    team_id = db.Column(db.Integer, db.ForeignKey('teams.id', ondelete='CASCADE'), nullable=True)
    creator_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    
    title = db.Column(db.String(150), nullable=False)
    theme = db.Column(db.String(100), nullable=False)
    difficulty = db.Column(db.String(50), nullable=False)
    
    problem_statement = db.Column(db.Text, nullable=False)
    target_audience = db.Column(db.Text, nullable=False)
    features = db.Column(db.Text, nullable=False)       # Stored as JSON or structured string
    tech_stack = db.Column(db.Text, nullable=False)     # Comma separated
    mvp_roadmap = db.Column(db.Text, nullable=False)    # Line breaks
    monetization = db.Column(db.Text, nullable=False)
    pitch_summary = db.Column(db.Text, nullable=False)
    demo_script = db.Column(db.Text, nullable=True)
    success_score = db.Column(db.Integer, default=50)   # Team Success Score (0-100)
    inspired_by = db.Column(db.Text, nullable=True)      # RAG: titles of retrieved past winning projects
    differentiation = db.Column(db.Text, nullable=True)  # RAG: how this idea differs from retrieved winners
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    creator = db.relationship('User', backref='created_projects')

class Hackathon(db.Model):
    __tablename__ = 'hackathons'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    start_date = db.Column(db.String(100), nullable=False)
    prize_pool = db.Column(db.String(100), nullable=False)
    category = db.Column(db.String(50), nullable=False)  # AI, Web Development, Cybersecurity, Open Source, Blockchain
    location = db.Column(db.String(150), nullable=False)
    link = db.Column(db.String(250), nullable=True)
    logo = db.Column(db.String(100), nullable=True)      # logo URL or font-awesome class

class Notification(db.Model):
    __tablename__ = 'notifications'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    title = db.Column(db.String(150), nullable=False)
    message = db.Column(db.Text, nullable=False)
    type = db.Column(db.String(50), nullable=False)      # match, invite, chat, project
    link = db.Column(db.String(200), nullable=True)
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Rating(db.Model):
    __tablename__ = 'ratings'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    activity_score = db.Column(db.Integer, default=0)    # Increments on actions
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
