import os
import webapp2
import jinja2
import re
import hmac
import hashlib
import random
from string import letters
import time

from google.appengine.ext import db

SECRET = 'thisissecret'

template_dir = os.path.join(os.path.dirname(__file__), 'templates')
jinja_env = jinja2.Environment(loader=jinja2.FileSystemLoader(template_dir),
                               autoescape=True)

USER_RE = re.compile(r"^[a-zA-Z0-9_-]{3,20}$")
PASSWORD_RE = re.compile(r"^.{3,20}$")
EMAIL_RE = re.compile(r"^[\S]+@[\S]+.[\S]+$")


def hash_str(s):
    return hmac.new(SECRET, s).hexdigest()


def make_secure_val(s):
    return "%s|%s" % (s, hmac.new(SECRET, s).hexdigest())


def check_secure_val(h):
    val = h.split('|')[0]
    if h == make_secure_val(val):
        return val


def render_str(template, **params):
    t = jinja_env.get_template(template)
    return t.render(params)


class Handler(webapp2.RequestHandler):
    def write(self, *a, **kw):
        self.response.out.write(*a, **kw)

    def render_str(self, template, **params):
        t = jinja_env.get_template(template)
        return t.render(params)

    def render(self, template, **kw):
        self.write(self.render_str(template, **kw))

    def set_secure_cookie(self, username, val):
        cookie_val = make_secure_val(val)
        self.response.headers.add_header(
            'Set-Cookie',
            '%s=%s; Path=/' % (username, cookie_val))

    def read_secure_cookie(self, username):
        cookie_val = self.request.cookies.get(username)
        return cookie_val and check_secure_val(cookie_val)

    def initialize(self, *a, **kw):
        webapp2.RequestHandler.initialize(self, *a, **kw)
        uid = self.read_secure_cookie('user_id')
        self.user = uid and User.by_id(int(uid))

        if self.user:
            self.username = self.user.username
        else:
            self.username = None

    def login(self, user):
        self.set_secure_cookie('user_id', str(user.key().id()))

    def logout(self):
        self.response.headers.add_header('Set-Cookie', 'user_id=; Path=/')

    def fetch_post_and_id(self):
        url = self.request.path
        self.post_id = url.split('/')[2]
        self.p = Blog.get_by_id(int(self.post_id))


class Blog(db.Model):
    subject = db.StringProperty(required=True)
    content = db.TextProperty(required=True)
    created = db.DateTimeProperty(auto_now_add=True)
    author = db.StringProperty(required=True)
    likes = db.IntegerProperty(required=True)
    liked_by = db.ListProperty(str)
    number_of_comments = db.IntegerProperty(required=True)

    def render(self):
        self._render_text = self.content.replace('\n', '<br>')
        return render_str("permalink.html", p=self)

# User section


def make_salt(length=5):
    return ''.join(random.choice(letters) for x in xrange(length))


def make_pw_hash(username, password, salt=None):
    if not salt:
        salt = make_salt()
    h = hashlib.sha256(username + password + salt).hexdigest()
    return '%s,%s' % (salt, h)


def valid_pw(username, password, h):
    salt = h.split(',')[0]
    return h == make_pw_hash(username, password, salt)


class User(db.Model):
    username = db.StringProperty(required=True)
    pw_hash = db.StringProperty(required=True)
    created = db.DateTimeProperty(auto_now_add=True)
    email = db.StringProperty()

    @classmethod
    def by_id(cls, uid):
        return User.get_by_id(uid)

    @classmethod
    def by_name(cls, username):
        u = User.all().filter('username =', username).get()
        return u

    @classmethod
    def register(cls, username, password, email=None):
        pw_hash = make_pw_hash(username, password)
        return User(username=username,
                    pw_hash=pw_hash,
                    email=email)

    @classmethod
    def login(cls, username, pw):
        u = cls.by_name(username)
        if u and valid_pw(username, pw, u.pw_hash):
            return u


class MainPage(Handler):
    def render_front(self, subject="", content="",
                     error="", created="", post_id=""):
        blogposts = db.GqlQuery("SELECT * FROM Blog "
                                "ORDER BY created DESC ")

        self.render("front.html", subject=subject, content=content,
                    error=error, created=created, blogposts=blogposts,
                    post_id=post_id, user=self.username)

    def get(self):
        self.render_front()


class BlogPage(Handler):
    def get(self):
        self.render('/newpost.html',
                    user=self.username)

    def post(self):
        subject = self.request.get('subject')
        content = self.request.get('content')
        author_hash = self.request.cookies.get('user_id')
        # Checks if the user is signed in
        if check_secure_val(author_hash) and subject and content:
            author = self.username
            a = Blog(subject=subject,
                     content=content,
                     author=author,
                     likes=0,
                     liked_by=[],
                     number_of_comments=0)
            a.put()
            self.redirect('/%s' % str(a.key().id()))
        elif not check_secure_val(author_hash):
            error = "You need to log in to post!"
            self.render("newpost.html",
                        error=error)
        else:
            error = "subject and content, please!"
            self.render("newpost.html",
                        subject=subject,
                        content=content,
                        error=error,
                        user=self.username)


class NewContentPage(Handler):
    def get(self, post_id):
        post = Blog.get_by_id(int(post_id))
        self.render('permalink.html',
                    post=post,
                    post_id=int(post_id),
                    subject=post.subject,
                    content=post.content,
                    user=self.username)


class Signup(Handler):
    def valid_username(self, username):
        return USER_RE.match(username)

    def valid_password(self, password):
        return PASSWORD_RE.match(password)

    def valid_email(self, email):
        if email:
            return EMAIL_RE.match(email)
        else:
            return True

    def valid_verify(self, password, verify):
        if password == verify:
            return True

    def get(self):
        self.render("signup.html")

    def post(self):
        have_error = False
        self.username = self.request.get('username')
        self.password = self.request.get('password')
        self.verify = self.request.get('verify')
        self.email = self.request.get('email')

        params = dict(username=self.username,
                      email=self.email)

        if not self.valid_username(self.username):
            params['error_username'] = "That's not a valid username."
            have_error = True

        if not self.valid_password(self.password):
            params['error_password'] = "That wasn't a valid password."
            have_error = True
        elif self.password != self.verify:
            params['error_verify'] = "Your passwords didn't match."
            have_error = True

        if not self.valid_email(self.email):
            params['error_email'] = "That's not a valid email."
            have_error = True

        if have_error:
            self.render('signup.html', **params)
        else:
            self.done()

    def done(self, *a, **kw):
        raise NotImplementedError


class Register(Signup):
    def done(self):
        # make sure the user doesn't already exist
        u = User.by_name(self.username)
        if u:
            msg = 'That user already exists.'
            self.render('signup.html', error_username=msg)
        else:
            u = User.register(self.username, self.password, self.email)
            u.put()

            self.login(u)
            self.redirect('/')


class LoginPage(Handler):
    def get(self):
        self.render('login.html')

    def post(self):
        username = self.request.get('username')
        password = self.request.get('password')

        u = User.login(username, password)
        if u:
            self.login(u)
            self.redirect('/')
        else:
            msg = 'Invalid login'
            self.render('login.html', error=msg)


class LogoutHandler(Handler):
    def get(self):
        self.logout()
        self.redirect('/')


class EditHandler(Handler):
    def get(self, url):
        self.fetch_post_and_id()
        if self.user.username == self.p.author:
            subject = self.p.subject
            content = self.p.content
            author = self.p.author
            self.render('/newpost.html',
                        subject=subject,
                        content=content,
                        author=author,
                        post_id=self.post_id,
                        user=self.username)
        else:
            self.redirect('/')

    def post(self, url):
        subject = self.request.get('subject')
        content = self.request.get('content')
        url = self.request.path
        post_id = url.split('/')[2]
        p = Blog.get_by_id(int(post_id))
        p.subject = subject
        p.content = content
        p.put()
        self.render("permalink.html",
                    p=p,
                    post_id=post_id,
                    subject=subject,
                    content=content,
                    )


class DeleteHandler(Handler):
    def get(self, url):
        self.fetch_post_and_id()
        if self.user.username == self.p.author:
            url = self.request.path
            post_id = url.split('/')[2]
            p = Blog.get_by_id(int(post_id))
            p.delete()
    # Sleep for 0.5 seconds, giving the db time to update before redirecting
            time.sleep(0.5)
            self.redirect('/')
        else:
            self.redirect('/')


class LikeHandler(Handler):
    def get(self, url):
        self.fetch_post_and_id()
        p = Blog.get_by_id(int(self.post_id))
        if (self.user.username
           and self.post_id
           and self.user.username not in p.liked_by):
            p.likes += 1
            p.liked_by.append(self.user.username)
            p.put()
            time.sleep(0.5)
            self.redirect('/')
        else:
            self.render('test.html',
                        error="something went wrong")


class UnlikeHandler(Handler):
    def get(self, url):
        self.fetch_post_and_id()
        p = Blog.get_by_id(int(self.post_id))
        if (self.user.username
           and self.post_id
           and self.user.username in p.liked_by):
            p.likes -= 1
            p.liked_by.remove(self.user.username)
            p.put()
            time.sleep(0.5)
            self.redirect('/')
        else:
            self.render('test.html',
                        error="something went wrong")


class Comment(db.Model):
    username = db.StringProperty(required=True)
    comment = db.TextProperty(required=True)
    created = db.DateTimeProperty(auto_now_add=True)
    post = db.ReferenceProperty(Blog, collection_name='comments')


class CommentHandler(Handler):
    def render_comments(self,
                        comment="",
                        created="",
                        post_id=""):
        blogcomments = db.GqlQuery("SELECT * FROM Comment "
                                   "ORDER BY created DESC ")
        self.fetch_post_and_id()
        self.render("comments.html",
                    subject=self.p.subject,
                    content=self.p.content,
                    comment=comment,
                    created=created,
                    blogcomments=blogcomments,
                    post_id=self.post_id,
                    user=self.username)

    def get(self, url):
        self.render_comments()

    def post(self, url):
        self.fetch_post_and_id()
        comment = self.request.get('comment')
        username = self.user.username
        post_id = self.post_id
        p = Blog.get_by_id(int(post_id))
        p.number_of_comments += 1
        c = Comment(username=username,
                    comment=comment,
                    post=p
                    )
        c.put()
        p.put()
        self.redirect('/comments/%s' % (post_id))

app = webapp2.WSGIApplication([('/*', MainPage),
                               ('/newpost', BlogPage),
                               ('/signup', Register),
                               ('/login', LoginPage),
                               ('/logout', LogoutHandler),
                               ('/edit/([0-9]+)', EditHandler),
                               ('/delete/([0-9]+)', DeleteHandler),
                               ('/like/([0-9]+)', LikeHandler),
                               ('/unlike/([0-9]+)', UnlikeHandler),
                               ('/comments/([0-9]+)', CommentHandler),
                               ('/([0-9]+)', NewContentPage)],
                              debug=True)
