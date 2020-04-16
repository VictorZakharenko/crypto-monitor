from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from hashlib import md5
from datetime import datetime
import jwt
from time import time
from app import db,login 
from flask import current_app
from app.search import add_to_index, remove_from_index, query_index


# class SearchableMixin(object):
#     @classmethod
#     def search(cls, expression, page, per_page):
#         ids, total = query_index(cls.__tablename__, expression, page, per_page)
#         if total == 0:
#             return cls.query.filter_by(id=0), 0
#         when = []
#         for i in range(len(ids)):
#             when.append((ids[i], i))
#         return cls.query.filter(cls.id.in_(ids)).order_by(
#             db.case(when, value=cls.id)), total

#     @classmethod
#     def before_commit(cls, session):
#         session._changes = {
#             'add': list(session.new),
#             'update': list(session.dirty),
#             'delete': list(session.deleted)
#         }

#     @classmethod
#     def after_commit(cls, session):
#         for obj in session._changes['add']:
#             if isinstance(obj, SearchableMixin):
#                 add_to_index(obj.__tablename__, obj)
#         for obj in session._changes['update']:
#             if isinstance(obj, SearchableMixin):
#                 add_to_index(obj.__tablename__, obj)
#         for obj in session._changes['delete']:
#             if isinstance(obj, SearchableMixin):
#                 remove_from_index(obj.__tablename__, obj)
#         session._changes = None

#     @classmethod
#     def reindex(cls):
#         for obj in cls.query:
#             add_to_index(cls.__tablename__, obj)

# db.event.listen(db.session, 'before_commit', SearchableMixin.before_commit)
# db.event.listen(db.session, 'after_commit', SearchableMixin.after_commit)


followers = db.Table('followers',
    db.Column('follower_id', db.Integer, db.ForeignKey('manager.id')),
    db.Column('followed_id', db.Integer, db.ForeignKey('manager.id'))
)


class Manager(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), index=True, unique=True)
    mname = db.Column(db.String(120), index=True)
    password_hash = db.Column(db.String(128))
    companies = db.relationship('Company', backref='manager', lazy='dynamic')

    followed = db.relationship(
        'Manager', secondary=followers,
        primaryjoin=(followers.c.follower_id == id),
        secondaryjoin=(followers.c.followed_id == id),
        backref=db.backref('followers', lazy='dynamic'), lazy='dynamic')


    about_me = db.Column(db.String(140))
    last_seen = db.Column(db.DateTime, default=datetime.utcnow)

    def followed_companies(self):
        followed = Company.query.join(
            followers, (followers.c.followed_id == Company.account_manager_id)).filter(
                followers.c.follower_id == self.id)
        own = Company.query.filter_by(account_manager_id=self.id)
        return followed.union(own)

    def follow(self, manager):
        if not self.is_following(manager):
            self.followed.append(manager)

    def unfollow(self, manager):
        if self.is_following(manager):
            self.followed.remove(manager)

    def is_following(self, manager):
        return self.followed.filter(
            followers.c.followed_id == manager.id).count() > 0

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def avatar(self, size):
        digest = md5(self.email.lower().encode('utf-8')).hexdigest()
        return 'https://www.gravatar.com/avatar/{}?d=identicon&s={}'.format(
            digest, size)

    def __repr__(self):
        return '<AccountManager {}>'.format(self.email)

    def get_reset_password_token(self, expires_in=600):
        return jwt.encode(
            {'reset_password': self.id, 'exp': time() + expires_in},
            current_app.config['SECRET_KEY'], algorithm='HS256').decode('utf-8')

    @staticmethod
    def verify_reset_password_token(token):
        try:
            id = jwt.decode(token, current_app.config['SECRET_KEY'],
                            algorithms=['HS256'])['reset_password']
        except:
            return
        return Manager.query.get(id)

@login.user_loader
def load_user(id):
    return Manager.query.get(int(id))

class Company(db.Model):
    __searchable__ = ['crypto']
    id = db.Column(db.Integer, primary_key=True)
    crypto = db.Column(db.String(120), index=True, unique=True)
    account_manager_id = db.Column(db.Integer, db.ForeignKey('manager.id'))
    customer_users = db.relationship('User', backref='company', lazy='dynamic')


    def delete_myself(self):

        for user in self.customer_users.all():
            user.delete_myself()
        db.session.delete(self)
        db.session.commit()

    def __repr__(self):
        return '<Company {}>'.format(self.crypto)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), index=True, unique=True)
    api_key = db.Column(db.String(120), index=True, unique=True)
    company_id = db.Column(db.Integer, db.ForeignKey('company.id'))

    def delete_myself(self):
        db.session.delete(self)
        db.session.commit()


    def __repr__(self):
        return '<User {}>'.format(self.email)
