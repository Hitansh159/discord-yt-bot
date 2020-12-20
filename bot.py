#! /usr/bin/env python

#imports
import os
import time
import random
import ffmpeg
import youtube_dl
#from googlesearch import search

import discord
from dotenv import load_dotenv
from discord.ext import commands
from discord import FFmpegPCMAudio

# youtube stream parameters
youtube_dl.utils.bug_reports_message = lambda: ''


ytdl_format_options = {
    'format': 'bestaudio/best',
    'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',
    'restrictfilenames': True,
    'noplaylist': True,
    'nocheckcertificate': True,
    'ignoreerrors': False,
    'logtostderr': False,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'auto',
    'source_address': '0.0.0.0' # bind to ipv4 since ipv6 addresses cause issues sometimes
}

ffmpeg_options = {
    'options': '-vn'
}

ytdl = youtube_dl.YoutubeDL(ytdl_format_options)

class YTDLSource(discord.PCMVolumeTransformer):
    def __init__(self, source, *, data, volume=0.5):
        super().__init__(source, volume)

        self.data = data

        self.title = data.get('title')
        self.url = data.get('url')

    @classmethod
    async def from_url(cls, url, *, loop=None, stream=False):
        loop = loop or asyncio.get_event_loop()
        data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=not stream))

        if 'entries' in data:
            # take first item from a playlist
            data = data['entries'][0]

        filename = data['url'] if stream else ytdl.prepare_filename(data)
        return cls(discord.FFmpegPCMAudio(filename, **ffmpeg_options), data=data)


# laoding token and other required environment variables
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

bot = commands.Bot(command_prefix= '!')

##############################################################
#bot commmands 						     #
##############################################################

@bot.command( name = 'hello', help='Responds hello')
async def hello(ctx):
	await ctx.send('hello')



@bot.command(name ='flip', help='flip the coin')
async def flip(ctx):
	choice = random.randint(0,1)
	choice = 'hats' if choice <= 0.5 else 'tails'
	await ctx.trigger_typing()
	time.sleep(1)
	await ctx.send(choice, delete_after = 2.0 )



@bot.command(name='sing', help='Sings songs', pass_context=True)
async def sing(ctx, *, url):
	channel = ctx.message.author.voice
	if not channel:
		await ctx.send('You are not connect to the voice channel')
		return

	vc = await channel.channel.connect()
	if vc.is_connected(): 
		await ctx.send("connected to vc")

	async with ctx.typing():
		player = await YTDLSource.from_url(url, loop=bot.loop)
		vc.play(player, after=lambda e:print('Player error: %s' % e) if e else None)
	await ctx.send('Now playing: {}'.format(player.title))

	if vc.is_playing():
		await ctx.send('playing!')

	vc.pause()
	vc.resume()

	await ctx.send("done")




@bot.command(name='stop', help="stop playing song")
async def stop(ctx):
	channel = ctx.message.author.voice
	if not channel:
		await ctx.send("you are not listning to me")

	vc = None
	for i in bot.voice_clients:
		if i!=None and i.channel == channel.channel:
			vc = i

	if vc.is_connected() and vc.is_playing():

		await ctx.send('ok not singing')
		await vc.disconnect()




#@bot.command(name = 'search', help="searches for a given teram in google", pass_context=True)
#async def search_google(ctx, s, top):
#	res = GoogleSearch().search(s)
#	await ctx.send(f'TOP{top} results')
#	for i in range(5):
#		await ctx.send('Title '+ res.title)
#		await ctx.send(res.content[:199])


bot.run(TOKEN)
