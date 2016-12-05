import webapp2
import jinja2
import os

from models.user import User
from models.blog import Blog
from models.comment import Comment

from functions import hasher

template_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'templates')
jinja_env = jinja2.Environment(loader=jinja2.FileSystemLoader(template_dir),
                               autoescape=True)


class Handler(webapp2.RequestHandler):
    def write(self, *a, **kw):
        self.response.out.write(*a, **kw)

    def render_str(self, template, **params):
        t = jinja_env.get_template(template)
        return t.render(params)

    def render(self, template, **kw):
        self.write(self.render_str(template, **kw))

    def set_secure_cookie(self, username, val):
        cookie_val = hasher.make_secure_val(val)
        self.response.headers.add_header(
            'Set-Cookie',
            '%s=%s; Path=/' % (username, cookie_val))

    def read_secure_cookie(self, username):
        cookie_val = self.request.cookies.get(username)
        return cookie_val and hasher.check_secure_val(cookie_val)

    def initialize(self, *a, **kw):
        webapp2.RequestHandler.initialize(self, *a, **kw)
        uid = self.read_secure_cookie('user_id')
        self.user = uid and User.by_id(int(uid))
        # Checks which user is logged in on each pageload
        if self.user:
            self.username = self.user.username
        else:
            self.username = None

    def login(self, user):
        self.set_secure_cookie('user_id', str(user.key().id()))

    def logout(self):
        self.response.headers.add_header('Set-Cookie', 'user_id=; Path=/')

    def fetch_post_and_id(self):
        # Helper function to shorten the code when dealing with posts
        url = self.request.path
        self.post_id = url.split('/')[2]
        self.p = Blog.get_by_id(int(self.post_id))

    def fetch_comment_and_id(self):
        # Helper function to shorten the code when dealing with comments
        url = self.request.path
        self.comment_id = url.split('/')[3]
        self.c = Comment.get_by_id(int(self.comment_id))
