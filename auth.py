from flask_login import UserMixin, LoginManager
import json

# Carregar usuários
with open("users.json") as f:
    USERS = json.load(f)

class User(UserMixin):
    def __init__(self, id):
        self.id = id

def get_user(username):
    if username in USERS:
        return User(username)
    return None

def validate_login(username, password):
    return username in USERS and USERS[username]["password"] == password

def configure_login(app):
    login_manager = LoginManager()
    login_manager.login_view = "login"
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(user_id):
        return get_user(user_id)
