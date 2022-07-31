import discord
from discord import app_commands
from discord.ui import Select, View

import random
import requests
import json

import youtube_dl
import pafy

from wand.image import Image

class SlashClient(discord.Client):
    def __init__(self):
        super().__init__(intents = discord.Intents.all(), command_prefix = '>')
        self.synced = False
    
    async def on_ready(self):
        await self.wait_until_ready()
        if not self.synced:
            await tree.sync()
            self.synced = True
        print(f'{self.user} is ready!')

client = SlashClient()
tree = app_commands.CommandTree(client)

@tree.command(name = "ping", description = "Returns pong!")
async def ping(interaction : discord.Interaction):
    await interaction.response.send_message("Pong!")

@tree.command(name = "echo", description = "Echoes the message")
async def echo(interaction : discord.Interaction):
    await interaction.response.send_message(interaction.message.content)

@tree.command(name = "flip", description = "Flips a coin")
async def flip(interaction : discord.Interaction):
    await interaction.response.send_message(random.choice(["heads", "tails"]))
    
@tree.command(name = "roll", description= "Rolls a dice")
async def roll(interaction : discord.Interaction):
    await interaction.response.send_message(random.randint(1, 6))
    
@tree.command(name = "rps", description = "Play rock paper scissors")
async def rps(interaction : discord.Interaction):
    bot_choice = random.choice(["rock", "paper", "scissors"])
    select = Select(
        placeholder="Choose an option!",
        options = [
            discord.SelectOption(label = "rock", emoji = "✊"),
            discord.SelectOption(label = "paper", emoji = "✋"),
            discord.SelectOption(label = "scissors", emoji = "✌")
        ]
    )
    async def check(interaction : discord.Interaction):
        user_choice = select.values[0]
        if user_choice == bot_choice:
            await interaction.response.send_message('It\'s a tie!')
        elif user_choice == 'rock':
            if bot_choice == 'paper':
                await interaction.response.send_message('I win!')
            else:
                await interaction.response.send_message('You win!')
        elif user_choice == 'paper':
            if bot_choice == 'scissors':
                await interaction.response.send_message('I win!')
            else:
                await interaction.response.send_message('You win!')
        elif user_choice == 'scissors':
            if bot_choice == 'rock':
                await interaction.response.send_message('I win!')
            else:
                await interaction.response.send_message('You win!')
    select.callback = check
    view = View()
    view.add_item(select)
    
    await interaction.response.send_message(view = view)
    
@tree.command(name = "dadjoke", description = "Tell a random dad joke!")
async def dadjoke(interaction : discord.Interaction):
    url = "https://dad-jokes.p.rapidapi.com/random/joke"

    headers = {
        "X-RapidAPI-Key": "d3c5dbe6ccmsh37d38169379cda7p1d66a8jsn4f5b8d97ed41",
        "X-RapidAPI-Host": "dad-jokes.p.rapidapi.com"
    }

    response = requests.request("GET", url, headers=headers)

    response = response.json()
    
    await interaction.response.send_message(response["body"][0]["setup"] + "\n" + response["body"][0]["punchline"])

voice = None
YDL_OPTIONS = {"format" : "bestaudio", "quiet" : True}

@tree.command(name = "join", description = "Join voice channel")
async def join(interaction : discord.Interaction, voice_channel : discord.VoiceChannel):
    global voice
    try:
        await interaction.response.send_message(f"Connected to voice channel {voice_channel.name}!")
        voice = await voice_channel.connect()
    except:
        await interaction.response.send_message("Already joined!")
        
@tree.command(name = "leave", description = "Leave voice channel")
async def leave(interaction : discord.Interaction):
    if voice is None:
        await interaction.response.send_message("Not in a voice channel!")
    else:
        await voice.disconnect()
        await interaction.response.send_message("Disconnected from voice channel!")

def _search(query, amount = 20):
    with youtube_dl.YoutubeDL(YDL_OPTIONS) as ydl:
        get_url = False
        try:
            requests.get(query) # check if link
            get_url = True
        except:
            video = ydl.extract_info(f"ytsearch:{amount}:{query}", download=False, ie_key="YoutubeSearch") # handle query
        else:
            video = ydl.extract_info(query, download=False) # handle link
    return [entry["webpage_url"] for entry in video["entries"]] if get_url else video

@tree.command(name = "play", description = "Play a song from youtube!")
async def play(interaction : discord.Interaction, link_or_query : str):
    if voice is None:
        await interaction.response.send_message("Not in a voice channel!")
        return
    video = _search(link_or_query)
    url = video["entries"][0]["webpage_url"]
    title = video["entries"][0]["title"]
    await interaction.response.send_message(f"Playing {title}...")
    url = pafy.new(url).getbestaudio().url
    voice.play(discord.FFmpegPCMAudio(url))


@tree.command(name = "search", description = "Search for songs on youtube!")
async def search(interaction : discord.Interaction, query : str):
    video = _search(query)["entries"][0]
    embed = discord.Embed(title = "Search result")
    amount = 0
    embed.description = f"[{video['title']}]({video['webpage_url']})"
    await interaction.response.send_message(embed = embed)
    
@tree.command(name = "stop", description = "Stop the music")
async def stop(interaction : discord.Interaction):
    if voice is None:
        await interaction.response.send_message("Not connected to voice!")
    elif not voice.is_playing():
        await interaction.response.send_message("Already stopped!")
    else:
        voice.stop()
        await interaction.response.send_message("Stopped!")
        
@tree.command(name = "pause", description = "Pause the music")
async def pause(interaction : discord.Interaction):
    if voice is None:
        await interaction.response.send_message("Not connected to voice!")
    elif voice.is_paused():
        await interaction.response.send_message("Already paused!")
    else:
        voice.pause()
        await interaction.response.send_message("Paused!")
        
@tree.command(name = "resume", description = "Resume the music")
async def resume(interaction : discord.Interaction):
    if voice is None:
        await interaction.response.send_message("Not connected to voice!")
    elif voice.is_playing():
        await interaction.response.send_message("Already playing!")
    else:
        voice.resume()
        await interaction.response.send_message("Resumed!")
        
file_name = "image_to_edit.jpg"
edited_file_name = "edited_image.jpg"

@tree.command(name = "editimg", description = "Edit an image")
async def editimg(interaction : discord.Interaction):
    # Download image
    if len(interaction.message.attachments) > 0:
        attachment = interaction.message.attachments[0]
        img_data = requests.get(attachment.url).content
        with open(file_name, 'wb') as handler:
            handler.write(img_data)
    
    select = Select(
        placeholder="Choose an option!",
        options = [
            discord.SelectOption(label = "grayscale"),
            discord.SelectOption(label = "implode"),
            discord.SelectOption(label = "swirl"),
            discord.SelectOption(label = "blur"),
            discord.SelectOption(label = "solarize"),
            discord.SelectOption(label = "flip")
        ]
    )
    async def edit(interaction : discord.Interaction):
        option = select.values[0]
        if option == "grayscale":
            with Image(filename=file_name) as img:
                img.transform_colorspace("gray")
                img.save(filename = edited_file_name)
        elif option == "implode":
            with Image(filename=file_name) as img:
                img.implode(0.7, "blend")
                img.save(filename = edited_file_name)
        elif option == "swirl":
            with Image(filename=file_name) as img:
                img.swirl(100, "blend")
                img.save(filename = edited_file_name)
        elif option == "blur":
            with Image(filename=file_name) as img:
                img.blur(sigma = 10)
                img.save(filename = edited_file_name)
        elif option == "solarize":
            with Image(filename=file_name) as img:
                img.solarize(threshold = 0.25 * img.quantum_range)
                img.save(filename = edited_file_name)
        elif option == "flip":
            with Image(filename=file_name) as img:
                img.flip()
                img.save(filename = edited_file_name)
        await interaction.response.send_message(file = discord.File(edited_file_name))
    select.callback = edit
    view = View()
    view.add_item(select)
    
    await interaction.response.send_message(view = view)
    
client.run(NO TOKEN 4 U)
