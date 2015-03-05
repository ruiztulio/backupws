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
parser.add_argument("-P", "--partition", help="Partition to be evaluated",
                    required=True)
parser.add_argument("-L", "--limit", help="Minimal free space before alert (Gb)",
                    default=10)

args = parser.parse_args()
mail_info = {'server': args.server,
             'from': args.From,
             'login': args.From,
             'to': args.To.split(","),
             'pswd': args.pswd}
partition = args.partition
limit = int(args.limit)


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

def get_data():
    out_df = df(block_size="G")
    out_df = out_df.encode("utf-8", "replace")
    out_data = out_df.split(" ")
    while out_data.count("") > 0:
        out_data.remove("")
    return out_data


def free_space(data, partition):
    for each in data:
        if partition in each:
            id_free = data.index(each) + 3
    return int(data[id_free].split("G")[0])


def mail_body(info, limit, data, partition):
    space = free_space(data, partition)
    table = "\t".join(data)
    name = str(uname(nodename=True)).split("\n")[0]
    if space <= limit + 5:
        subject = "WARNING! "
        if space <= limit:
            subject = "RED ALERT! "
    subject += "Server %s out of space <no-reply>" % name
    body = "Server %s is running out of space " % name
    body += "in partition %s.\n\n" % partition
    body += "It has %sG of free space\n\nMore info:\n\n" % space
    body += table
    body += "\nThis is an automatic message. Do not Reply!\n\nVauxoo."
    info.update({'subject': subject})
    info.update({'message': body})
    return info


if __name__ == '__main__':
    data = get_data()
    if free_space(data, partition) <= limit + 5:
        mail_info = mail_body(mail_info, limit, data, partition)
        send_mail(mail_info)
