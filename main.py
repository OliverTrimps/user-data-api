from flask import Flask, render_template, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin, login_user, LoginManager, login_required, current_user, logout_user
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv
from flask_cors import CORS, cross_origin


load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY')
CORS(app, supports_credentials=True)

database_user = os.getenv('DATABASE_USER')
database_password = os.getenv('DATABASE_PASSWORD')
database_host = os.getenv('DATABASE_HOST')
database_name = os.getenv('DATABASE_NAME')

postgresql_path = os.environ.get('DATABASE_URL', f'postgresql://{database_user}:{database_password}@{database_host}/{database_name}')
app.config['SQLALCHEMY_DATABASE_URI'] = postgresql_path
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

date = datetime.now()
# timer = timedelta(minutes=2)

login_manager = LoginManager()
login_manager.init_app(app)


@login_manager.user_loader
def load_user(user_id):
    return Users.query.get(int(user_id))


class Users(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    # first_name = db.Column(db.String(50), nullable=False)
    # last_name = db.Column(db.String(50), nullable=False)
    user_name = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(250), unique=True, nullable=False)
    password = db.Column(db.String(250), nullable=False)
    date_registered = db.Column(db.String(20), nullable=False)

    def to_dict(self):
        # dictionary = {}
        # for column in self.__table__.columns:
        #     dictionary[column.name] = getattr(self, column.name)
        return {column.name: getattr(self, column.name) for column in self.__table__.columns}


# with app.app_context():
#     db.create_all()


@app.route('/')
def home():
    return render_template('index.html')


@app.route("/register", methods=['POST'])
@cross_origin(origins='*', supports_credentials=True)
def register():
    email = request.json.get('email')
    # password = request.form.get('password')
    guest = Users.query.filter_by(email=email).first()

    if request.method == "POST":
        password = generate_password_hash(password=request.json.get('password'), method='pbkdf2:sha256', salt_length=8)
        # username = user.user_name , method='pbkdf2:sha256', salt_length=8
        if guest:
            return jsonify(response={"error": {"user exists": "an account with that email already exists!"}}), 401
        elif Users.query.filter_by(user_name=request.json.get('uname')).first():
            # Users.query.filter_by(user_name=request.form.get('uname')).first()
            return jsonify(response={"error": {"user exists": "username has been taken by another user!"}}), 401
        else:
            with app.app_context():
                new_user = Users(user_name=request.json.get('uname'),
                                 email=request.json.get('email'),
                                 password=password,
                                 date_registered=f"{date.month}/{date.day}/{date.year}",)
                db.session.add(new_user)
                db.session.commit()
    return jsonify(response={"success": "User Added!"}), 200


@app.route("/login", methods=["POST"])
@cross_origin(origins='*', supports_credentials=True)
def login():
    # user_name = request.form.get('fname')
    email = request.json.get('email')
    password = request.json.get('password')

    user_by_email = Users.query.filter_by(email=email).first()
    if request.method == "POST":
        if password is None:
            return jsonify(response={"error": {"No Data": "Password is a 'None' Value!"}}), 404
        if not user_by_email:
            return jsonify(response={"error": {"user not found": "email does not exist!"}}), 404
        elif not check_password_hash(user_by_email.password, password):
            return jsonify(response={"error": {"invalid credentials": "password is incorrect!"}}), 404
        else:
            login_user(user_by_email)
            logged_in = current_user.is_authenticated
    return jsonify(response={"success": "login successful!", "status": f"{logged_in}"}), 200


@app.route("/user", methods=["GET"])
def user():
    guests = db.session.query(Users).all()
    guest_in_session = current_user.user_name
    guests_username = {}
    for guest in guests:
        guests_username[f'user{guest.id}'] = guest.user_name
    return jsonify(response={'Users': f'{guests_username}', 'Current User': f'{guest_in_session}'})


@app.route("/access")
@login_required
def access_page():
    name = current_user.user_name
    if not name:
        logged_in = False
        return jsonify(response={"error": {"unauthorized": "login to access this page", "status": f"{logged_in}"}}), 403
    else:
        logged_in = current_user.is_authenticated
        return jsonify(response={"success": {f"{name}": "you have access to this page", "status": f"{logged_in}"}}), 200


@app.route("/logout")
def logout():
    logout_user()
    return jsonify(response={"success": "logout successful!"})


if __name__ == "__main__":
    app.run(debug=True)
