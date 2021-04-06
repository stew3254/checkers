import flask
import jinja2
import sqlalchemy as sqla
from sqlalchemy.orm import sessionmaker, scoped_session
from sassutils.wsgi import SassMiddleware
from models import *

# Create the flask app
app = flask.Flask(__name__)
# Allow using pug for templating
app.jinja_loader = jinja2.FileSystemLoader("templates/pug")
app.jinja_env.add_extension("pypugjs.ext.jinja.PyPugJSExtension")
# Allow sass to be used instead of css
app.wsgi_app = SassMiddleware(app.wsgi_app, {
    'app': {'sass_path': 'static/sass',
            'css_path': 'static/css',
            'strip_extension': True,
            },
})
engine = sqla.create_engine("sqlite://checkers.db")
conn = engine.connect()
Base.metadata.create_all(engine)
session = scoped_session(sessionmaker(bind=engine, autoflush=False, autocommit=False))()


@app.route("/", methods=["GET"])
def index():
    return flask.render_template("index.pug")


@app.route("/play", methods=["GET", "POST"])
def play():
    if flask.request.method == "GET":
        return flask.render_template("checkers.pug", letters="abcdefgh", str=str)
    else:
        return flask.request.form


if __name__ == "__main__":
    app.run()
    session.close()
