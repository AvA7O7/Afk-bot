import subprocess
import sys
import discord
import asyncio
import signal
import os
from colorama import init, Fore

init(autoreset=True)

# تأكد من تثبيت المكتبات المطلوبة
required_libraries = ["discord", "colorama", "PyNaCl"]
def install_libraries():
    for lib in required_libraries:
        try:
            __import__(lib)
        except ImportError:
            subprocess.check_call([sys.executable, "-m", "pip", "install", lib])
install_libraries()

def print_banner():
    print(""" 
        █               █
       █ █             █ █
      █   █  █     █  █   █
      █████   █   █   █████
      █   █    █ █    █   █
      █   █     █     █   █
""" + Fore.RED + "\n                              Made by ! AvA | Support : dis.gg/9x\n")

# قراءة البيانات من الملف
def read_tokens_and_channels():
    data = {}
    if os.path.exists("voice.txt"):
        with open("voice.txt", "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                if "=" in line:
                    parts = line.split("=")
                    token = parts[0]
                    if ":" in parts[1]:
                        # ممكن يكون rom:activity أو activity بدون روم
                        channel_part, *activity_parts = parts[1].split(":", 1)
                        try:
                            cid = int(channel_part)
                            activity = activity_parts[0] if activity_parts else None
                            data[token] = (cid, activity)
                        except ValueError:
                            data[token] = (None, parts[1])
                    else:
                        try:
                            cid = int(parts[1])
                            data[token] = (cid, None)
                        except ValueError:
                            data[token] = (None, None)
                else:
                    data[line] = (None, None)
    return data

def save_tokens_and_channels(data):
    with open("voice.txt", "w", encoding="utf-8") as f:
        for tok, (cid, activity) in data.items():
            line = f"{tok}="
            if cid:
                line += f"{cid}"
            if activity:
                if cid:
                    line += f":{activity}"
                else:
                    line += f"{activity}"
            f.write(line + "\n")

def display_bot_info(user, channel_id):
    print(Fore.CYAN + "="*50)
    print(Fore.GREEN + f"[+] Bot: {user}")
    print(Fore.YELLOW + f"    Voice Channel ID: {channel_id}")
    print(Fore.CYAN + "="*50 + "\n")

async def run_bot(token, channels_data):
    intents = discord.Intents.default()
    intents.message_content = True
    client = discord.Client(intents=intents)

    async def ensure_voice():
        await client.wait_until_ready()
        while not client.is_closed():
            info = channels_data.get(token)
            if isinstance(info, tuple):
                cid = info[0]
                if cid:
                    guild = client.guilds[0] if client.guilds else None
                    if guild:
                        ch = guild.get_channel(cid)
                        if isinstance(ch, discord.VoiceChannel):
                            vc = discord.utils.get(client.voice_clients, guild=guild)
                            if not vc or not vc.is_connected():
                                try:
                                    await ch.connect(self_deaf=True)
                                    display_bot_info(client.user, cid)
                                except Exception:
                                    pass
            await asyncio.sleep(60)

    @client.event
    async def on_ready():
        info = channels_data.get(token)
        if isinstance(info, tuple) and len(info) == 2:
            activity_str = info[1]
            try:
                if activity_str:
                    parts = activity_str.split(":", 2)
                    atype = parts[0]
                    name = parts[1]
                    url = parts[2] if len(parts) == 3 else None

                    if atype == "playing":
                        act = discord.Game(name=name)
                    elif atype == "listening":
                        act = discord.Activity(type=discord.ActivityType.listening, name=name)
                    elif atype == "watching":
                        act = discord.Activity(type=discord.ActivityType.watching, name=name)
                    elif atype == "stream" and url:
                        act = discord.Streaming(name=name, url=url)
                    else:
                        act = None

                    if act:
                        await client.change_presence(activity=act)
            except Exception as e:
                print(Fore.RED + f"[-] Failed to load activity for {client.user}: {e}")
        client.loop.create_task(ensure_voice())

    @client.event
    async def on_message(message):
        if message.author.bot or not message.content.startswith("!"):
            return
        if client.user.mention not in message.content:
            return
        if not message.author.guild_permissions.administrator:
            return await message.reply("**❌ يجب أن تكون لديك صلاحيات المسؤول لاستخدام هذا الأمر.**")

        content = message.content.replace(client.user.mention, "").strip()
        parts = content.split()
        cmd = parts[0].lower()

        if cmd == "!setchannel":
            if len(parts) != 2 or not parts[1].isdigit():
                return await message.reply("**❌ استخدم: !setchannel <voice_channel_id**")
            cid = int(parts[1])
            _, activity = channels_data.get(token, (None, None))
            channels_data[token] = (cid, activity)
            save_tokens_and_channels(channels_data)
            return await message.reply(f"**✅ تم حفظ قناة الصوت ذات الـ ID {cid}.**")

        elif cmd == "!setname":
            if len(parts) < 2:
                return await message.reply("**❌ استخدم: !setname NewName**")
            new_name = " ".join(parts[1:])
            try:
                await client.user.edit(username=new_name)
                await message.reply(f"**✅ تم تغيير اسم البوت إلى {new_name}.**")
            except Exception as e:
                await message.reply(f"**❌ فشل تغيير الاسم: {e}**")

        elif cmd == "!setavatar":
            if not message.attachments:
                return await message.reply("**❌ قم بإرفاق صورة.**")
            try:
                data = await message.attachments[0].read()
                await client.user.edit(avatar=data)
                await message.reply("✅** تم تحديث الصورة بنجاح.**")
            except Exception as e:
                await message.reply(f"**❌ فشل تحديث الصورة: {e}**")

        elif cmd == "!setbanner":
            if not message.attachments:
                return await message.reply("**❌ قم بإرفاق صورة.**")
            try:
                data = await message.attachments[0].read()
                await client.user.edit(banner=data)
                await message.reply("**✅ تم تحديث البانر بنجاح.**")
            except Exception as e:
                await message.reply(f"**❌ فشل تحديث البانر: {e}**")

        elif cmd == "!setactivity":
            if len(parts) < 3:
                return await message.reply(
                    "**❌ استخدم: !setactivity playing | listening | watching | stream Name [URL]**"
                )
            atype = parts[1].lower()
            name = parts[2]
            url = parts[3] if atype == "stream" and len(parts) > 3 else None

            try:
                if atype == "playing":
                    act = discord.Game(name=name)
                elif atype == "listening":
                    act = discord.Activity(type=discord.ActivityType.listening, name=name)
                elif atype == "watching":
                    act = discord.Activity(type=discord.ActivityType.watching, name=name)
                elif atype == "stream" and url:
                    act = discord.Streaming(name=name, url=url)
                else:
                    return await message.reply("**❌ نوع النشاط غير صالح أو URL للبث مفقود.**")

                await client.change_presence(activity=act)

                cid, _ = channels_data.get(token, (None, None))
                activity = f"{atype}:{name}:{url}" if url else f"{atype}:{name}"
                channels_data[token] = (cid, activity)
                save_tokens_and_channels(channels_data)

                await message.reply(f"**✅ تم تغيير النشاط إلى: {atype} {name}{f' ({url})' if url else ''}.**")
            except Exception as e:
                await message.reply(f"**❌ فشل تغيير النشاط: {e}**")

        elif cmd == "!help":
            embed = discord.Embed(
                title=" أوامر التحكم في البوت",
                description=(
                    "**عند استعمال اي امر يجب عليك منشن البوت المراد التحكم به في الرسالة**\n\n"
                    "**!setchannel   تعيين قناة الصوت.**\n"
                    "**!setname  تغيير اسم البوت.**\n"
                    "**!setavatar  تغيير صورة البوت .**\n"
                    "**!setbanner  تغيير بنر البوت .**\n"
                    "**!setactivity  تغيير النشاط.**"
                ),
                color=discord.Color.from_str("#808080")
            )
            embed.set_footer(
                text=" Support: dis.gg/9x",
                icon_url=message.guild.icon.url if message.guild.icon else None
            )
            await message.reply(embed=embed)

    await client.start(token)

async def main():
    print_banner()
    channels_data = read_tokens_and_channels()
    tokens = list(channels_data.keys())
    while True:
        try:
            tasks = [run_bot(tok, channels_data) for tok in tokens]
            await asyncio.gather(*tasks)
        except Exception as e:
            print(Fore.RED + f"[-] Error: {e}")
            await asyncio.sleep(5)

def handle_exit(sig, frame):
    print(Fore.YELLOW + "\n[!] CTRL+C detected — restarting...\n")
    asyncio.create_task(main())

signal.signal(signal.SIGINT, handle_exit)

if __name__ == "__main__":
    asyncio.run(main())
