import os
from telegram import Update, Bot, Message
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, filters, CommandHandler
import httpx
from datetime import datetime
import requests
import json
from importlib.resources import files
import re
from pathlib import Path
import asyncio
import telegramify_markdown
from telegram import InputMediaPhoto

class NexiraBot:
    def __init__(self, bot_token: str, api_url: str, db_url: str = ''):
        self.api_url = api_url
        self.db_url = db_url
        self.application = ApplicationBuilder().token(bot_token).build()
        self.application.add_handler(CommandHandler("new_chat", self.new_chat))
        self.application.add_handler(CommandHandler("clear_chat", self.clear_chat))
        self.application.add_handler(CommandHandler("mini_mavia_chatbot", self.mini_mavia_chatbot))
        self.application.add_handler(CommandHandler("block_clans_chatbot", self.block_clans_chatbot))
        self.application.add_handler(CommandHandler("standard_chatbot", self.standard_chatbot))
        self.application.add_handler(CommandHandler("list_all_agents", self.list_all_agents))
        self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))
        self.application.add_handler(MessageHandler(filters.Document.ALL, self.handle_document_upload))
        self.application.add_handler(MessageHandler(filters.PHOTO, self.handle_photo_upload))
        self.application.add_handler(MessageHandler(filters.AUDIO | filters.VOICE, self.handle_audio_upload))
        self.chatbot_agent = 'standard_agent'
        self.http_client = httpx.AsyncClient(timeout=20.0)

    def convert_message_obj(self, message_obj: Message):
        bot_text = message_obj.text if message_obj.text else 'image'
        is_bot = message_obj.from_user.is_bot
        message_id = message_obj.message_id
        timestamp = message_obj.date
        message = {"role": "assistant" if is_bot else "user", "content": bot_text, "timestamp": timestamp.isoformat(), "message_id": message_id}
        return message

    async def deal_with_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE, reply_text: str):
        messages = []
        text = update.effective_message.text
        user_id = update.effective_user.id
        chat_id = update.effective_chat.id
        is_bot = update.effective_user.is_bot
        message_id = update.effective_message.message_id
        timestamp = update.effective_message.date
        messages.append({"role": "user" if not is_bot else "assistant", "content": text, "timestamp": timestamp.isoformat(), "message_id": message_id})
        message_obj = await update.message.reply_text(reply_text)
        message = self.convert_message_obj(message_obj)
        messages.append(message)
        await self.store_message_mongodb(user_id, chat_id, self.chatbot_agent, messages)

    async def standard_chatbot(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await self.deal_with_command(update, context, "🤖 Hello! I'm your standard chatbot. Send me a message!")
        self.chatbot_agent = 'standard_agent'

    async def mini_mavia_chatbot(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await self.deal_with_command(update, context, "🤖 Hello! I'm your Mini Mavia chatbot. Send me a message!")
        self.chatbot_agent = 'mini_mavia_agent'

    async def block_clans_chatbot(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await self.deal_with_command(update, context, "🤖 Hello! I'm your Block Clans chatbot. Send me a message!")
        self.chatbot_agent = 'block_clans_agent'

    async def list_all_agents(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await self.deal_with_command(update, context, "Currently, there are 3 agents available: \n1. /mini_mavia_chatbot \n2. /block_clans_chatbot \n3. /standard_chatbot")


    async def clear_chat(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        chat_id = update.effective_chat.id

        await self.deal_with_command(update, context, "🤖 Clearing chat history...")
        if self.db_url:
            response = await self.http_client.get(self.db_url + f"/llm_model/chat_history/{user_id}/{chat_id}")
            if response.status_code == 200:
                data = response.json()
                chat_history = data.get("history", [])
                for convo in chat_history:
                    for msg in convo.get("messages", []):
                        try:
                            await context.bot.delete_message(
                                chat_id=chat_id,
                                message_id=msg["message_id"]
                            )
                            print(f"Deleted message {msg['message_id']}")
                        except Exception as e:
                            print(f"⚠️ Failed to delete message {msg['message_id']}: {e}")

    async def new_chat(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if self.db_url:
            await self.http_client.post(self.db_url + "/llm_model/clear_chat", json={
                "user_id": update.effective_user.id,
                "chat_id": update.effective_chat.id,
                "agent_name": ""
            })
        await self.deal_with_command(update, context, "🤖 New chat started!")

    async def store_message_mongodb(self, user_id: int, chat_id: int, bot_name: str, messages: list):
        if self.db_url:
            await self.http_client.post(self.db_url + "/llm_model/save_message", json={
                "user_thread": {
                    "user_id": user_id,
                    "chat_id": chat_id,
                    "agent_name": bot_name
                },
                "messages": messages
            })
    
    async def extract_images_from_response(self, response: str) -> tuple[str, list[Path]]:
        pdf_folder = files("nexira_ai_package.vector_db") / "nexira_docs"
        output_folder = pdf_folder / "dataset"
        image_pattern = r'!\[[^\]]*\]\((.*)\)'
        matches = re.findall(image_pattern, response)
        image_paths = []
        for url in matches:
            filename = Path(url).name
            base_name = filename.split(".pdf")[0]
            image_path = output_folder / f"{base_name}_images" / filename

            if image_path.exists():
                image_paths.append(image_path)
            else:
                print(f"⚠️ Image not found: {image_path}")
        cleaned_response = re.sub(image_pattern, '', response).strip()
        return cleaned_response, image_paths

    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        messages = []
        text = update.effective_message.text
        user_id = str(update.effective_user.id)
        chat_id = str(update.effective_chat.id)
        is_bot = update.effective_user.is_bot
        message_id = update.effective_message.message_id
        timestamp = update.effective_message.date
        messages.append({"role": "user" if not is_bot else "assistant", "content": text, "timestamp": timestamp.isoformat(), "message_id": message_id})
        if update.effective_chat.type in ["group", "supergroup"]:
            bot_username = (await context.bot.get_me()).username
            if f"@{bot_username}" not in text:
                await self.store_message_mongodb(user_id, chat_id, self.chatbot_agent, messages)
                return
        try:
            url = self.api_url + "/llm_model/ask"
            response = await self.http_client.post(url, json={'question': text, 'agent_name': self.chatbot_agent, 'user_id': user_id, 'chat_id': chat_id})
            bot_text = response.json()['response']['answer']
            cleaned_response, image_paths = await self.extract_images_from_response(bot_text)

            print(cleaned_response)
            converted = telegramify_markdown.markdownify(
                cleaned_response,
                max_line_length=None,
                normalize_whitespace=False
            )
            message_obj = await update.message.reply_text(converted, parse_mode="MarkdownV2")
            if image_paths:
                media_group = [InputMediaPhoto(media=open(path, "rb")) for path in image_paths]
                media_response = await update.message.reply_media_group(media=media_group)
                for media in media_response:
                    message = self.convert_message_obj(media)
                    messages.append(message)

            message = self.convert_message_obj(message_obj)
            messages.append(message)
            await self.store_message_mongodb(user_id, chat_id, self.chatbot_agent, messages)
        except Exception as e:
            await update.message.reply_text(f"Error: {str(e)}")

    async def handle_document_upload(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        print("Document upload")
        #print(update)
        document = update.effective_message.document
        user_id = str(update.effective_user.id)
        chat_id = str(update.effective_chat.id)
        is_bot = update.effective_user.is_bot
        message_id = update.effective_message.message_id
        timestamp = update.effective_message.date
        file_id = document.file_id
        unique_id = document.file_unique_id
        file_size = document.file_size
        file_name = document.file_name

        file = await context.bot.get_file(file_id)
        file_bytes = await file.download_as_bytearray()

        files = {"file": (file_name, file_bytes)}
        data = {
            "file_name": file_name,
            "metadata": json.dumps({
                "user_id": user_id,
                "chat_id": chat_id,
                "is_bot": is_bot,
                "message_id": message_id,
                "timestamp": timestamp.isoformat(),
                "file_size": file_size,
                "file_unique_id": unique_id,
                "file_id": file_id
            })
        }

        response = requests.post(
            self.db_url + "/vector_db/insert_document",
            files=files,
            data=data
        )



    async def handle_photo_upload(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        print("Photo upload")
        print(update)

    async def handle_audio_upload(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        print("Audio upload")
        print(update)

    def run(self):
        print("🤖 Bot is running...")
        self.application.run_polling()
