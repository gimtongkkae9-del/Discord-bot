import os
import subprocess
import sys

# 1. 메모리 절약을 위해 필수 라이브러리만 아주 천천히 설치
def install_requirements():
    # 고음질보다는 '실행'이 우선이므로 가장 가벼운 패키지만 구성
    libs = ["discord.py[voice]", "yt-dlp", "PyNaCl"]
    try:
        import discord
        import yt_dlp
    except ImportError:
        print("메모리 한계에 맞춰 필수 부품만 설치 중... (잠시만 대기)")
        # 메모리 튕김 방지를 위해 하나씩 설치 시도
        for lib in libs:
            subprocess.check_call([sys.executable, "-m", "pip", "install", lib])
        print("설치 완료! 서버를 다시 시작합니다.")
        os.execl(sys.executable, sys.executable, *sys.argv)

install_requirements()

import discord
from discord.ext import commands
import yt_dlp

# 2. 서버 부하를 줄이는 최소화 설정
YDL_OPTIONS = {
    'format': 'bestaudio/best',
    'noplaylist': True,
    'nocheckcertificate': True, # 보안 체크 생략으로 속도 향상
    'quiet': True,
    'no_warnings': True,
    'default_search': 'ytsearch',
}

FFMPEG_OPTIONS = {
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
    'options': '-vn'
}

intents = discord.Intents.default() # 메모리 절약을 위해 필요한 권한만 설정
intents.message_content = True

bot = commands.Bot(command_prefix='!', intents=intents)

@bot.event
async def on_ready():
    print(f'✅ 서버 한계 모드로 시작: {bot.user.name}')

@bot.command()
async def 재생(ctx, *, search):
    # 음성 채널 연결 확인
    if not ctx.author.voice:
        return await ctx.send("먼저 음성 채널에 들어가주세요.")
    
    if not ctx.voice_client:
        await ctx.author.voice.channel.connect()

    async with ctx.typing():
        with yt_dlp.YoutubeDL(YDL_OPTIONS) as ydl:
            info = ydl.extract_info(search, download=False)
            if 'entries' in info: # 검색어인 경우
                info = info['entries'][0]
            url = info['url']
            title = info['title']

        # 여기서 오류나면 서버에 ffmpeg가 아예 없는 것임
        try:
            source = await discord.FFmpegOpusAudio.from_probe(url, **FFMPEG_OPTIONS)
            ctx.voice_client.play(source)
            await ctx.send(f"🎵 **재생:** {title}")
        except Exception as e:
            await ctx.send("❌ 이 서버는 노래 재생 기능을 지원하지 않습니다 (ffmpeg 부재).")

# 3. 봇 토큰 입력
bot.run('MTQ2OTU4NjA3MjgzMTc5MTEwNA.Gy939i.j7p1OffcQa7dr7cPhvh-pSmjFsAy4bjbJIYxVo')
