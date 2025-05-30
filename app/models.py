from typing import Optional
from datetime import datetime, timezone
import sqlalchemy as sa
import sqlalchemy.orm as so
from app import db
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from app import login

class User(UserMixin, db.Model):
    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    username: so.Mapped[str] = so.mapped_column(sa.String(64), index=True,
                                                unique=True)
    email: so.Mapped[str] = so.mapped_column(sa.String(120), index=True,
                                            unique=True)
    password_hash: so.Mapped[Optional[str]] = so.mapped_column(sa.String(256))
    points: so.Mapped[int] = so.mapped_column(sa.Integer, default=0)

    posts: so.WriteOnlyMapped['Post'] = so.relationship(
        back_populates='author')
    assessments: so.WriteOnlyMapped['Assessment'] = so.relationship(
        back_populates='user')

    def __repr__(self):
        return '<User {}>'.format(self.username)
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)    
    
    @login.user_loader
    def load_user(id):
        return User.query.get(int(id))
        
class Post(db.Model):
    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    body: so.Mapped[str] = so.mapped_column(sa.String(140))
    timestamp: so.Mapped[datetime] = so.mapped_column(
        index=True, default=lambda: datetime.now(timezone.utc))
    user_id: so.Mapped[int] = so.mapped_column(sa.ForeignKey(User.id),
                                            index=True)

    author: so.Mapped[User] = so.relationship(back_populates='posts')

    def __repr__(self):
        return '<Post {}>'.format(self.body)

class Assessment(db.Model):
    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    user_id: so.Mapped[int] = so.mapped_column(sa.ForeignKey(User.id), nullable=False)
    score: so.Mapped[int] = so.mapped_column(sa.Integer, nullable=False)
    total_questions: so.Mapped[int] = so.mapped_column(sa.Integer, nullable=False)
    correct_answers: so.Mapped[int] = so.mapped_column(sa.Integer, nullable=False)
    wrong_answers: so.Mapped[int] = so.mapped_column(sa.Integer, nullable=False)
    timestamp: so.Mapped[datetime] = so.mapped_column(
        index=True, default=lambda: datetime.now(timezone.utc))
    questions: so.Mapped[Optional[dict]] = so.mapped_column(sa.JSON, nullable=False)
    answers: so.Mapped[Optional[dict]] = so.mapped_column(sa.JSON, nullable=False)

    user: so.Mapped[User] = so.relationship(back_populates='assessments')

    def __repr__(self):
        return f'<Assessment {self.id} - User {self.user_id} - Score {self.score}>'
