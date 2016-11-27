import os
import webapp2
import jinja2
import re
import hmac
import hashlib
import random
from string import letters

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
    return "%s|%s" % (s, hash_str(s))


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


class Blog(db.Model):
    subject = db.StringProperty(required=True)
    content = db.TextProperty(required=True)
    created = db.DateTimeProperty(auto_now_add=True)
    author = db.StringProperty(required=True)

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
    def login(cls, username):
        return username


class MainPage(Handler):
    def render_front(self, subject="", content="",
                     error="", created="", post_id=""):
        blogposts = db.GqlQuery("SELECT * FROM Blog "
                                "ORDER BY created DESC ")

        self.render("front.html", subject=subject, content=content,
                    error=error, created=created, blogposts=blogposts,
                    post_id=post_id)

    def get(self):
        self.render_front()


class BlogPage(Handler):
    def get(self):
        self.render('/newpost.html')

    def post(self):
        subject = self.request.get("subject")
        content = self.request.get("content")
        author_hash = self.request.cookies.get('username')
        # Checks if the user is signed in
        if check_secure_val(author_hash) and subject and content:
            author = author_hash.split('|')[0]
            a = Blog(subject=subject, content=content, author=author)
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
                        error=error)


class NewContentPage(Handler):
    def get(self, post_id):
        post = Blog.get_by_id(int(post_id))
        self.render('permalink.html',
                    post=post,
                    post_id=int(post_id),
                    subject=post.subject,
                    content=post.content)


class SignupPage(Handler):

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
        self.render('signup.html')

    def post(self):
        username = self.request.get("username")
        email = self.request.get("email")
        password = self.request.get("password")
        verify = self.request.get("verify")
        if (self.valid_username(username)
           and self.valid_email(email)
           and self.valid_password(password)
           and self.valid_verify(password, verify)):
                new_cookie_user = make_secure_val(str(username))
                self.response.headers.add_header('Set-Cookie',
                                                 'username=%s'
                                                 % new_cookie_user)
                u = User.by_name(username)
                if u:
                    msg = 'That user already exists.'
                    self.render('signup.html', user_error=msg)
                else:
                    u = User.register(username=username,
                                      password=password,
                                      email=email)
                    u.put()
                    self.redirect('/welcome')
        else:
            if not self.valid_username(username):
                user_error = "That's not a valid username"
            else:
                user_error = ""
            if not self.valid_password(password):
                password_error = "That's not a valid password"
            else:
                password_error = ""
            if email:
                if not self.valid_email(email):
                    email_error = "That's not a valid email"
            else:
                email_error = ""
            if not self.valid_verify(password, verify):
                verify_error = "Your passwords didn't match"
            else:
                verify_error = ""
            self.render("signup.html",
                        user_error=user_error,
                        password_error=password_error,
                        email_error=email_error,
                        verify_error=verify_error)


class WelcomePage(Handler):
    def get(self):
        username_hash = self.request.cookies.get('username')
        if check_secure_val(username_hash):
            username = username_hash.split('|')[0]
            self.render('welcome.html', username=username)
        else:
            self.redirect('/signup')


class LoginPage(Handler):
    def get(self):
        self.render('login.html')

    def post(self):
        username = self.request.get('username')
        password = self.request.get('password')
        u = User.by_name(username)
        if u:
            h = u.pw_hash
        if (not u or not valid_pw(username, password, h)):
                usermsg = 'Username or password wrong'
                self.render('login.html', usermsg=usermsg)
        else:
            new_cookie_user = make_secure_val(str(username))
            self.response.headers.add_header('Set-Cookie',
                                             'username=%s; Path=/'
                                             % (new_cookie_user))
            self.redirect('/welcome')


class LogoutHandler(Handler):
    def get(self):
        self.response.headers.add_header('Set-Cookie',
                                         'username=; Path=/')
        self.redirect('/signup')

app = webapp2.WSGIApplication([('/', MainPage),
                               ('/newpost', BlogPage),
                               ('/signup', SignupPage),
                               ('/welcome', WelcomePage),
                               ('/login', LoginPage),
                               ('/logout', LogoutHandler),
                               ('/([0-9]+)', NewContentPage)],
                              debug=True)
