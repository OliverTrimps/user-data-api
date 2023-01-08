from flask import Flask, render_template, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin, login_user, LoginManager, login_required, current_user, logout_user
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv


load_dotenv()

app = Flask(__name__)
# app.config['SECRET_KEY'] = '8BYkEfBA6O6donzWlSihBXox7C0sKR6b'
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY')

database_user = os.getenv('DATABASE_USER')
database_password = os.getenv('DATABASE_PASSWORD')
database_host = os.getenv('DATABASE_HOST')
database_name = os.getenv('DATABASE_NAME')

# app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///accounts.db'
# app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:LoneWolf007@localhost:5432/accounts'
app.config['SQLALCHEMY_DATABASE_URI'] = f'postgresql://{database_user}:{database_password}@{database_host}/{database_name}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

date = datetime.now()
timer = timedelta(minutes=2)

login_manager = LoginManager()
login_manager.init_app(app)


@login_manager.user_loader
def load_user(user_id):
    return Users.query.get(int(user_id))


class Users(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
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
def register():
    email = request.form.get('email')
    password = request.form.get('password')
    print(email, password)
    user = Users.query.filter_by(email=email).first()
    # username = user.user_name
    if user:
        return jsonify(response={"error": {"user exists": "an account with that email already exists!"}}), 401
    elif Users.query.filter_by(user_name=request.form.get('uname')).first():
        # Users.query.filter_by(user_name=request.form.get('uname')).first()
        return jsonify(response={"error": {"user exists": "username has been taken by another user!"}}), 401
    else:
        hash_pass = generate_password_hash(password, method='pbkdf2:sha256', salt_length=8)
        with app.app_context():
            new_user = Users(first_name=request.form.get('fname'),
                             last_name=request.form.get('lname'),
                             user_name=request.form.get('uname'),
                             email=request.form.get('email'),
                             password=hash_pass,
                             date_registered=f"{date.month}/{date.day}/{date.year}",)
            db.session.add(new_user)
            db.session.commit()
    return jsonify(response={"success": "User Added!"}), 200


@app.route("/login", methods=["POST"])
def login():
    # user_name = request.form.get('fname')
    email = request.form.get('email')
    password = request.form.get('password')
    print(email, password)
    # users = db.session.query(Users).all()
    # for user in users:
    #     if user == "":
    #         return jsonify(response={"error": {"user not found": "No user found!"}}), 404
    user_by_email = Users.query.filter_by(email=email).first()
    # user_by_name = Users.query.filter_by(user_name=name).first()
    # print(user_by_email.user_name)
    if not user_by_email:
        return jsonify(response={"error": {"user not found": "email does not exist!"}}), 404
    # elif not user_by_name:
    #     return jsonify(response={"error": {"user not found": "username or email does not exist!"}}), 404
    elif not check_password_hash(user_by_email.password, password):
        return jsonify(response={"error": {"invalid credentials": "password is incorrect!"}}), 404
    else:
        # login_user(user_by_email)
        login_user(user_by_email, duration=timer)
        logged_in = current_user.is_authenticated
        return jsonify(response={"success": "login successful!", "status": f"{logged_in}"}), 200


@app.route("/access")
@login_required
def access_page():
    name = current_user.user_name
    # query_login_status = request.args.get("status")
    # print(name)
    if not name:
        logged_in = False
        return jsonify(response={"error": {"unauthorized": "login to access this page", "status": f"{logged_in}"}}), 403
    # elif query_login_status == "None":
    #     logged_in = False
    #     return jsonify(response={"error": {"unauthorized": "login to access this page"}}), 403
    else:
        logged_in = current_user.is_authenticated
        return jsonify(response={"success": {f"{name}": "you have access to this page", "status": f"{logged_in}"}}), 200


@app.route("/logout")
def logout():
    logout_user()
    return jsonify(response={"success": "logout successful!"})


if __name__ == "__main__":
    app.run(debug=True)
