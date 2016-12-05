from handler import Handler
from google.appengine.ext import db


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
