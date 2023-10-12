import discord
import aiohttp
import asyncio
from datetime import datetime, timedelta
from discord import Embed
import pytz
import pymongo

# Your credentials
DISCORD_TOKEN = 'TOKEN'
NS_API_KEY = 'NSPRIMARYKEY'
MONGO_URI = 'MONGODB_CONNECTION_URL'

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
    'BDE': 'Bunde',
    'MES': 'Meerssen',
    'LG': 'Landgraaf',
    'EDN': 'Eijsden'
}

client.db = pymongo.MongoClient(MONGO_URI).db

async def fetch(url, session, headers):
    async with session.get(url, headers=headers) as response:
        return await response.json()

async def check_delays():
    stations = ['MT', 'MTR', 'STD', 'EHV', 'RM', 'BDE', 'MES', 'LG', 'EDN']  

    async with aiohttp.ClientSession() as session:
        while True:
            next_check_time = datetime.now(pytz.timezone('Europe/Amsterdam')) + timedelta(minutes=5)  # Default to 5 minutes
            for station_code in stations:
                headers = {
                    'Ocp-Apim-Subscription-Key': NS_API_KEY,
                }

                disruption_data = await fetch(f'https://gateway.apiportal.ns.nl/reisinformatie-api/api/v3/disruptions/station/{station_code}', session, headers)
                departures_data = await fetch(f'https://gateway.apiportal.ns.nl/reisinformatie-api/api/v2/departures?station={station_code}', session, headers)

                now = datetime.now(pytz.timezone('Europe/Amsterdam'))

                all_departures = {}
                for departure in departures_data.get('payload', {}).get('departures', []):
                    name = departure.get('name', 'Onbekende naam')
                    if name in all_departures:
                        existing_time_str = all_departures[name].get('actualDateTime', '')
                        existing_time = datetime.strptime(existing_time_str, "%Y-%m-%dT%H:%M:%S%z")
                        new_time_str = departure.get('actualDateTime', '')
                        new_time = datetime.strptime(new_time_str, "%Y-%m-%dT%H:%M:%S%z")
                        if new_time < existing_time:
                            all_departures[name] = departure
                    else:
                        all_departures[name] = departure

                delay_embeds = {}
                for departure_name, departure in all_departures.items():
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
                        title = f"Naar: {departure.get('direction', 'Onbekende richting')} - {departure_name}"
                        description = f"Geplande Tijd: <t:{planned_unix_timestamp}:T>\nActuele Tijd: <t:{actual_unix_timestamp}:T>\nStatus: {status_text}\nStation van herkomst: {station_of_origin}"
                        embed_color = 0xff0000 if is_cancelled or is_delayed else 0x00ff00
                        embed = Embed(title=title, description=description, color=embed_color)
                        delay_embeds[departure_name] = embed

                    # Calculate the time at which this message should be deleted
                    deletion_time = actual_time + timedelta(minutes=2)
                    # Update next_check_time if this deletion_time is sooner
                    next_check_time = min(next_check_time, deletion_time)

                channel = client.get_channel(1150686728403828807)  # Replace with your actual channel ID
                if channel:
                    current_entries = client.db.entries.find({"station_code": station_code})
                    for entry in current_entries:
                        message_id = entry['message_id']
                        departure_id = entry['departure_id']
                        if departure_id not in delay_embeds:
                            message = await channel.fetch_message(message_id)
                            await message.delete()
                            client.db.entries.delete_one({"_id": entry['_id']})
                        else:
                            message = await channel.fetch_message(message_id)
                            await message.edit(embed=delay_embeds[departure_id])
                            del delay_embeds[departure_id]

                    for departure_id, embed in delay_embeds.items():
                        message = await channel.send(embed=embed)
                        client.db.entries.insert_one({
                            "station_code": station_code,
                            "departure_id": departure_id,
                            "message_id": message.id,
                            "actualDateTime": departures_data.get('actualDateTime', '')
                        })

            # Calculate the sleep interval as the difference between now and next_check_time
            sleep_interval = (next_check_time - datetime.now(pytz.timezone('Europe/Amsterdam'))).total_seconds()
            # Ensure sleep_interval is at least 1 second to prevent busy-waiting
            sleep_interval = max(sleep_interval, 1)
            
            await asyncio.sleep(sleep_interval)

@client.event
async def on_ready():
    print(f'Ingelogd als {client.user}')
    client.loop.create_task(check_delays())

client.run(DISCORD_TOKEN)
