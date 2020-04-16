from flask import render_template, current_app
from app.email import send_email
from flask import current_app


def send_password_reset_email(manager):
    token = manager.get_reset_password_token()
    send_email('[Crypto monitor] Reset Your Password',
               sender=current_app.config['ADMINS'][0],
               recipients=[manager.email],
               text_body=render_template('email/reset_password.txt',
                                         manager=manager, token=token),
               html_body=render_template('email/reset_password.html',
                                         manager=manager, token=token))