from datetime import datetime, timedelta
import unittest
from app import app, db
from app.models import Manager, 

from config import Config

class TestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite://'


class UserModelCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app(TestConfig)
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_password_hashing(self):
        m = Manager(email='test_manager@getresponse.com')
        m.set_password('cat')
        self.assertFalse(m.check_password('dog'))
        self.assertTrue(m.check_password('cat'))

    def test_avatar(self):
        m = Manager(email='john@example.com')
        self.assertEqual(m.avatar(128), ('https://www.gravatar.com/avatar/'
                                         'd4c74594d841139328695756648b6bd6'
                                         '?d=identicon&s=128'))

    def test_follow(self):
        m1 = Manager(email='test_manager@getresponse.com')
        m2 = Manager(email='test_manager1@getresponse.com')
        db.session.add(m1)
        db.session.add(m2)
        db.session.commit()
        self.assertEqual(m1.followed.all(), [])
        self.assertEqual(m1.followers.all(), [])

        m1.follow(m2)
        db.session.commit()
        self.assertTrue(m1.is_following(m2))
        self.assertEqual(m1.followed.count(), 1)
        self.assertEqual(m1.followed.first().email, 'test_manager1@getresponse.com')
        self.assertEqual(m2.followers.count(), 1)
        self.assertEqual(m2.followers.first().email, 'test_manager@getresponse.com')

        m1.unfollow(m2)
        db.session.commit()
        self.assertFalse(m1.is_following(m2))
        self.assertEqual(m1.followed.count(), 0)
        self.assertEqual(m2.followers.count(), 0)

    def test_follow_posts(self):
        # create four users
        m1 = Manager(email='est_manager1@getresponse.com')
        m2 = Manager(email='est_manager2@getresponse.com')
        m3 = Manager(email='est_manager3@getresponse.com')
        m4 = Manager(email='est_manager4@getresponse.com')
        db.session.add_all([m1, m2, m3, m4])

        # create four posts
        now = datetime.utcnow()
        p1 = Company(crypto="post from john", manager=m1)
        p2 = Company(crypto="post from susan", manager=m2)
        p3 = Company(crypto="post from mary", manager=m3)
        p4 = Company(crypto="post from david", manager=m4)
        db.session.add_all([p1, p2, p3, p4])
        db.session.commit()

        # setup the followers
        m1.follow(m2)  # 1 follows 2
        m1.follow(m4)  # 1 follows 4
        m2.follow(m3)  # 2 follows 3
        m3.follow(m4)  # 3 follows 4
        db.session.commit()

        # check the followed posts of each user
        f1 = set(m1.followed_companies().all())
        f2 = set(m2.followed_companies().all())
        f3 = set(m3.followed_companies().all())
        f4 = set(m4.followed_companies().all())
        self.assertEqual(f1, set([p2, p4, p1]))
        self.assertEqual(f2, set([p2, p3]))
        self.assertEqual(f3, set([p3, p4]))
        self.assertEqual(f4, set([p4]))

if __name__ == '__main__':
    unittest.main(verbosity=2)