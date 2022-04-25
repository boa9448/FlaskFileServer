from FileServer import db


class User(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    username = db.Column(db.String(150), unique = True, nullable = False)
    password = db.Column(db.String(200), nullable = False)
    email = db.Column(db.String(120), unique = True, nullable = False)
    admin_permission = db.Column(db.Integer, nullable = False)
    permission = db.Column(db.Integer, nullable = False)
    create_date = db.Column(db.DateTime(), nullable = False)


class File(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    filename = db.Column(db.String(200), nullable = False)
    hash = db.Column(db.String(200), nullable = False)
    size = db.Column(db.Integer, nullable = False)
    permission = db.Column(db.Integer, nullable = False)
    

class UserLog(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    user_id = db.Column(db.Integer, nullable = False)
    level = db.Column(db.Integer, nullable = False)
    type = db.Column(db.Integer, nullable = False)
    message = db.Column(db.String(200), nullable = False)
    create_date = db.Column(db.DateTime(), nullable = False)


class FileAccessLog(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    user_id = db.Column(db.Integer, nullable = False)
    file_id = db.Column(db.Integer, nullable = False)
    file_name = db.Column(db.String(200), nullable = False)
    create_date = db.Column(db.DateTime(), nullable = False)


class FileAccessPermission(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id", ondelete="CASCADE"))
    user = db.relationship("User", backref = db.backref("file_access_permision_set"))
    file_id = db.Column(db.Integer, db.ForeignKey("file.id", ondelete="CASCADE"))
    file = db.relationship("File", backref = db.backref("file_set"))
    create_date = db.Column(db.DateTime(), nullable = False)