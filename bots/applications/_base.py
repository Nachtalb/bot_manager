import logging
from pydantic import BaseModel
from telegram import User
from telegram.ext import ApplicationBuilder

from bots.config import ApplicationConfig
from bots.config import config as global_config


class ApplicationWrapper:
    class Arguments(BaseModel):
        pass

    class Config(BaseModel):
        id: str
        telegram_token: str
        auto_start: bool = False

    def __init__(self, config: ApplicationConfig):
        self.config = self.Config.parse_obj(config)
        self.arguments = self.Arguments.parse_obj(config.arguments)

        self.name = f"{self.__class__.__name__}-{self.config.id}"

        self.logger = logging.getLogger(self.id)
        self.logger.setLevel(global_config.local_log_level_int)

        self.application = ApplicationBuilder().token(self.config.telegram_token).build()
        self.running: bool = False
        self._bot: User | None = None

    @property
    def id(self):
        return self.config.id

    @property
    def auto_start(self):
        return self.config.auto_start

    async def get_bot(self) -> User:
        if not self._bot:
            await self._refresh_bot_info()
        return self._bot  # pyright: ignore[reportGeneralTypeIssues]

    async def _refresh_bot_info(self) -> User:
        self._bot = await self.application.bot.get_me()
        return self._bot

    async def setup(self):
        """Run as immediately after all applications have been loaded"""
        pass

    async def startup(self):
        """Run after the bot has been initialized and started"""
        pass

    async def shutdown(self):
        """Run before the application is being stopped"""
        pass

    async def teardown(self):
        """Run before the manager is stopped (eg. due to a config reload or CTRL-C)"""
        pass

    async def start_application(self):
        await self.application.initialize()
        await self.application.start()
        await self.application.updater.start_polling()
        self.logger.info("Started")
        self.running = True
        await self.startup()
        return self

    async def stop_application(self):
        if self.running:
            await self.shutdown()
            await self.application.updater.stop()
            await self.application.stop()
            await self.application.shutdown()
            self.running = False
            self.logger.info("Stopped")
        else:
            self.logger.info("Already stopped")
