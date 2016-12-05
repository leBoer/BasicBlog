from handler import Handler
from models import Blog


class BlogPage(Handler):
    def get(self):
        self.render('/newpost.html',
                    user=self.username)

    def post(self):
        subject = self.request.get('subject')
        content = self.request.get('content')
        # Checks if the user is signed in
        if self.user and subject and content:
            author = self.username
            a = Blog(subject=subject,
                     content=content,
                     author=author,
                     likes=0,
                     liked_by=[],
                     number_of_comments=0)
            a.put()
            self.redirect('/%s' % str(a.key().id()))
        elif not self.user:
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
