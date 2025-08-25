from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from sqlalchemy import UniqueConstraint, CheckConstraint

db = SQLAlchemy()

class User(UserMixin, db.Model):
    """Represents a user of the platform."""
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    bio = db.Column(db.Text)

    # NEW: Profile picture field
    profile_pic = db.Column(
        db.String(255),
        default="default_profile.png"  # <-- make sure you place this in /static/uploads/ or /static/img/
    )

    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    # Skills this user offers
    offered = db.relationship(
        "UserSkill",
        primaryjoin="and_(User.id==UserSkill.user_id, UserSkill.relation=='offer')",
        cascade="all, delete-orphan",
        lazy="dynamic",
        overlaps="wanted,user"
    )

    # Skills this user wants
    wanted = db.relationship(
        "UserSkill",
        primaryjoin="and_(User.id==UserSkill.user_id, UserSkill.relation=='want')",
        cascade="all, delete-orphan",
        lazy="dynamic",
        overlaps="offered,user"
    )


class Skill(db.Model):
    """Represents a skill that can be offered or wanted."""
    __tablename__ = "skills"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False, index=True, unique=True)
    description = db.Column(db.Text)

    # Metadata for filtering
    category = db.Column(db.String(100), index=True)
    difficulty = db.Column(db.String(50), index=True)   # Beginner / Intermediate / Advanced
    location = db.Column(db.String(120), index=True)    # City, region, or online

    # Users connected to this skill
    users = db.relationship(
        "UserSkill",
        back_populates="skill",
        cascade="all, delete-orphan"
    )


class UserSkill(db.Model):
    """Associates a user with a skill, marking whether it's offered or wanted."""
    __tablename__ = "user_skill"

    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    skill_id = db.Column(db.Integer, db.ForeignKey("skills.id", ondelete="CASCADE"), primary_key=True)
    relation = db.Column(db.String(10), primary_key=True)  # 'offer' or 'want'

    user = db.relationship(
        "User",
        backref=db.backref("skills", lazy="dynamic", cascade="all, delete-orphan")
    )
    skill = db.relationship("Skill", back_populates="users")

    __table_args__ = (
        CheckConstraint("relation in ('offer','want')", name="ck_user_skill_relation"),
        UniqueConstraint("user_id", "skill_id", "relation", name="uq_user_skill"),
    )


class Swap(db.Model):
    """Represents a skill swap between two users."""
    __tablename__ = "swaps"

    id = db.Column(db.Integer, primary_key=True)
    requester_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    responder_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    offered_skill_id = db.Column(db.Integer, db.ForeignKey("skills.id"))
    wanted_skill_id = db.Column(db.Integer, db.ForeignKey("skills.id"))
    status = db.Column(db.String(20), default="pending", nullable=False)  # pending/accepted/declined/completed
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    requester = db.relationship("User", foreign_keys=[requester_id])
    responder = db.relationship("User", foreign_keys=[responder_id])
    offered_skill = db.relationship("Skill", foreign_keys=[offered_skill_id])
    wanted_skill = db.relationship("Skill", foreign_keys=[wanted_skill_id])


class Review(db.Model):
    """Represents a review left by a user after a swap."""
    __tablename__ = "reviews"

    id = db.Column(db.Integer, primary_key=True)
    swap_id = db.Column(db.Integer, db.ForeignKey("swaps.id", ondelete="CASCADE"), nullable=False)
    reviewer_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    rating = db.Column(db.Integer, nullable=False)  # 1–5 stars
    comment = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
