import flask
from flask import request
import redis
import time
import json


from flask import redirect
from flask import render_template
from flask import session
from flask import url_for
from flask import abort
from functools import wraps

from models import *

def current_user():
    uid = session.get('user_id')
    if uid is not None:
        u = User.query.get(uid)
        return u
    else:
        return None

def admin_required(f):
    @wraps(f)
    def function(*args, **kwargs):
        u = current_user()
        if u == None:
            return render_template('index.html', user=u)

        return f(*args, **kwargs)

    return function


'''
# 使用 gunicorn 启动
gunicorn --worker-class=gevent -t 9999 redischat:app -b 0.0.0.0:8000
# 开启 debug 输出
gunicorn --log-level debug --worker-class=gevent -t 999 redis_chat81:app
# 把 gunicorn 输出写入到 gunicorn.log 文件中
gunicorn --log-level debug --access-logfile gunicorn.log --worker-class=gevent -t 999 redis_chat81:app
'''

# 连接上本机的 redis 服务器
# 所以要先打开 redis 服务器
red = redis.Redis(host='localhost', port=6379, db=0)
print('redis', red)

app = flask.Flask(__name__)
app.secret_key = 'pfsdfhloi'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True


# 发布聊天广播的 redis 频道
chat_channel = 'chat'



def stream():
    '''
    监听 redis 广播并 sse 到客户端
    '''
    # 对每一个用户 创建一个[发布订阅]对象
    pubsub = red.pubsub()
    # 订阅广播频道
    pubsub.subscribe(chat_channel)
    # 监听订阅的广播
    for message in pubsub.listen():
        print(message)
        if message['type'] == 'message':
            data = message['data'].decode('utf-8')
            # 用 sse 返回给前端
            yield 'data: {}\n\n'.format(data)


@app.route('/subscribe')
@admin_required
def subscribe():
    return flask.Response(stream(), 
        mimetype="text/event-stream")


@app.route('/chatroom/')
def index_view():
    u = current_user()
    return flask.render_template('index.html', user=u)


def current_time():
    return int(time.time())


@app.route('/chatroom/chat/add', methods=['POST'])
@admin_required
def chat_add():
    msg = request.get_json()
    user_id = msg.get('user_id', '')
    u = User.query.get(user_id)
    username = u.username
    avatar = u.avatar
    content = msg.get('content', '')
    channel = msg.get('channel', '')
    r = {
        'user': username,
        'avatar': avatar,
        'content': content,
        'channel': channel,
        'created_time': current_time(),
    }
    message = json.dumps(r, ensure_ascii=False)
    # 用 redis 发布消息
    m = Message(r)
    m.save()
    red.publish(chat_channel, message)

    return 'OK'


@app.route('/chatroom/login', methods=['POST'])
def login():
    form = request.form
    username = form.get('username','')
    user = User.query.filter_by(username=username).first()
    status, msg = user.validate_login(form)
    if status:
        session['user_id'] = user.id
        return render_template('index.html', message=msg, user=user)
    else:
        user = current_user()
        return render_template('index.html', message=msg, user=user)
#
@app.route('/chatroom/register', methods=['POST'])
def register():
    form = request.form
    uu = current_user()
    u = User(form)
    status, msgs = u.valid()
    if status:
        u.save()
        message = msgs[0]
        return render_template('index.html', message=message, user=uu)
    else:
        message = msgs[1]
        return render_template('index.html', message=message, user=uu)



if __name__ == '__main__':
    config = dict(
        host='0.0.0.0',
        debug=True,
        post=8000,
    )
    app.run(**config)
