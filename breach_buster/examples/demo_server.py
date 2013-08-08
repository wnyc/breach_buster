import web
from StringIO import StringIO
from gzip import GzipFile
from breach_buster.middleware.gzip import compress_string


class breachable:
    def GET(self):
        web.header('content-encoding','gzip')
        out = StringIO()
        f = GzipFile(fileobj=out, mode='w', compresslevel=6)
        name = web.input(name='').name
        f.write(SITE % name)
        f.flush()
        return out.getvalue()

class correct_horse_battery_staple:
    def GET(self):
        web.header('content-encoding','gzip')
        out = StringIO()
        f = GzipFile(fileobj=out, mode='w', compresslevel=6)
        name = web.input(name='').name
        name = name.replace('+', ' ')
        f.write((SITE % name).replace('f675d2395f243c89', 'correct_horse_battery_staple'))
        f.flush()
        return out.getvalue()


class unbreachable:
    def GET(self):
        web.header('content-encoding','gzip')
        name = web.input(name='').name
        return compress_string(SITE % name)
    
urls = ('/good', 'unbreachable', '/bad', 'breachable', '/chbs', 'correct_horse_battery_staple')

def main():
    app = web.application(urls, globals())
    app.internalerror = web.debugerror
    app.run()




STORY = """<p>In the olden time, when wishing was having, there lived a King, whose daughters were all beautiful; but the youngest was so exceedingly beautiful that the Sun himself, although he saw her very often, was enchanted every time she came out into the sunshine.</p>

<p>Near the castle of this King was a large and gloomy forest, and in the midst stood an old lime-tree, beneath whose branches splashed a little fountain; so, whenever it was very hot, the King's youngest daughter ran off into this wood, and sat down by the side of this fountain; and, when she felt dull, would often divert herself by throwing a golden ball up in the air and catching it. And this was her favourite amusement.</p>

<a href="do_something?CSRF=f675d2395f243c89">If you liked this story do something nice for the author</a>


<p>Now, one day it happened, that this golden ball, when the King's daughter threw it into the air, did not fall down into her hand, but on the grass; and then it rolled past her into the fountain. The King's daughter followed the ball with her eyes, but it disappeared beneath the water, which was so deep that no one could see to the bottom. Then she began to lament, and to cry louder and louder; and, as she cried, a voice called out, "Why weepest thou, O King's daughter? thy tears would melt even a stone to pity." And she looked around to the spot whence the voice came, and saw a Frog stretching his thick ugly head out of the water. "Ah! you old water-paddler," said she, "was it you that spoke? I am weeping for my golden ball, which has slipped away from me into the water."</p>

"""
           


SITE = "<html><body><h1>Frog prince</h1><h2>Hello %%s</h2></p><hr/>%s</h></body></html>" % STORY
