import argparse
import datetime
import logging
import pprint
import requests
import sys
import time

import schedule
import yagmail
import yaml

from urllib.parse import quote, parse_qsl


def encode_params(**kwargs):
    string = "&"
    for k, v in kwargs.items():
        string += "&{}={}".format(quote(k, "UTF-8"), quote(str(v), "UTF-8"))

    return string[1:]


def report(pid, student_name, student_id, token, college, url="https://tjxsfw.chisai.tech/api/school_tjxsfw_student/yqfkLogDailyreport/v2"):
    now = datetime.datetime.now()
    now = now.strftime("%Y-%m-%d %H:%M:%S")
    headers = {
        "Host": "tjxsfw.chisai.tech",
        "Connection": "keep-alive",
        "Content-Length": "569",
        "Authorization": token,
        "User-Agent": "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/53.0.2785.143 Safari/537.36 MicroMessenger/7.0.9.501 NetType/WIFI MiniProgramEnv/Windows WindowsWechat",
        "content-type": "application/x-www-form-urlencoded",
        "Referer": "https://servicewechat.com/wx427cf6b5481c866a/32/page-frame.html",
        "Accept-Encoding": "gzip, deflate, br",
    }

    params = encode_params(
        studentPid=pid,
        studentName=student_name,
        studentStudentno=student_id,
        studentCollege=college,
        reportDatetime=now,
        locLat=31.37482,
        locLng=121.26621,
        locNation="中国",
        locProvince="上海市",
        locCity="上海市",
        locDistrict="嘉定区",
        locNation1="中国",
        locProvince1="上海市",
        locCity1="上海市",
    )
    res = requests.post(url, headers=headers, data=params)
    return params, res


def send_email(from_addr, to_addr, passwd, subject, text):
    _, host = from_addr.split("@", 1)
    yag = yagmail.SMTP(user=from_addr, password=passwd, host='smtp.{}'.format(host))
    yag.send(to=to_addr, subject=subject, contents=text)


def main(config, logger):
    logger.info("Start auto report for {}-{}".format(config["id"], config["name"]))
    params, res = report(
        config["pid"],
        config["name"],
        config["id"],
        config["token"],
        config["college"],
    )
    logger.info("HTTPS POST request has been sent. The raw parameter string is as followed: {}".format(params))
    logger.info("Decoded parameters are: \n{}".format(pprint.pformat(parse_qsl(params))))
    logger.info("Recieved response: {}".format(str(res.text)))
    if config["sender_email"] != "":
        send_email(
            config["sender_email"],
            config["reciever_email"],
            config["email_passwd"],
            subject="自动打卡 - {} - {}".format(config["name"], datetime.datetime.now().strftime("%Y.%m.%d")),
            text=str(res.text)
        )
        logger.info("Email from {} has been sent to {}".format(config["sender_email"], config["reciever_email"]))


def setup_logger(filename="log.txt"):
    logger = logging.getLogger("Logger")
    logger.setLevel(logging.INFO)
    ch = logging.StreamHandler(stream=sys.stdout)
    ch.setLevel(logging.INFO)
    ch.setFormatter(
        logging.Formatter(
            "\033[32m[%(asctime)s %(levelname)s]\033[0m %(message)s",
            datefmt="%y/%m/%d %H:%M:%S"
        )
    )
    logger.addHandler(ch)

    return logger


def get_config():
    parser = argparse.ArgumentParser(description="cvpack2 Training")
    parser.add_argument(
        "--yaml",
        required=True,
        type=str,
        help="path to the yaml config file"
    )
    args = parser.parse_args()
    return yaml.safe_load(open(args.yaml))


if __name__ == '__main__':
    config = get_config()
    logger = setup_logger()
    logger.info("\n" + pprint.pformat(config))
    schedule.every().day.at(config["time"]).do(main, config, logger)
    while True:
        schedule.run_pending()
        time.sleep(30)  # check every 30 seconds