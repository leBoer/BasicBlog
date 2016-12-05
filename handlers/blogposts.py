import time

from handler import Handler
from models.blog import Blog


class NewContentPage(Handler):
    def get(self, post_id):
        post = Blog.get_by_id(int(post_id))
        self.render('permalink.html',
                    post=post,
                    post_id=int(post_id),
                    subject=post.subject,
                    content=post.content,
                    user=self.username)


class EditHandler(Handler):
    def get(self, url):
        self.fetch_post_and_id()
        if self.user.username == self.p.author:
            self.render('/newpost.html',
                        subject=self.p.subject,
                        content=self.p.content,
                        author=self.p.author,
                        post_id=self.post_id,
                        user=self.username)
        else:
            self.redirect('/')

    def post(self, url):
        self.fetch_post_and_id()
        self.p.subject = self.request.get('subject')
        self.p.content = self.request.get('content')
        self.p.put()
        self.render("permalink.html",
                    p=self.p,
                    post_id=self.post_id,
                    subject=self.p.subject,
                    content=self.p.content,
                    )


class DeleteHandler(Handler):
    def get(self, url):
        self.fetch_post_and_id()
        if self.user.username == self.p.author:
            self.p.delete()
    # Sleep for 0.5 seconds, giving the db time to update before redirecting
            time.sleep(0.5)
            self.redirect('/')
        else:
            self.redirect('/')
