import time

from google.appengine.ext import db
from handler import Handler
from models import Comment


class CommentHandler(Handler):
    def render_comments(self, new_comment, heading):
        self.fetch_post_and_id()
        blogcomments = db.GqlQuery("SELECT * FROM Comment "
                                   "WHERE post_id = %s "
                                   "ORDER BY created DESC"
                                   % (int(self.post_id)))
        if self.user:
            username = self.user.username
        else:
            username = None
        self.render('comments.html',
                    subject=self.p.subject,
                    content=self.p.content,
                    new_comment=new_comment,
                    blogcomments=blogcomments,
                    post_id=self.post_id,
                    heading=heading,
                    count=self.p.number_of_comments,
                    user=username,)

    def get(self, url):
        self.render_comments(new_comment="",
                             heading="Make a new comment")

    def post(self, url):
        if self.user:
            self.fetch_post_and_id()
            comment = self.request.get('comment')
            self.p.number_of_comments += 1
            c = Comment(username=self.user.username,
                        comment=comment,
                        post_id=int(self.post_id))
            c.put()
            self.p.put()
            # Sleep for 0.5 seconds
            time.sleep(0.5)
            self.redirect('/comments/%s' % (self.post_id))
        else:
            self.redirect('/login')


class EditCommentHandler(CommentHandler):
    def get(self, url1, url2):
        self.fetch_comment_and_id()
        if self.user and self.username == self.c.username:
            self.render_comments(self.c.comment,
                                 heading="Edit your comment")
        else:
            self.redirect('/login')

    def post(self, url1, url2):
        self.fetch_comment_and_id()
        self.fetch_post_and_id()
        if self.user and self.username == self.c.username:
            comment = self.request.get('comment')
            self.c.comment = comment
            self.c.put()
            # Sleep for 0.5 seconds
            time.sleep(0.5)
            self.redirect('/comments/%s' % (self.post_id))
        else:
            self.redirect('/login')


class DeleteCommentHandler(CommentHandler):
    def get(self, url1, url2):
        self.fetch_comment_and_id()
        self.fetch_post_and_id()
        if self.username and self.user.username == self.c.username:
            self.c.delete()
            self.p.number_of_comments -= 1
            self.p.put()
            # Sleep for 0.5 seconds
            time.sleep(0.5)
            self.redirect('/comments/%s' % (self.post_id))
        else:
            self.redirect('/comments/%s' % (self.post_id))
