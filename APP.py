from flask import Flask, render_template
from flask_login import LoginManager
from flask_migrate import Migrate
from models import db, User
from user_routes import user_bp
from survey_routes import survey_bp
from contact_routes import contact_bp
from schedule_routes import schedule_bp

app = Flask(__name__)
app.secret_key = 'your-secret-key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize extensions
db.init_app(app)
login_manager = LoginManager(app)
login_manager.login_view = 'user.login'  # Updated to use blueprint route
migrate = Migrate(app, db)

# Register blueprints
app.register_blueprint(user_bp, url_prefix='')
app.register_blueprint(survey_bp, url_prefix='')
app.register_blueprint(contact_bp, url_prefix='')
app.register_blueprint(schedule_bp, url_prefix='')

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/')
def index():
    return render_template('index.html', title="Home", app_name="Conduct")

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
