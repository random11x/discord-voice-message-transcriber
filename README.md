# discord-voice-message-transcriber
Discord.py bot that transcribes voice messages using OpenAI Whisper

![image](https://github.com/random11x/discord-voice-message-transcriber/assets/137963515/71c92a83-86df-47ed-a4e8-d42e37996c3b)

# Get Started

To use the bot, you will first need to install [Python](https://python.org). Python 3.10 is recommended as it's the easiest to set up. 3.11 also works and can provide some speedup, but you may need to install a pre-release version of numba using `pip install --pre numba`.

You can install the needed dependencies by doing `pip install -r requirements.txt`.

You will also need a bot token (acquirable at the [Discord Developer Portal](https://discord.com/developers/applications)), which you will need to add to the `.env` file after `BOT_TOKEN=`. Make sure your bot has the Message Content intent, or it won't be able to read any voice messages.

Your bot user will need these permissions depending on what functions you want it to do (Permission Integer: `279172992000`):

![image](https://github.com/random11x/discord-voice-message-transcriber/assets/137963515/d30c65f8-ec95-4315-9907-9a7520665b3f)

`Trascribe Memo (Public)` and `Auto Trascribe` will need to be able to send messages and view the channel. `Transcribe Memo (Private)` and `Convert Memo To Mp3` need less permissions as they use direct replies that only the user can see.

Finally, in the config.ini file, you can change some settings that alter how the bot works. You will need to add your User ID in the `admin > users` variable, just so you can control the bot via commands later. Alternately, you can also input a Role ID in `admin > role` to allow users with a specific role to control the bot, but this requires the Server Members intent.

Once you have successfully started the bot, send "!synctree" in a channel the bot can see in order to get context menu functionality + slash commands working. (This can sometimes take up to an hour for the commands to propogate through discords servers. If they aren't appearing also try to restart discord, that might help)

The context menu commands will appear when rightclicking on a message

![image](https://github.com/random11x/discord-voice-message-transcriber/assets/137963515/123db5f9-db50-4e9c-aff9-a471606fb4ca)

Currently the slash commands are commented out. But if you want to turn them back on, they would appear when you use "/" in the text input field.

![image](https://github.com/random11x/discord-voice-message-transcriber/assets/137963515/800b6f59-eae7-4aff-9318-9ad3af59d1c9)

(In order to get these to show up you would have to uncomment the commands in main.py and then run !synctree)

# Contribute & Other Stuff

Sorry for the spaghetti code, I frankly have no idea how to do voice recognition efficiently.

Feel free to make pull requests to improve stuff for the next person.

If you encounter any issues with the code, leave them in the issue tracker and someone might fix it for you.

The code is licensed under the MIT license, which probably means you can do whatever with it, so have fun :)
