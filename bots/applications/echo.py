from telegram import Update
from telegram.ext import ContextTypes, MessageHandler, filters

from bots.applications._base import Application


class Echo(Application):
    async def setup(self):
        self.application.add_handler(MessageHandler(filters.TEXT, self.echo))

    async def echo(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if update.message:
            await update.message.reply_markdown_v2(update.message.text_markdown_v2_urled)


Application = Echo
