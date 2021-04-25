import dotenv
import flask
import jinja2
import os
from sassutils.wsgi import SassMiddleware
from sqlalchemy.exc import IntegrityError

from models import *
from database import db
from routes import routes


dotenv.load_dotenv()
# Create the flask app
app = flask.Flask(__name__)
# Allow using pug for templating
app.jinja_loader = jinja2.FileSystemLoader("src/templates/pug")
app.jinja_env.add_extension("pypugjs.ext.jinja.PyPugJSExtension")
# Allow sass to be used instead of css
app.wsgi_app = SassMiddleware(app.wsgi_app, {
    'app': {'sass_path': 'static/sass',
            'css_path': 'static/css',
            'strip_extension': True,
            },
})

app.config["SQLALCHEMY_DATABASE_URI"] = "".join(f"""
postgresql+psycopg2://{os.getenv('POSTGRES_USER')}:{os.getenv('POSTGRES_PASSWORD')}
@{os.getenv('POSTGRES_HOST')}:{os.getenv('POSTGRES_PORT')}/{os.getenv('POSTGRES_DB')}
""".splitlines())
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Add the routes
app.register_blueprint(routes)

# Add the app to the database
with app.app_context():
    db.init_app(app)

    # Drop all tables for debugging
    # db.drop_all()
    # Make all tables
    db.create_all()

    try:
        user = User(encode(b"ai").decode(), datetime.datetime.utcnow(), "localhost")
        db.session.add(user)
        db.session.commit()
    except IntegrityError:
        db.session.rollback()

if __name__ == "__main__":
    app.run()
    db.session.close()
