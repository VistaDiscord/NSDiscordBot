import discord
import aiohttp
import asyncio
from datetime import datetime, timedelta
from discord import Embed
import pytz

# Your credentials
DISCORD_TOKEN = 'TOKEN'
NS_API_KEY = 'NSPRIMARYKEY'

intents = discord.Intents.default()
intents.typing = False
intents.presences = False
client = discord.Client(intents=intents)

station_names = {
    'MT': 'Maastricht',
    'MTR': 'Maastricht Randwyck',
    'STD': 'Sittard',
    'EHV': 'Eindhoven',
    'RM': 'Roermond',
}

async def fetch(url, session, headers):
    async with session.get(url, headers=headers) as response:
        return await response.json()

async def check_delays():
    # List of station codes to check
    stations = ['MT', 'MTR', 'STD', 'EHV', 'RM']  

    async with aiohttp.ClientSession() as session:
        while True:
            for station_code in stations:
                headers = {
                    'Ocp-Apim-Subscription-Key': NS_API_KEY,
                }

                # Check for disruptions
                disruption_data = await fetch(f'https://gateway.apiportal.ns.nl/reisinformatie-api/api/v3/disruptions/station/{station_code}', session, headers)

                # Check for departures
                departures_data = await fetch(f'https://gateway.apiportal.ns.nl/reisinformatie-api/api/v2/departures?station={station_code}', session, headers)

                delay_embeds = []

                # Get the current time in the Netherlands (Central European Time)
                now = datetime.now(pytz.timezone('Europe/Amsterdam'))

                for departure in departures_data.get('payload', {}).get('departures', []):
                    planned_time_str = departure.get('plannedDateTime', '')
                    actual_time_str = departure.get('actualDateTime', '')
                    planned_time = datetime.strptime(planned_time_str, "%Y-%m-%dT%H:%M:%S%z")
                    actual_time = datetime.strptime(actual_time_str, "%Y-%m-%dT%H:%M:%S%z")
                    time_difference = planned_time - now

                    is_cancelled = departure.get('cancelled', False)
                    is_delayed = planned_time != actual_time

                    if time_difference <= timedelta(minutes=60) and (is_delayed or is_cancelled):
                        planned_unix_timestamp = int((planned_time - datetime(1970, 1, 1, tzinfo=pytz.utc)).total_seconds())
                        actual_unix_timestamp = int((actual_time - datetime(1970, 1, 1, tzinfo=pytz.utc)).total_seconds())
                        status_text = "Geannuleerd" if is_cancelled else ("Vertraagd" if is_delayed else "Op tijd")
                        station_of_origin = station_names.get(station_code, 'Onbekend station')
                        title = f"Naar: {departure.get('direction', 'Onbekende richting')} - {departure.get('name', 'Onbekende naam')}"
                        description = f"Geplande Tijd: <t:{planned_unix_timestamp}:T>\nActuele Tijd: <t:{actual_unix_timestamp}:T>\nStatus: {status_text}\nStation van herkomst: {station_of_origin}"
                        embed_color = 0xff0000 if is_cancelled or is_delayed else 0x00ff00
                        embed = Embed(title=title, description=description, color=embed_color)
                        delay_embeds.append(embed)

                # If there are any delays or disruptions, send an embed to the specified Discord channel
                if delay_embeds:
                    channel = client.get_channel(1150686728403828807)  # Replace with your actual channel ID
                    if channel:
                        for embed in delay_embeds:
                            await channel.send(embed=embed)

            await asyncio.sleep(60 * 10)  # Check every 10 minutes

@client.event
async def on_ready():
    print(f'Ingelogd als {client.user}')
    client.loop.create_task(check_delays())

client.run(DISCORD_TOKEN)

