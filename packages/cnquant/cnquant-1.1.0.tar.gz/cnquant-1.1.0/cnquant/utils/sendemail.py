import json
from email.mime.text import MIMEText
from email.header import Header
import smtplib

from cnquant.config.config_data_path import get_file_path_mail


"""
设置发件箱信息，这里使用的是QQ邮箱
{
  "MAIL_HOST": "smtp.qq.com",
  "MAIL_USER": "1111111@qq.com",
  "MAIL_PASSWORD": "邮箱里面的SMTP密码"
}
"""


def send_email(mail, title, content):
    with open(get_file_path_mail(), 'r') as f:
        data = json.load(f)

    # 第三方 SMTP 服务
    mail_host = data.get('MAIL_HOST')  # 设置服务器
    mail_user = data.get('MAIL_USER')  # 用户名
    mail_pass = data.get('MAIL_PASSWORD')  # 口令

    # 发件人，收件人
    sender = mail_user
    receivers = mail  # 接收邮件的邮箱，就是微信绑定的

    # 邮件内容
    message = MIMEText(content, 'plain', 'utf-8')
    message['From'] = Header(f'XiaoQi {sender}')
    message['To'] = Header(mail)

    # 邮件主题
    message['Subject'] = Header(title, 'utf-8')

    # 发送邮件
    try:
        smtpObj = smtplib.SMTP()
        smtpObj.connect(mail_host, 25)  # 25 为 SMTP 端口号
        smtpObj.login(mail_user, mail_pass)
        smtpObj.sendmail(sender, receivers, message.as_string())
        print("邮件发送成功")
    except smtplib.SMTPException:
        print("Error: 无法发送邮件")


# if __name__ == '__main__':
#     mail = "33688114@qq.com"
#     send_email(mail, title='测试的标题3', content='测试的内容。几句话。')
