import smtplib
from email.message import EmailMessage
def sendmail(to,subject,body):
    server=smtplib.SMTP_SSL('smtp.gmail.com',465)
    server.login('lakshmikondiparthi.456@gmail.com','zxxq kfue cmlr gbow')
    msg=EmailMessage()
    msg['From']='lakshmikondiparthi.456@gmail.com'
    msg['Subject']=subject
    msg['To']=to
    msg.set_content(body)
    server.send_message(msg)
    server.quit()

