#!/usr/bin/python
# -*- coding: utf-8 -*-

import smtplib
import argparse
from sh import df
from sh import uname

parser = argparse.ArgumentParser()
parser.add_argument("--server", help="SMTP Server:Port",
                    default="smtp.gmail.com:587")
parser.add_argument("-F", "--From", help="Sender's email address",
                    required=True)
parser.add_argument("-T", "--To", help="Comma separated recipient's email list",
                    required=True)
parser.add_argument("-W", "--pswd", help="Email password", required=True)

args = parser.parse_args()
mail_info = {'server': args.server,
             'from': args.From,
             'login': args.From,
             'to': args.To.split(","),
             'pswd': args.pswd}


def send_mail(info):
    header = "From: %s\n" % info['from']
    header += "To: %s\n" % ",".join(info['to'])
    header += "Subject: %s\n\n" % info['subject']
    message = header + info['message']
    server = smtplib.SMTP(info['server'])
    server.starttls()
    server.login(info['login'], info['pswd'])
    problems = server.sendmail(info['from'], info['to'], message)
    server.quit()


def free_space():
    out_df = df(block_size="G")
    out_df = out_df.encode("utf-8", "replace")
    data = out_df.split(" ")
    while data.count("") > 0:
        data.remove("")
    for each in data:
        if "home" in each:
            id_free = data.index(each) - 2
    return int(data[id_free].split("G")[0])


def mail_body(info, space):
    name = str(uname(nodename=True)).split("\n")[0]
    if space <= 15:
        subject = "WARNING! "
        if space <= 10:
            subject = "RED ALERT! "
    subject += "Server %s out of space <no-reply>" % name
    body = "Server %s is running out of space. " % name
    body += "It has %sG free\n\n" % space
    body += str(df(block_size="G"))
    info.update({'subject': subject})
    info.update({'message': body})
    return info


if __name__=='__main__':
    mail_info = mail_body(mail_info, free_space())
    send_mail(mail_info)
