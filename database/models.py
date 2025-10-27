from .base import db, login_manager
from datetime import datetime, timedelta, timezone
from sqlalchemy import Column, DateTime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
import uuid

# Asia/Shanghai timezone (UTC+8)
_local_tz = timezone(timedelta(hours=8))

def generate_uuid():
    return str(uuid.uuid4())

class TimestampMixin:
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(_local_tz), nullable=False)
    updated_at = Column(DateTime(timezone=True),
                        default=lambda: datetime.now(_local_tz),
                        onupdate=lambda: datetime.now(_local_tz),
                        nullable=False)


class User(db.Model, TimestampMixin, UserMixin):
    # 用户表
    __tablename__ = 'users'
    # 字段
    uid = db.Column(db.String(36), primary_key=True, default=generate_uuid)
    uname = db.Column(db.String(64), unique=True, nullable=False)
    uinfo = db.Column(db.Text, nullable=True)
    sid = db.Column(db.String(36), unique=True, nullable=False)
    email = db.Column(db.String(128), unique=True, nullable=False)
    passwd_hash = db.Column(db.String(128), nullable=False)
    uimg = db.Column(db.String(256), nullable=True)
    gid = db.Column(db.String(36), db.ForeignKey('groups.gid', ondelete='SET NULL'), nullable=True)
    role = db.Column(db.Integer, default=0)  # 0: 普通用户, 1: 管理员

    @property
    def is_admin(self):
        return self.role == 1
    
    @property
    def is_leader(self):
        return self.group.leader_id == self.uid if self.group else False

    def set_password(self, password):
        self.passwd_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.passwd_hash, password)

    def __repr__(self):
        return f"<User {self.uname} ({self.email})>"
    
    def get_id(self):
        return self.uid


class Group(db.Model, TimestampMixin):
    # 工作组表
    __tablename__ = 'groups'
    # 字段
    gid = db.Column(db.String(36), primary_key=True, default=generate_uuid)
    gname = db.Column(db.String(64), nullable=False)
    ginfo = db.Column(db.Text, nullable=True)
    gimg = db.Column(db.String(256), nullable=True)
    leader_id = db.Column(db.String(36), db.ForeignKey('users.uid'), nullable=False)
    users = db.relationship('User', backref='group', foreign_keys=[User.gid], lazy=True)
    projects = db.relationship(
        'Project',
        backref='group',
        cascade='all, delete-orphan',
        passive_deletes=True,
        lazy=True
    )

    def __repr__(self):
        users_list = ';'.join(user.uname for user in self.users)
        return f"<Group {self.gname} ({users_list})>"


class Project(db.Model, TimestampMixin):
    # 项目表
    __tablename__ = 'projects'
    # 字段
    pid = db.Column(db.String(36), primary_key=True, default=generate_uuid)
    pname = db.Column(db.String(100), nullable=False)
    pinfo = db.Column(db.Text, nullable=True)
    pimg = db.Column(db.String(256), nullable=True)
    gid = db.Column(db.String(36), db.ForeignKey('groups.gid', ondelete='CASCADE'), nullable=False)
    docker_id = db.Column(db.String(64), unique=True, default=generate_uuid)
    port = db.Column(db.Integer, unique=True, nullable=True)
    docker_port = db.Column(db.Integer, unique=True, nullable=True)

    def __repr__(self):
        return f"<Project {self.pname} ({self.port}:{self.docker_port})>"


# 用户加载回调函数(flask_login)    
@login_manager.user_loader
def load_user(user_id: str):
    return db.session.get(User, user_id)