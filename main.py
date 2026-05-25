from flask import Flask
from threading import Thread
import discord
from discord.ext import commands
import yt_dlp
import asyncio
import os

# 1. HỆ THỐNG KEEP ALIVE (GIỮ BOT ONLINE 24/7)
app = Flask('')

@app.route('/')
def home(): 
    return "Music Bot is online"

def run_flask(): 
    app.run(host='0.0.0.0', port=8080)

def keep_alive(): 
    Thread(target=run_flask).start()

# 2. CẤU HÌNH BOT VỚI CÁC BIẾN TỪ FILE .ENV
intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True

# Đọc Application ID từ file cấu hình của bro (nếu có)
APP_ID = os.getenv("APPLICATION_ID")

bot = commands.Bot(
    command_prefix="!", 
    intents=intents,
    application_id=int_app_id if (int_app_id := None or APP_ID is None) else int(APP_ID)
)

# 3. CẤU HÌNH GIẢI MÃ ÂM THANH CHỐNG LỖI FORMAT YOUTUBE
YTDL_OPTIONS = {
    'format': 'ba/b',
    'noplaylist': True,
    'default_search': 'ytsearch',
    'quiet': True,
    'extract_flat': False
}
FFMPEG_OPTIONS = {
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
    'options': '-vn'
}

ytdl = yt_dlp.YoutubeDL(YTDL_OPTIONS)

@bot.event
async def on_ready():
    print(f"Bot nhạc {bot.user} đã sẵn sàng hoạt động!")
    print(f"Application ID: {bot.application_id}")
    # Đồng bộ hóa các lệnh với hệ thống Discord
    try:
        synced = await bot.tree.sync()
        print(f"Đã đồng bộ {len(synced)} lệnh gạch chéo (Slash Commands)!")
    except Exception as e:
        print(f"Lỗi đồng bộ lệnh: {e}")

# 4. CÁC LỆNH ĐIỀU KHIỂN NHẠC (DÙNG TIỀN TỐ !)
@bot.command()
async def join(ctx):
    if not ctx.author.voice:
        await ctx.send("Bro phải vào một phòng Voice trước đã!")
        return
    channel = ctx.author.voice.channel
    if ctx.voice_client:
        await ctx.voice_client.move_to(channel)
    else:
        await channel.connect()
    await ctx.send(f"Đã vào phòng: **{channel.name}**")

@bot.command()
async def leave(ctx):
    if ctx.voice_client:
        await ctx.voice_client.disconnect()
        await ctx.send("Đã rời phòng thoại.")
    else:
        await ctx.send("Bot đang không ở trong phòng nào cả.")

@bot.command()
async def stop(ctx):
    if ctx.voice_client and ctx.voice_client.is_playing():
        ctx.voice_client.stop()
        await ctx.send("⏹️ Đã dừng phát nhạc.")
    else:
        await ctx.send("Hiện tại không có bài nào đang phát.")

@bot.command()
async def play(ctx, *, search: str):
    if not ctx.voice_client:
        if ctx.author.voice:
            await ctx.author.voice.channel.connect()
        else:
            await ctx.send("Bro phải vào phòng Voice trước!")
            return

    await ctx.send(f"🔍 Đang tìm kiếm: `{search}`... Chờ tí nhé bro.")

    loop = asyncio.get_event_loop()
    try:
        data = await loop.run_in_executor(None, lambda: ytdl.extract_info(search, download=False))
    except Exception as e:
        await ctx.send(f"❌ Lỗi tìm kiếm rồi bro ơi: {e}")
        return

    if 'entries' in data:
        video = data['entries'][0]
    else:
        video = data

    url = video['url']
    title = video['title']

    if ctx.voice_client.is_playing():
        ctx.voice_client.stop()

    try:
        source = discord.FFmpegPCMAudio(url, **FFMPEG_OPTIONS)
        ctx.voice_client.play(source)
        await ctx.send(f"🎶 **Đang phát:** {title}")
    except Exception as e:
        await ctx.send(f"❌ Lỗi khi stream nhạc: {e}")

# KÍCH HOẠT HỆ THỐNG ONLINE 24/7
keep_alive()

# CHẠY BOT BẰNG TOKEN TỪ FILE .ENV CỦA BRO
bot.run(os.getenv("DISCORD_TOKEN"))
