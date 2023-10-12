# NSDISCORDBOT

Checks delays and cancelled train rides

## Planned Features

- Bus Delays 

## Getting Started

### Prerequisites

- Python 3.8 or newer
- Discord account and a bot token

### Installation

1. Clone the repository:
    ```bash
    git clone https://github.com/VistaDiscord/NSDiscordBot.git
    cd NSDiscordBot
    ```

2. Install the required dependencies:
    - You'll need to install some pip plugins:
    ```bash
    pip install discord.py aiohttp asyncio datetime pytz
    ```

3. Change the following lines:
    ```python
    TOKEN = 'TOKEN'
    NS_API_KEY = your-NS-API-Key
    ```

4. Replace `'TOKEN'` with your Discord bot token and `NSAPI` with the APi Key of the NS.

### Usage

1. Run the bot:
    ```bash
    python run.py
    ```

2. The bot will start monitoring the API and send status updates to the specified Discord channel every 10 minutes.

## Support

If you encounter any issues or have feature suggestions, please open an issue on GitHub.

## Contributing

Feel free to fork the project, open a Pull Request, or submit issues and feature requests on GitHub.

## License

The project is free to use, and free to duplicate
