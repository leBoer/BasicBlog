import re

from handler import Handler
from models import User


class Signup(Handler):
    USER_RE = re.compile(r"^[a-zA-Z0-9_-]{3,20}$")
    PASSWORD_RE = re.compile(r"^.{3,20}$")
    EMAIL_RE = re.compile(r"^[\S]+@[\S]+.[\S]+$")

    def valid_username(self, username):
        return self.USER_RE.match(username)

    def valid_password(self, password):
        return self.PASSWORD_RE.match(password)

    def valid_email(self, email):
        if email:
            return self.EMAIL_RE.match(email)
        else:
            return True

    def valid_verify(self, password, verify):
        if password == verify:
            return True

    def get(self):
        self.render("signup.html",
                    user=self.username)

    def post(self):
        have_error = False
        self.username = self.request.get('username')
        self.password = self.request.get('password')
        self.verify = self.request.get('verify')
        self.email = self.request.get('email')

        params = dict(username=self.username,
                      email=self.email)

        if not self.valid_username(self.username):
            params['user_error'] = "That's not a valid username."
            have_error = True

        if not self.valid_password(self.password):
            params['password_error'] = "That wasn't a valid password."
            have_error = True
        elif self.password != self.verify:
            params['verify_error'] = "Your passwords didn't match."
            have_error = True

        if not self.valid_email(self.email):
            params['email_error'] = "That's not a valid email."
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
            self.render('signup.html', error=msg)
        else:
            u = User.register(self.username, self.password, self.email)
            u.put()

            self.login(u)
            self.redirect('/')
