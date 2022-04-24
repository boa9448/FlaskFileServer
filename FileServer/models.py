from FileServer import db


class User(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    username = db.Column(db.String(150), unique = True, nullable = False)
    password = db.Column(db.String(200), nullable = False)
    email = db.Column(db.String(120), unique = True, nullable = False)
    admin_permission = db.Column(db.Integer, nullable = False, default = 1)
    permission = db.Column(db.Integer, nullable = False)
    create_date = db.Column(db.DateTime(), nullable=False)


class File(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    filename = db.Column(db.String(200), nullable = False)
    hash = db.Column(db.String(200), nullable = False)
    size = db.Column(db.Integer, nullable = False)
    permission = db.Column(db.Integer, nullable = False)
    
