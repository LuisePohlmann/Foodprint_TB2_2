from app.__init__ import db, create_app
from flask_login import LoginManager

if __name__ == "__main__":
    app = create_app()
    db.create_all(app=app)
    app.run(debug=True)
