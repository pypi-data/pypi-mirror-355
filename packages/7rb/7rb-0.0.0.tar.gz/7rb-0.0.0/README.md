# 7rb Library

Advanced custom emoji handler for Telethon .

## Installation
```bash
pip install 7rb
```

## Usage

### Basic Setup
```python
import 7rb
from telethon import TelegramClient

client = TelegramClient('session', api_id, api_hash)
```

### Golden Method (Emoji Conversion)
```python
emoji_map = {
    '✨': '5280790529565536648',
    '💃🏻': '5280790529565536648'
}

7rb.Golden(client, emoji_map)
```

### Emoji Extraction
```python
@client.on(events.NewMessage)
async def handler(event):
    emoji_ids = 7rb.Emoji(event.message)
    if emoji_ids:
        print("Found custom emojis:", emoji_ids)
```

## Features
- Convert regular emojis to custom emojis
- Extract custom emoji IDs from messages
- Works with all Telethon send methods
- By : @YoGoLdEn .