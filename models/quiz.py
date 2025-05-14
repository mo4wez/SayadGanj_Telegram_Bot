from peewee import *
from models.base import BaseModel
from models.users import User
import json
import datetime

class Quiz(BaseModel):
    """Model for storing quiz information"""
    title = CharField()
    description = TextField(null=True)
    created_at = DateTimeField(default=datetime.datetime.now)
    scheduled_for = DateTimeField(null=True)
    duration_minutes = IntegerField(default=10)
    is_active = BooleanField(default=False)
    is_completed = BooleanField(default=False)
    questions = TextField()  # Stored as JSON
    
    def get_questions(self):
        """Parse and return the questions as a list of dictionaries"""
        return json.loads(self.questions)
    
    def set_questions(self, questions_list):
        """Convert questions list to JSON and store it"""
        self.questions = json.dumps(questions_list)
        
    def get_participant_count(self):
        """Get the number of participants in this quiz"""
        return QuizParticipant.select().where(QuizParticipant.quiz == self).count()
    
    def get_top_scores(self, limit=10):
        """Get the top scores for this quiz"""
        return (QuizParticipant
                .select(QuizParticipant, User)
                .join(User)
                .where(QuizParticipant.quiz == self)
                .order_by(QuizParticipant.score.desc())
                .limit(limit))

class QuizParticipant(BaseModel):
    """Model for tracking quiz participants and their scores"""
    quiz = ForeignKeyField(Quiz, backref='participants')
    user = ForeignKeyField(User, backref='quiz_participations')
    score = IntegerField(default=0)
    completed = BooleanField(default=False)
    started_at = DateTimeField(default=datetime.datetime.now)
    completed_at = DateTimeField(null=True)
    answers = TextField(null=True)  # Stored as JSON
    
    def get_answers(self):
        """Parse and return the user's answers"""
        if not self.answers:
            return []
        return json.loads(self.answers)
    
    def set_answers(self, answers_list):
        """Convert answers list to JSON and store it"""
        self.answers = json.dumps(answers_list)
    
    def calculate_score(self, quiz_questions):
        """Calculate the user's score based on their answers"""
        answers = self.get_answers()
        score = 0
        
        for i, question in enumerate(quiz_questions):
            if i < len(answers) and answers[i] == question['correct_answer']:
                score += 1
                
        self.score = score
        return score

class QuizLeaderboard(BaseModel):
    """Model for storing overall quiz leaderboard"""
    user = ForeignKeyField(User, backref='leaderboard_entries', unique=True)
    total_score = IntegerField(default=0)
    quizzes_participated = IntegerField(default=0)
    quizzes_won = IntegerField(default=0)
    last_updated = DateTimeField(default=datetime.datetime.now)
    
    @classmethod
    def update_for_user(cls, user, score_change=0, participated=False, won=False):
        """Update the leaderboard entry for a user"""
        leaderboard, created = cls.get_or_create(user=user)
        
        if score_change:
            leaderboard.total_score += score_change
            
        if participated:
            leaderboard.quizzes_participated += 1
            
        if won:
            leaderboard.quizzes_won += 1
            
        leaderboard.last_updated = datetime.datetime.now()
        leaderboard.save()
        
        return leaderboard
    
    @classmethod
    def get_top_users(cls, limit=10):
        """Get the top users on the leaderboard"""
        return (cls
                .select(cls, User)
                .join(User)
                .order_by(cls.total_score.desc())
                .limit(limit))

def create_tables():
    """Create all the tables for quiz functionality"""
    with BaseModel._meta.database:
        BaseModel._meta.database.create_tables([Quiz, QuizParticipant, QuizLeaderboard])