from flask import Flask
import os

def create_app():
    app = Flask(
        __name__,
        template_folder="../templates",
        static_folder="../static"
    )

    # ADD THIS LINE: This is required to encrypt user sessions (logins)
    app.secret_key = "super_secret_ninja_key_change_this_later"

    # Initialize the database when the app starts
    from .database import init_db
    init_db()

    # Register your routes
    from .routes import main
    app.register_blueprint(main)

    return app