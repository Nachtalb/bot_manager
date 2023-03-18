from telegram.ext import ApplicationBuilder


class ApplicationWrapper:
    def __init__(self, telegram_token: str, _id: str, auto_start: bool = False, setup_args: dict = {}):
        self.telegram_token = telegram_token
        self.id = _id
        self.name = f"{self.__class__.__name__}-{self.id}"
        self.auto_start = auto_start
        self.setup_args = setup_args

        self.application = ApplicationBuilder().token(telegram_token).build()
        self.running: bool = False

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

    async def start(self):
        await self.application.initialize()
        await self.application.start()
        await self.application.updater.start_polling()
        self.running = True
        return self

    async def stop(self):
        if self.running:
            await self.shutdown()
            await self.application.updater.stop()
            await self.application.stop()
            await self.application.shutdown()
            self.running = False
