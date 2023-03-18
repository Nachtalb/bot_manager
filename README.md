# Telegram Bot Manager

A small app that can run however many different telegram bots you want with a
simple interface to managed them.

## Install

Clone the repo to your host then. Install it via poetry and run `start-bots`:

```bash
git clone https://github.com/Nachtalb/bot_manager
cd bot_manager
poetry install
echo '[
  {
    "id": "echo",
    "module_name": "echo",
    "telegram_token": "some token",
    "auto_start": true,
    "arguments": {
      "foo": "bar"
    }
  }
]' > config.json
poetry run start-bots
```

## Developing

To develop new bots simply copy paste the existing `echo.py` to a eg. `group_manager.py`.
Then in the `group_manager.py` rename your class to `GroupManager` and at the
bottom set `Application = GroupManager`.

In the `def setup(self):` method you can add handlers to your application or
whatever you need to configure. Other than the `setup` which is run before the
application has been started you can also use `async startup`, `async shutdown`
and `teardown` which are run after the bot has been started, before it's
stopped and before the whole manager is stopped (eg. when using CTRL-C).

Last but not least add an entry in the `config.json`. Whereas the arguments and
the auto_start are optional. Auto start is by default off.

## Usage

After you have started the manager with `poetry run start-bots` you can open
the shown url `https://localhost:8000` and manage your bots.
