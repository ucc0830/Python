# -*- coding: utf-8 -*-
import requests

from bs4 import BeautifulSoup
from flask import Flask
from slack import WebClient
from slackeventsapi import SlackEventAdapter
from slack.web.classes.blocks import *

from selenium import webdriver

# driver = webdriver.Chrome('/Users/student/Downloads/chromedriver_win32/chromedriver')
driver = webdriver.PhantomJS('/Users/student/Downloads/phantomjs-2.1.1-windows/bin/phantomjs')
driver.implicitly_wait(1)

SLACK_TOKEN = 'xoxb-691503792807-678240180722-gAeNvg1tilsMyO6v8fykpPKQ'
SLACK_SIGNING_SECRET = 'e74e1b14ad853375974d11b80152ccb5'

app = Flask(__name__)
# /listening 으로 슬랙 이벤트를 받습니다.
slack_events_adaptor = SlackEventAdapter(SLACK_SIGNING_SECRET, "/listening", app)
slack_web_client = WebClient(token=SLACK_TOKEN)

# 크롤링 함수 구현하기
def search_KDA(text):
    id = text.split(' ')[1:]
    url = 'https://www.op.gg/summoner/userName=' + id[0]
    source_code = requests.get(url).text
    soup = BeautifulSoup(source_code, "html.parser")

    for parts in soup.find_all("div", class_="SummonerRatingMedium"):
        image = parts.find("img")
        RankType = parts.find("div", class_="RankType")
        TierRank = parts.find("div", class_="TierRank")
        TierInfo = parts.find("div", class_="TierInfo")

    block1 = ImageBlock(
        image_url=image.get('src'),
        alt_text="이미지 없음"
    )
    block2 = SectionBlock(text='랭크타입 : ' + RankType.get_text())
    block3 = SectionBlock(text='티어랭크 : ' + TierRank.get_text().replace('\n', ''))
    block4 = SectionBlock(text='리그포인트 : ' + TierInfo.get_text(strip=' ').replace('/', '    전적 : ').replace('LW', 'L    승률 : W').replace('Win Ratio ', ''))
    blocks = [block1, block2, block3, block4]

    return blocks

def rank(text):
    driver.get('https://www.op.gg/ranking/ladder/')
    html = driver.page_source
    soup = BeautifulSoup(html, "html.parser")

    champions = []
    numm=[]
    namee=[]
    tierr=[]

    for highest in soup.find_all("ul", class_="ranking-highest__list"):
        for num in highest.find_all("div", class_="ranking-highest__rank"):
            numm.append(num.get_text())
        for name in highest.find_all("a", class_="ranking-highest__name"):
            namee.append(name.get_text())
        for tierpoint in highest.find_all("div", class_="ranking-highest__tierrank"):
            tierr.append(tierpoint.get_text())

    print(namee)
    print(numm)
    print(tierr)
    for i in range(5):
        tmp = numm[i]+ ' 위 : ' + namee[i]+ ' ' + tierr[i]
        champions.append(tmp)

    return u'\n'.join(champions)

def most(line):
    driver.get('https://www.op.gg/champion/statistics')
    html = driver.page_source
    soup = BeautifulSoup(html, "html.parser")

    a_list = []
    for i in soup.find_all("tbody", class_="tabItem champion-trend-tier-" + line):
        for num, j in enumerate(i.find_all('div', class_='champion-index-table__name')):
            if num >= 10:
                break
            a_list.append(str(num + 1) + '위: ' + j.get_text().strip())

    return u'\n'.join(a_list)

# 챗봇이 멘션을 받았을 경우
@slack_events_adaptor.on("app_mention")
def app_mentioned(event_data):
    channel = event_data["event"]["channel"]
    text = event_data["event"]["text"]
    # 챗봇 시작명령을 받으면 문자열과 버튼 출력하게 함
    is_start = text.split(' ')[1:]
    print(is_start[0])

    if (is_start[0] == '시작'):
        slack_web_client.chat_postMessage(
            channel=channel,
            text='전적검색 => ID입력\n 대세 챔피언 검색 => 대세,(라인)\n랭킹 검색 => 랭킹\n'
        )
    elif (is_start[0] == '대세,탑'):
        line = 'TOP'
        most_str = most(line)
        slack_web_client.chat_postMessage(
            channel=channel,
            text=most_str)
    elif (is_start[0] == '대세,미드'):
        line = 'MID'
        most(line)
        most_str = most(line)
        slack_web_client.chat_postMessage(
            channel=channel,
            text=most_str)
    elif (is_start[0] == '대세,정글'):
        line = 'JUNGLE'
        most(line)
        most_str = most(line)
        slack_web_client.chat_postMessage(
            channel=channel,
            text=most_str)
    elif (is_start[0] == '대세,봇'):
        line = 'ADC'
        most(line)
        most_str = most(line)
        slack_web_client.chat_postMessage(
            channel=channel,
            text=most_str)
    elif (is_start[0] == '대세,서폿'):
        line = 'SUPPORT'
        most(line)
        most_str = most(line)
        slack_web_client.chat_postMessage(
            channel=channel,
            text=most_str)
    elif (is_start[0] == '랭킹'):
        keywords=rank(text)
        slack_web_client.chat_postMessage(
            channel=channel,
            text=keywords
        )
    # 전적검색기능
    else:
        my_blocks = search_KDA(text)
        slack_web_client.chat_postMessage(
            channel=channel,
            blocks=extract_json(my_blocks)
        )

# / 로 접속하면 서버가 준비되었다고 알려줍니다.
@app.route("/", methods=["GET"])
def index():
    return "<h1>Server is ready.</h1>"

if __name__ == '__main__':
    app.run('0.0.0.0', port=5000)