import time

from handlers import Handler


class LikeHandler(Handler):
    def get(self, url):
        self.fetch_post_and_id()
        if (self.user
           and self.post_id
           and self.user.username not in self.p.liked_by):
            self.p.likes += 1
            self.p.liked_by.append(self.user.username)
            self.p.put()
            time.sleep(0.5)
            self.redirect('/')
        else:
            self.redirect('/login')


class UnlikeHandler(Handler):
    def get(self, url):
        self.fetch_post_and_id()
        if (self.user
           and self.post_id
           and self.user.username in self.p.liked_by):
            self.p.likes -= 1
            self.p.liked_by.remove(self.user.username)
            self.p.put()
            time.sleep(0.5)
            self.redirect('/')
        else:
            self.redirect('/login')
