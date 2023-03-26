import logging
from typing import TYPE_CHECKING

from pydantic import BaseModel
from telegram import User
from telegram.ext import ApplicationBuilder

from bots.config import ApplicationConfig
from bots.config import config as global_config

if TYPE_CHECKING:
    from . import AppManager


class Application:
    class Arguments(BaseModel):
        pass

    class Config(BaseModel):
        id: str
        telegram_token: str
        auto_start: bool = False

    def __init__(self, manager: "AppManager", config: ApplicationConfig):
        self.manager = manager
        self.config = self.Config.parse_obj(config)
        self.arguments = self.Arguments.parse_obj(config.arguments)

        self.logger = logging.getLogger(self.id)
        self.logger.setLevel(global_config.local_log_level_int)

        self.name = f"{self.__class__.__name__}-{self.config.id}"

        self.initialized: bool = False
        self.running: bool = False

        self.application = ApplicationBuilder().token(self.config.telegram_token).build()

    @property
    def id(self):
        return self.config.id

    @property
    def auto_start(self):
        return self.config.auto_start

    async def get_bot(self) -> User:
        if not self.application.bot._bot_user:
            await self.application.bot.get_me()
        return self.application.bot._bot_user  # pyright: ignore[reportGeneralTypeIssues]

    async def refresh_bot(self) -> User:
        return await self.application.bot.get_me()

    # =========
    # LIFECYCLE
    # =========

    async def initialize(self):
        """Initialise the application

        This is the first method called after creating an application.
        It initialize both the self.router and the python-telegram-bot
        self.application.

        After initialize() we have a fully functional ptb bot that can
        send updated to Telegram (it just doesn't receive updates yet).
        So it is possible to use self.get_me() to get an instance of
        our bot, set user specific commands etc.

        Lifecycle:
            - * initialize()
            - on_initialize()
            - start()
            - on_start()
            - on_pause()
            - pause()
            - on_shutdown()
            - shutdown()
        """
        if not self.initialized:
            self.add_routes()
            if hasattr(self, "handle_error"):
                self.application.add_error_handler(self.handle_error)  # pyright: ignore[reportGeneralTypeIssues]

            await self.application.initialize()
            self.initialized = True
            self.running = False
            self.logger.info("Initialized")
        else:
            self.logger.debug("Already initialized")

        await self.on_initialize()

    async def on_initialize(self):
        """Called after app has been initialized

        Overwrite this method instead of initialize. You can add handlers
        to self.application, open database connections etc.

        Lifecycle:
            - initialize()
            - * on_initialize()
            - start()
            - on_start()
            - on_pause()
            - pause()
            - on_shutdown()
            - shutdown()
        """
        pass

    async def start(self) -> "Application":
        """Starts the underlying ptb app

        Start receiving updates from Telegram, start the updater processing queue
        and start the job queue.

        Lifecycle:
            - initialize()
            - on_initialize()
            - * start()
            - on_start()
            - on_pause()
            - pause()
            - on_shutdown
            - shutdown()
        """
        if not self.running:
            await self.application.start()
            await self.application.updater.start_polling()  # pyright: ignore[reportOptionalMemberAccess]

            self.running = True

            await self.on_start()
            self.logger.info("Started")
        else:
            self.logger.info("Already started")

        await self.on_start()
        return self

    async def on_start(self):
        """Run after the app has been started

        After the app has been started (receiving updates from Telegram),
        on_start() is run where you can run whatever you might need.

        Lifecycle:
            - initialize()
            - on_initialize()
            - start()
            - * on_start()
            - on_pause()
            - pause()
            - on_shutdown()
            - shutdown()
        """
        pass

    async def on_pause(self):
        """Run before we pause the app

        Before the app has will be paused (stop receiving updates from Telegram),
        on_pause() is run.

        If you shutdown an application it is first paused and then shutdown. So
        while the application is running the shutdown will run:
        on_pause() -> pause() -> shutdown()

        Lifecycle:
            - initialize()
            - on_initialize()
            - start()
            - on_start()
            - * on_pause()
            - pause()
            - on_shutdown()
            - shutdown()
        """
        pass

    async def pause(self):
        """Pause the application

        Waits for running tasks to finish then stops receiving updates from
        Telegram, stops the update queue and the job queue. If there are sill
        unprocessed updates in the queue, they will not be processed.

        Lifecycle:
            - initialize()
            - on_initialize()
            - start()
            - on_start()
            - on_pause()
            - * pause()
            - on_shutdown()
            - shutdown()
        """
        await self.on_pause()

        if self.running:
            await self.application.updater.stop()  # pyright: ignore[reportOptionalMemberAccess]
            await self.application.stop()

            self.running = False
            self.logger.info("Paused")
        else:
            self.logger.debug("Already paused")

    async def on_shutdown(self):
        """Right before the app is shut down

        Override this instead of shutdown. Here you can save any in memory data,
        close potential database connections and so on.

        Lifecycle:
            - initialize()
            - on_initialize()
            - start()
            - on_start()
            - on_pause()
            - pause()
            - * on_shutdown()
            - shutdown()
        """
        pass

    async def shutdown(self):
        """Shutdown the application

        Shuts down ("uninitialize") the application.
        If the app is still running it will first be paused then shut down.
        on_pause() -> pause() -> shutdown()

        Lifecycle:
            - initialize()
            - on_initialize()
            - start()
            - on_start()
            - on_pause()
            - pause()
            - on_shutdown()
            - * shutdown()
        """
        if self.running:
            await self.pause()

        await self.on_shutdown()

        if self.initialized:
            await self.application.shutdown()
            self.initialized = False
            self.running = False

            self.logger.info("Shutdown")

    async def reload(self) -> "Application":
        """Reload the whole app

        First it shuts down the app, deletes it's instance, reloads the python
        module and then inits and starts the app again (if it was started
        beforehand). So it realods the corresponding python code as well as the
        configuration from the config.json.
        """
        return await self.manager.reload_app(self.id)
