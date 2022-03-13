from app.__init__ import db, create_app

app = create_app()
db.create_all(app=app)

if __name__ == "__main__":
    app.run()
