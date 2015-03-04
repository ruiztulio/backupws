#!/usr/bin/python
# -*- coding: utf-8 -*-

import smtplib
import argparse
from sh import df
from sh import uname

parser = argparse.ArgumentParser()
parser.add_argument("--server", help="SMTP Server",
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
             'pswd': args.pswd
}

def sendmail(info):
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


if __name__=='__main__':
    mail_info.update({'subject': "Prueba"})
    mail_info.update({'message': str(uname(nodename=True))})
    sendmail(mail_info)
