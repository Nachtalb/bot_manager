from pathlib import Path
from pydantic import Field
from telegram import Update
from telegram.ext import ContextTypes, MessageHandler, filters

from bots.applications._base import Application


class Echo(Application):
    class Arguments(Application.Arguments):
        sample_field_1: str = "Foo"
        sample_field_2: int
        sample_field_3: Path = Field(default_factory=lambda: Path(__file__))

    arguments: "Echo.Arguments"

    async def on_initialize(self):
        self.application.add_handler(MessageHandler(filters.TEXT, self.echo))

    async def echo(self, update: Update, _: ContextTypes.DEFAULT_TYPE):
        if update.message:
            await update.message.reply_markdown_v2(update.message.text_markdown_v2_urled)


Application = Echo
