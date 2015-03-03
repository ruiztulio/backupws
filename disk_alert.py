#!/usr/bin/python
# -*- coding: utf-8 -*-

import smtplib


def sendmail(from_add, to_add, subject, message, login, psswd,
             smtpserver='smtp.gmail.com:587', cc_add=None):
    header = 'From: %s\n' % from_add
    header += 'To: %s\n' % ','.join(to_add)
    if cc_add:
        header += 'Cc: %s\n' % ','.join(cc_add)
    header += 'Subject: %s\n\n' % subject
    message = header + message
    server = smtplib.SMTP(smtpserver)
    server.starttls()
    server.login(login, psswd)
    problems = server.sendmail(from_add, to_add, message)
    server.quit()

sendmail(from_add='python@RC.net',
         to_add=['leonardo@vauxoo.com'],
         cc_add=['tulio@vauxoo.com'],
         subject='Prueba',
         message='Probando el enviador de mails',
         login='el_correo_@vauxoo.com',
         psswd='pswd')
