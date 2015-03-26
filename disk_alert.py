#!/usr/bin/python
# -*- coding: utf-8 -*-

import smtplib
import argparse
import logging
from sh import df
from sh import uname

parser = argparse.ArgumentParser()
parser.add_argument("--server", help="SMTP Server:Port",
                    default="smtp.gmail.com:587")
parser.add_argument("-F", "--From", help="Sender's email address",
                    required=True)
parser.add_argument("-T", "--To",
                    help="Comma separated recipient's email list",
                    required=True)
parser.add_argument("-W", "--pswd", help="Email password", required=True)
parser.add_argument("-P", "--partition",
                    help=" Comma separated partitions to be evaluated",
                    required=True)
parser.add_argument("-L", "--limit",
                    help="Minimal free space before alert (Gb)",
                    default=10)
parser.add_argument("--log-level", help="Level of logger. INFO as default",
                    default="info")
parser.add_argument("--logfile", help="File where log will be saved",
                    default=None)

args = parser.parse_args()
level = getattr(logging, args.log_level.upper(), None)

logging.basicConfig(level=level,
                    filename=args.logfile,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('Space watch')

mail_info = {'server': args.server,
             'from': args.From,
             'to': args.To.split(","),
             'pswd': args.pswd}
partition = args.partition.split(",")
limit = int(args.limit)


def send_mail(info):
    header = "From: %s\n" % info['from']
    header += "To: %s\n" % ",".join(info['to'])
    header += "Subject: %s\n\n" % info['subject']
    message = header + info['message']
    server = smtplib.SMTP(info['server'])
    server.starttls()
    server.login(info['from'], info['pswd'])
    problems = server.sendmail(info['from'], info['to'], message)
    server.quit()


def get_data():
    logger.debug("Collecting data")
    out_df = df(block_size="G")
    out_df = out_df.encode("utf-8", "replace")
    out_data = out_df.split(" ")
    while out_data.count("") > 0:
        out_data.remove("")
    logger.debug("Data collected")
    return out_data


def free_space(data, partition):
    for each in data:
        if partition in each:
            id_free = data.index(each) + 3
    return int(data[id_free].split("G")[0])


def mail_body(info, limit, data, partition):
    table = "\t".join(data)
    name = str(uname(nodename=True)).split("\n")[0]
    logger.info("Evaluating free space")
    space = []
    for each in partition:
        space.append(free_space(data, each))
    if min(space) <= limit + 5:
        logger.info("Partitions under limit space found. Writing mail")
        subject = "WARNING! "
        if min(space) <= limit:
            subject = "RED ALERT! "
        subject += "Server %s out of space <no-reply>" % name
        body = "Server %s is running out of space.\n\n" % name
        for each in partition:
            if space[partition.index(each)] <= limit + 5:
                logger.debug("Partition %s under limit space", each)
                body += "In partition %s: " % each
                body += "%sG of free space\n" % space[partition.index(each)]
        body += "\nMore info:\n\n"
        body += table
        body += "\nThis is an automatic message. Do not Reply!\n\nVauxoo."
        info.update({'subject': subject})
        info.update({'message': body})
        logger.debug("Sending mail")
        try:
            send_mail(info)
            logger.info("Mail sent to %s", ",".join(info['to']))
        except Exception as e:
            logger.error(e)
    else:
        logger.info("No partitions found under limit space")


if __name__ == '__main__':
    logger.debug("Excecuting Free Space Alert script")
    data = get_data()
    mail_body(mail_info, limit, data, partition)
