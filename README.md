# Telegram Bot Manager

A small app that can run however many different telegram bots you want with a
simple interface to managed them.

## Install

Clone the repo to your host then. Install it via poetry and run `start-bots`:

```bash
git clone https://github.com/Nachtalb/bot_manager
cd bot_manager
poetry install
cp config.example.json config.json  # Adjust config.json file
poetry run start-bots
```

## Developing

### Base

Create a new module in `bots.applications`:

```text
bots
├── ...
└── applications
   ├── ...
   └── my_app.py

```

Create and application in `my_app.py`:

```python
from bots.applications._base import ApplicationWrapper

class MyApp(ApplicationWrapper):
    pass

Application = MyApp
```

Adjust `config.json` to use your new app.

```json
{
  ...,
  "app_configs": [
    {
      "id": "my-app",
      "telegram_token": "123....",
      "auto_start": true,
      "module_name": "my_app"
    }
  ]
}
```

### Setup

Now your bot is already configured and working. But of course you want some
functionality. For this you can simply adjust the `setup()` method to configure
your application.

```python
class MyApplication(ApplicationWrapper):
    async def setup(self):
        self.application.add_handler(MessageHandler(filters.TEXT, self.echo))

    async def echo(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if update.message:
            await update.message.reply_markdown_v2(update.message.text_markdown_v2_urled)
```

### Custom Config

Maybe you want to run multiple telegram bots of the same type to decrease
rate limits in channels or something alike. So you need a way to pass custom
arguments to your bot. You can do so by defining "Arguments".

First add your arguments to the class:

```python
from pathlib import Path
from bots.applications._base import ApplicationWrapper

class MyApplication(ApplicationWrapper):
    class Arguments(ApplicationWrapper.Arguments):
        custom_arg_1: int
        custom_arg_2: Path

    arguments: "MyApplication.Arguments"  # Make sure type hinting works

    async def setup(self):
        ...
        do_stuff_with(self.arguments.custom_arg_1, self.arguments.custom_arg_2)
```

Then add the arguments to your `config.json`. In this example I now create
two bots of the same kind with different arguments (also make sure the `id` is
unique):

```json
{
  ...,
  "app_configs": [
    {
      "id": "my-app-1",
      "telegram_token": "123....",
      "auto_start": true,
      "module_name": "my_app",
      "arguments": {
        "custom_arg_1": "Some text",
        "custom_arg_2": "path/to/a/file.txt"
      }
    },
    {
      "id": "my-app-2",
      "telegram_token": "456....",
      "auto_start": true,
      "module_name": "my_app",
      "arguments": {
        "custom_arg_1": "Another text",
        "custom_arg_2": "path/to/a/different/file.txt"
      }
    }
  ]
}

```

## Usage

After you have started the manager with `poetry run start-bots` you can open
the shown url `https://localhost:8000` and manage your bots.
