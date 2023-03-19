from pydantic import BaseModel
from telegram.ext import ApplicationBuilder

from bots.config import ApplicationConfig


class ApplicationWrapper:
    class Arguments(BaseModel):
        pass

    class Config(BaseModel):
        id: str
        module_name: str
        telegram_token: str
        auto_start: bool = False

    def __init__(self, config: ApplicationConfig):
        raw_config = config.dict()
        self.arguments = self.Arguments.parse_obj(raw_config.pop("arguments"))
        self.config = self.Config.parse_obj(raw_config)

        self.name = f"{self.__class__.__name__}-{self.config.id}"

        self.application = ApplicationBuilder().token(self.config.telegram_token).build()
        self.running: bool = False

    @property
    def id(self):
        return self.config.id

    @property
    def auto_start(self):
        return self.config.auto_start

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
        self.running = True
        return self

    async def stop_application(self):
        if self.running:
            await self.shutdown()
            await self.application.updater.stop()
            await self.application.stop()
            await self.application.shutdown()
            self.running = False
