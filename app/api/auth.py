# -*- coding: UTF-8 -*-
from flask_httpauth import HTTPBasicAuth, HTTPTokenAuth
from flask import g
from app.models import db
from app.api.errors import error_response
from app.models.user import User


basic_auth = HTTPBasicAuth()
token_auth = HTTPTokenAuth()


@basic_auth.verify_password
def verify_password(username, password):
    '''用于检查用户提供的用户名和密码'''
    user = User.query.filter_by(username=username).first()
    if user is None:
        return False
    g.current_user = user
    return user.check_password(password)


@basic_auth.error_handler
def basic_auth_error():
    '''用于在认证失败的情况下返回错误响应'''
    return error_response(401, '登录异常')


@token_auth.verify_token
def verify_token(token):
    '''用于检查用户请求是否有token，并且token真实存在，还在有效期内'''
    payload = User.verify_jwt(token) if token else None
    g.user_id = payload['id']
    # if g.current_user:
        # 每次认证通过后（即将访问资源API），更新 last_seen 时间
        # g.current_user.ping()
        # db.session.commit()
    return g.user_id is not None


@token_auth.error_handler
def token_auth_error():
    '''用于在 Token Auth 认证失败的情况下返回错误响应'''
    return error_response(401)
