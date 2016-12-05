import webapp2

from handlers import MainPage
from handlers import BlogPage
from handlers import Register
from handlers import LoginPage, LogoutHandler
from handlers import LikeHandler, UnlikeHandler
from handlers import CommentHandler, EditCommentHandler, DeleteCommentHandler
from handlers import NewContentPage, EditHandler, DeleteHandler


app = webapp2.WSGIApplication([
    ('/*', MainPage),
    ('/newpost', BlogPage),
    ('/signup', Register),
    ('/login', LoginPage),
    ('/logout', LogoutHandler),
    ('/edit/([0-9]+)', EditHandler),
    ('/delete/([0-9]+)', DeleteHandler),
    ('/like/([0-9]+)', LikeHandler),
    ('/unlike/([0-9]+)', UnlikeHandler),
    ('/comments/([0-9]+)', CommentHandler),
    ('/edit_comment/([0-9]+)/([0-9]+)', EditCommentHandler),
    ('/delete_comment/([0-9]+)/([0-9]+)', DeleteCommentHandler),
    ('/([0-9]+)', NewContentPage)],
    debug=True)
