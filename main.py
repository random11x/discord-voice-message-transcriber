from typing import Union
import warnings
warnings.filterwarnings("ignore", message=".*The 'nopython' keyword.*")

import io
import os
import re
import sys
import functools
import configparser
import urllib.parse
import traceback

import discord
import speech_recognition
import pydub
from discord import app_commands

from dotenv import load_dotenv

color_error=0xda201b
color_waiting=0x1d4ffc
color_warn=0xdb8d1a
color_done=0x239632

load_dotenv(".env")
BOT_TOKEN = os.getenv("BOT_TOKEN")

config = configparser.ConfigParser()
config.read("config.ini")

if "transcribe" not in config and "admins" not in config:
	print("Something is wrong with your config.ini file.")
	sys.exit(1)

try:
	TRANSCRIBE_ENGINE = config["transcribe"]["engine"]
	TRANSCRIBE_APIKEY = config["transcribe"]["apikey"]
	TRANSCRIBE_AUTOMATICALLY = config.getboolean("transcribe", "automatically")
	TRANSCRIBE_VMS_ONLY = config.getboolean("transcribe", "voice_messages_only")
	ADMIN_USERS = [int(i) for i in re.split(", |,", config["admins"]["users"])]
	ADMIN_ROLE = config.getint("admins", "role")

except (configparser.NoOptionError, ValueError):
	print("Something is wrong with your config.ini file.")
	sys.exit(1)

intents = discord.Intents.default()
intents.messages = True
intents.message_content = True
intents.members = ADMIN_ROLE != 0
client = discord.Client(command_prefix='!', intents=intents, allowed_mentions=discord.AllowedMentions.none()) # i didnt want the bot pinging people. Remove allowed_mentions if you do
tree = app_commands.CommandTree(client)

previous_transcriptions = {}

@client.event
async def on_ready():
	print("BOT READY!")

async def transcribe_message(message, interaction=None, is_private=False):
	
	original_response = None if interaction is None else await interaction.original_response()
	msg = original_response

	try:

		if len(message.attachments) == 0:
			error_embed=discord.Embed(color=color_error, description="Transcription failed! (No Voice Message)")
			if original_response is not None:
				await msg.edit(embed=error_embed)
			else:
				await message.reply(embed=error_embed, mention_author=False)
			return
		if TRANSCRIBE_VMS_ONLY and message.attachments[0].content_type != "audio/ogg":
			error_embed=discord.Embed(color=color_error, description="Transcription failed! (Attachment not a Voice Message)")
			if original_response is not None:
				await msg.edit(embed=error_embed)
			else:
				await message.reply(embed=error_embed, mention_author=False)
			return
		
		if original_response is None:
			waiting_embed=discord.Embed(color=color_waiting, description="✨ Transcribing...")
			msg = await message.reply(embed=waiting_embed, mention_author=False)
		
		# Read voice file and converts it into something pydub can work with
		voice_file = await message.attachments[0].read()
		voice_file = io.BytesIO(voice_file)
		
		# Convert original .ogg file into a .wav file
		x = await client.loop.run_in_executor(None, pydub.AudioSegment.from_file, voice_file)
		
		new = io.BytesIO()
		await client.loop.run_in_executor(None, functools.partial(x.export, new, format='wav'))
		
		# Convert .wav file into speech_recognition's AudioFile format or whatever idrk
		recognizer = speech_recognition.Recognizer()
		with speech_recognition.AudioFile(new) as source:
			audio = await client.loop.run_in_executor(None, recognizer.record, source)
		
		# Runs the file through OpenAI Whisper (or API, if configured in config.ini)
		if TRANSCRIBE_ENGINE == "whisper":
			result = await client.loop.run_in_executor(None, recognizer.recognize_whisper, audio)
		elif TRANSCRIBE_ENGINE == "api":
			if TRANSCRIBE_APIKEY == "0":
				discord.Embed(color=color_error, description="Transcription failed! (Configured to use Whisper API, but no API Key provided!)")
				await msg.edit(embed=error_embed)
				return
			result = await client.loop.run_in_executor(None, functools.partial(recognizer.recognize_whisper_api, audio, api_key=TRANSCRIBE_APIKEY))

		if result == "":
			no_hear=discord.Embed(color=color_warn, description="*The bot didn't hear anything*")
			await msg.edit(embed=no_hear)
		else:
			# Send results + truncate in case the transcript is longer than 4050 characters
			result = "*\"" + result[:4050] + ("..." if len(result) > 4050 else "") + "\"*"
			if interaction is None or is_private:
				await msg.edit(embed=discord.Embed(color=color_done,description=result))
			else:
				await interaction.delete_original_response()
				msg = await message.reply(embed=discord.Embed(color=color_done,description=result), mention_author=False)

			previous_transcriptions[message.id] = {"id": msg.id, "url": msg.jump_url}

	except Exception as error:
		# handle the exception
		traceback.print_exc()

		error_embed=discord.Embed(color=color_error, description="Transcribe failed! (Unknown Error)")

		if msg is None:
			msg = await interaction.response.send_message(embed=error_embed, ephemeral=True)
		else:
			await msg.edit(embed=error_embed)

async def transcode_message(message, interaction):

	original_response = None if interaction is None else await interaction.original_response()
	msg = original_response

	try:
		if len(message.attachments) == 0:
			error_embed=discord.Embed(color=color_error, description="Transcode failed! (No Voice Message)")
			await msg.edit(embed=error_embed)
			return
		if TRANSCRIBE_VMS_ONLY and message.attachments[0].content_type != "audio/ogg":
			error_embed=discord.Embed(color=color_error, description="Transcode failed! (Attachment not a Voice Message)")
			await msg.edit(embed=error_embed)
			return
		
		if original_response is None:
			waiting_embed=discord.Embed(color=color_waiting, description="✨ Transcoding...")
			msg = await message.reply(embed=waiting_embed, mention_author=False)
		
		# Read voice file and converts it into something pydub can work with
		voice_file = await message.attachments[0].read()
		voice_file = io.BytesIO(voice_file)
		
		# Convert original .ogg file into a .wav file
		x = await client.loop.run_in_executor(None, pydub.AudioSegment.from_file, voice_file)
			
		new_mp3 = io.BytesIO()
		await client.loop.run_in_executor(None, functools.partial(x.export, new_mp3, format='mp3'))
		
		# Send results + truncate in case the transcript is longer than 4050 characters
		await msg.remove_attachments(message.attachments)
		msg = await msg.add_files(discord.File(new_mp3, filename="voice_message"))

		safe_string = urllib.parse.quote_plus(msg.attachments[0].url)
		
		transcode_embed=discord.Embed(title=":arrow_forward: Play Mp3", url="https://embedmediaplayer.web.app/?url="+safe_string, color=color_done)
		
		await msg.edit(embed=transcode_embed)
	except Exception as error:
		# handle the exception
		traceback.print_exc()

		error_embed=discord.Embed(color=color_error, description="Transcode failed! (Unknown Error)")

		if msg is None:
			msg = await interaction.response.send_message(embed=error_embed, ephemeral=True)
		else:
			await msg.edit(embed=error_embed)


def is_manager(input: Union[discord.Interaction, discord.Message]) -> bool:
	if type(input) is discord.Interaction:
		user = input.user
	else:
		user = input.author
	
	if user.id in ADMIN_USERS:
		return True
	
	if ADMIN_ROLE != 0:
		admin = input.guild.get_role(ADMIN_ROLE)

		if user in admin.members:
			return True

	return False


@client.event
async def on_message(message):
	if TRANSCRIBE_AUTOMATICALLY and message.flags.voice and len(message.attachments) == 1:
		await transcribe_message(message)

	if message.content == "!synctree" and is_manager(message):
		# await tree.sync(guild=message.guild)
		await tree.sync(guild=None)
		await message.reply("Sync received. Syncing can take up to an hour for discord servers to propagate the bot's commands.")
		return

# ## I commented this stuff out cause I dont need these commands
# # Slash Command / Context Menu Handlers
# @tree.command(name="opensource", description="Get a link for this bot's source code.")
# async def open_source(interaction: discord.Interaction):
# 	embed = discord.Embed(
#     	title="Open Source",
#     	description="This bot is open source! You can find the source code "
#                     "[here](https://github.com/RyanCheddar/discord-voice-message-transcriber)",
#     	color=0x00ff00
# 	)
# 	await interaction.response.send_message(embed=embed)
    
# @tree.command(name="synctree", description="Syncs the bot's command tree.")
# async def synctree(interaction: discord.Interaction):
# 	if not is_manager(interaction):
# 		await interaction.response.send_message(content="You are not a Bot Manager!")
# 		return

# 	await tree.sync(guild=None)
# 	await interaction.response.send_message(content="Sync received. Syncing can take up to an hour for discord servers to propagate the bot's commands.")

@tree.context_menu(name="Convert Memo To Mp3")
async def transcode_contextmenu_private(interaction: discord.Interaction, message: discord.Message):
	waiting_embed=discord.Embed(color=color_waiting, description="✨ Transcoding...")
	await interaction.response.send_message(embed=waiting_embed, ephemeral=True)
	await transcode_message(message, interaction)

@tree.context_menu(name="Transcribe Memo (public)")
async def transcribe_contextmenu_public(interaction: discord.Interaction, message: discord.Message):
    await handle_transcription_request(interaction, message, False)

@tree.context_menu(name="Transcribe Memo (private)")
async def transcribe_contextmenu_private(interaction: discord.Interaction, message: discord.Message):
    await handle_transcription_request(interaction, message, True)

async def handle_transcription_request(interaction, message, is_private):
	try:
		msg = None

		try:
			if message.id in previous_transcriptions:
				transcribed_info = previous_transcriptions[message.id]
				transcribed_message_id = transcribed_info.get("id")
				transcribed_message_url = transcribed_info.get("url")

				message = await interaction.channel.fetch_message(transcribed_message_id)

				already_done_embed = discord.Embed(color=0x239632,description="Already processed: " + transcribed_message_url)
				msg = await interaction.response.send_message(embed=already_done_embed, ephemeral=True)
				return
		except Exception as error:
			# handle the exception
			# print("An exception occurred:", type(error).__name__)
			# Suppress error and just re-transcribe the message
			pass
		waiting_embed=discord.Embed(color=color_waiting, description="✨ Transcribing...")
		msg = await interaction.response.send_message(embed=waiting_embed, ephemeral=True)
		await transcribe_message(message, interaction, is_private)
	except Exception as error:
		# handle the exception
		traceback.print_exc()

		error_embed=discord.Embed(color=color_error, description="Transcribe failed! (Unknown Error)")

		if msg is None:
			msg = await interaction.response.send_message(embed=error_embed, ephemeral=True)
		else:
			await msg.edit(embed=error_embed)

if __name__ == "__main__":
	client.run(BOT_TOKEN)
