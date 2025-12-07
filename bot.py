import os
import discord
import requests
from discord.ext import tasks, commands
from datetime import datetime, timedelta

TOKEN = os.getenv("DISCORD_TOKEN")
CHANNEL_ID = int(os.getenv("CHANNEL_ID"))  # set in Railway

# Bulkington/Bedworth coordinates
LAT = 52.48
LON = -1.47

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

def get_tomorrow_morning_forecast():
    url = (
        f"https://api.open-meteo.com/v1/forecast?"
        f"latitude={LAT}&longitude={LON}"
        f"&hourly=temperature_2m,precipitation"
        f"&timezone=Europe/London"
    )
    data = requests.get(url).json()

    tomorrow = (datetime.now() + timedelta(days=1)).date()
    hours = data["hourly"]["time"]
    temps = data["hourly"]["temperature_2m"]
    rain = data["hourly"]["precipitation"]

    for time_str, temp, precip in zip(hours, temps, rain):
        dt = datetime.fromisoformat(time_str)
        if dt.date() == tomorrow and dt.hour == 7:  # 7 AM tomorrow
            return temp, precip
    return None, None

@tasks.loop(time=datetime.strptime("15:40", "%H:%M").time())  # run daily at 4 PM
async def check_weather():
    temp, precip = get_tomorrow_morning_forecast()
    print("Forecast:", temp, "°C,", precip, "mm rain")

    channel = await bot.fetch_channel(CHANNEL_ID)

    if temp is None:
        await channel.send("⚠️ Could not fetch tomorrow's forecast.")
        return

    if temp <= 3:
        if precip > 0:
            await channel.send(
                f"🌧️ Tomorrow 7 AM will be {temp}°C with rain. No cover needed!"
            )
        else:
            await channel.send(
                f"❄️ Tomorrow 7 AM will be {temp}°C and dry. Put a cover on your car!"
            )
    else:
        await channel.send(
            f"✅ Tomorrow 7 AM will be {temp}°C. No cover needed."
        )

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")
    check_weather.start()

bot.run(TOKEN)