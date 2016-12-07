import hashlib
import os
from flask import session
from flask_sqlalchemy import SQLAlchemy
import time
from flask import Flask



app = Flask(__name__)
app.secret_key = 'qweqadasdafasrwqaerxcvzv'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True
# 指定数据库的路径
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///myapp.db'

db = SQLAlchemy(app)


class ModelMixin(object):
    def __repr__(self):
        class_name = self.__class__.__name__
        properties = ('{0} = {1}'.format(k, v) for k, v in self.__dict__.items())
        return '<{0}: \n  {1}\n>'.format(class_name, '\n  '.join(properties))

    def save(self):
        db.session.add(self)
        db.session.commit()

    def delete(self):
        db.session.delete(self)
        db.session.commit()


    def time(self):
        dt = int(time.time())
        return  dt


class User(db.Model, ModelMixin):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String())
    password = db.Column(db.String())
    avatar = db.Column(db.String())
    created_time = db.Column(db.Integer, default=0)
    captcha = db.Column(db.String())
    # 下面定义关系
    messages = db.relationship('Message', backref='user', foreign_keys='Message.user_id')


    def __init__(self, form):
        super(User, self).__init__()
        self.username = form.get('username', '')
        self.password = form.get('password', '')
        self.created_time = self.time()
        self.avatar = form.get('avatar', '/chatroom/static/img/1.jpg')
        self.captcha = form.get('captcha', '')
    # 验证注册用户的合法性的
    def valid(self):
        u = User.query.filter_by(username=self.username).first()
        valid_username = User.query.filter_by(username=self.username).first() == None
        valid_username_len = len(self.username) >= 4
        valid_password_len = len(self.password) >= 4
        valid_captcha = self.captcha == '吃瓜群众'
        msgs = ['注册成功，请登录']
        if not valid_username:
            message = '用户名已经存在'
            msgs.append(message)
        elif not valid_username_len:
            message = '用户名长度必须大于等于 4'
            msgs.append(message)
        elif not valid_password_len:
            message = '密码长度必须大于等于 4'
            msgs.append(message)
        elif not valid_captcha:
            message = '验证码必须输入 ‘吃瓜群众’'
            msgs.append(message)
        status = valid_username and valid_username_len and valid_password_len and valid_captcha
        return status, msgs

    # 验证用户登录
    def validate_login(self, form):
        username = form.get('username')
        password = form.get('password')
        username_equals = username == self.username
        password_equals = password == self.password
        if username_equals and password_equals:
            status = True
            msg = '登录成功'
        else:
            status = False
            msg = '用户名或密码错误'
        return status, msg


class Message(db.Model, ModelMixin):
    __tablename__ = 'Messages'
    # 下面是字段定义
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.String())
    created_time = db.Column(db.String(), default=0)
    # 外键
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))

    def __init__(self, form):

        self.content = form.get('content', '')
        self.created_time = self.time()
        self.channel = form.get('channel', '')


def db_build():
    db.drop_all()
    db.create_all()
    print('rebuild database')


if __name__ == '__main__':
    # 先 drop_all 删除所有数据库中的表
    # 再 create_all 创建所有的表
    db_build()