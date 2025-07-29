from telethon import TelegramClient
from telethon.tl import types
from telethon.extensions import markdown

def Golden(client: TelegramClient, emoji_map: dict) -> TelegramClient:
    def parse_text(text: str) -> tuple[str, list]:
        text, entities = markdown.parse(text)
        new_entities = []
        for entity in entities:
            if (isinstance(entity, types.MessageEntityTextUrl) and 
                entity.url.startswith('emoji/')):
                try:
                    document_id = int(entity.url.split('/')[1])
                    new_entities.append(
                        types.MessageEntityCustomEmoji(
                            offset=entity.offset,
                            length=entity.length,
                            document_id=document_id
                        )
                    )
                except (IndexError, ValueError):
                    new_entities.append(entity)
            else:
                new_entities.append(entity)
        return text, new_entities

    def unparse_text(text: str, entities: list) -> str:
        new_entities = []
        for entity in entities or []:
            if isinstance(entity, types.MessageEntityCustomEmoji):
                new_entities.append(
                    types.MessageEntityTextUrl(
                        offset=entity.offset,
                        length=entity.length,
                        url=f'emoji/{entity.document_id}'
                    )
                )
            else:
                new_entities.append(entity)
        return markdown.unparse(text, new_entities)

    class CustomParseMode:
        def __init__(self, parse, unparse):
            self.parse = parse
            self.unparse = unparse

    def format_text(text: str) -> str:
        for emoji, emoji_id in emoji_map.items():
            text = text.replace(emoji, f'[{emoji}](emoji/{emoji_id})')
        return text

    client.parse_mode = CustomParseMode(parse_text, unparse_text)
    client.format_with_custom_emojis = format_text

    original_send_message = client.send_message
    original_edit_message = client.edit_message

    def custom_send_message(entity, message, **kwargs):
        if isinstance(message, str):
            message = client.format_with_custom_emojis(message)
        return original_send_message(entity, message, **kwargs)

    def custom_edit_message(entity, message, text=None, **kwargs):
        if isinstance(text, str):
            text = client.format_with_custom_emojis(text)
        elif isinstance(message, str):
            message = client.format_with_custom_emojis(message)
            text = message
        return original_edit_message(entity, message, text=text, **kwargs)

    client.send_message = custom_send_message
    client.edit_message = custom_edit_message

    return client

def Emoji(message: types.Message) -> list[str]:
    if not message.entities:
        return []
    
    emoji_ids = []
    for entity in message.entities:
        if isinstance(entity, types.MessageEntityCustomEmoji):
            emoji_ids.append(str(entity.document_id))
    
    return emoji_ids