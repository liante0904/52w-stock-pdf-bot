import asyncio
from telegram import Bot
from telegram.constants import ParseMode
import time
import os

async def sendMarkDownText(token, chat_id, sendMessageText=None, file=None, title=None, is_markdown=False):
    MAX_LENGTH = 4096  # Telegram 최대 메시지 길이
    bot = Bot(token=token)
    
    if sendMessageText is None and file is None:
        raise ValueError("Either 'sendMessageText' or 'file' must be provided")

    async def send_chunk(message_chunk, part_info=""):
        final_message = f"**{title} {part_info}**\n\n" if title else ""
        final_message += message_chunk
        
        parse_mode = ParseMode.MARKDOWN if is_markdown else None
        await bot.send_message(chat_id=chat_id, text=final_message, disable_web_page_preview=True, parse_mode=parse_mode)
        await asyncio.sleep(2)

    # 리스트 형태의 메시지 처리
    if isinstance(sendMessageText, list):
        total_parts = len(sendMessageText)
        for idx, chunk in enumerate(sendMessageText):
            await send_chunk(chunk, part_info=f"(Part {idx + 1}/{total_parts})")

    # 단일 문자열 메시지 처리
    elif isinstance(sendMessageText, str):
        def split_message(text, max_length):
            lines = text.split('\n')
            chunks = []
            current_chunk = ""
            
            for line in lines:
                if len(current_chunk) + len(line) + 1 <= max_length:
                    current_chunk += line + '\n'
                else:
                    chunks.append(current_chunk.strip())
                    current_chunk = line + '\n'
            
            if current_chunk:
                chunks.append(current_chunk.strip())
            
            return chunks

        messages = split_message(sendMessageText, MAX_LENGTH - (len(title) + 20 if title else 0))
        total_parts = len(messages)
        for idx, message in enumerate(messages):
            await send_chunk(message, part_info=f"(Part {idx + 1}/{total_parts})")

    # 파일 처리
    if file:
        async def send_file(file_path):
            await bot.send_document(chat_id=chat_id, document=open(file_path, 'rb'))
            await asyncio.sleep(2)

        if isinstance(file, str):
            await send_file(file)
        elif isinstance(file, list):
            for f in file:
                if isinstance(f, str):
                    await send_file(f)
                elif isinstance(f, dict) and 'file' in f:
                    await send_file(f['file'])
