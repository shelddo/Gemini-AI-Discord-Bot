from google import genai
from google.genai import types
from google.oauth2 import service_account
import os
from dotenv import load_dotenv
from discord.ext import commands, tasks
import discord
import asyncio

import discord.ext
load_dotenv()

# BOT AND GOOGLE API KEYS
BOT_TOKEN = os.environ.get("BOT_TOKEN") 
GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY") 

# BOT CONFIGURATION
MODEL = "gemini-3.1-flash-lite"
BOT_NAME = "Cleber"
BOT_INSTRUCTIONS = f'Seu nome é {BOT_NAME}, você é um bot do Discord, você foi feito apenas para conversar com as pessoas,' \
" então responda-as num linguajar mais xulo e casual, usando gírias e palavrões (NA MEDIDA). Evite disseminar ódio gratuito e discursos de ódio."
CHANNEL_ID = 1019366631488634922 # PREDEFINED CHANNEL ID, CHANGES WHEN SOMEONE TALKS TO THE BOT

startConvo = False # checks if the bot is chatting or not

print(f"Discord.py version: {discord.__version__}")


## Bot initialization

intents = discord.Intents.all()
intents.message_content = True
client = commands.Bot(command_prefix='!', intents=intents)
client.activity = discord.Activity(type=discord.ActivityType.watching, name="o chat")

@client.event
async def on_ready():
    print(f'Logado como {client.user}')

## Bot initialization end

## Bot tools (commands that the bot can execute)

def kickUser(guild_id:int, requesting_user:int, target_id:int, really:bool=False):
    if really == False:
        return "Para continuar, necessário que o úsuario que solicitou confirme a operação, pergunte se ele tem certeza e execute o comando."
    else:
        asyncio.create_task(kick(int(guild_id), int(requesting_user), int(target_id), really))

def deleteTextChannel(channel_id:int):
    print(channel_id)
    asyncio.create_task(textChannelDelete(int(channel_id)))

def createTextChannel(server_id:int, nome_canal:str):
    print(f"Criou canal {nome_canal}, no servidor de id {server_id}")
    print(server_id)
    asyncio.create_task(textChannelCreate(int(server_id), nome_canal))

def clearMsgs(amount:int=5):
    ctx = client.get_channel(CHANNEL_ID)
    asyncio.create_task(clear(ctx, amount))

def stopConversation():
    global startConvo
    print("Conversa encerrada por solicitação do usuário.")
    startConvo = False
    count.cancel()

## Bot tools end

## Discord commands

@client.event
@commands.has_permissions(kick_members=True)
async def kick(guild_id, requesting_user:int, target_id, confirmation):
    print("O usuário a ser kickado é: ", target_id)
    print("O usuário solicitando é: ", requesting_user)
    print("O id do servidor é: ", guild_id)
    guild = client.get_guild(guild_id)
    print("O nome do servidor é: ", guild)
    print("Tem certeza? ", confirmation)
    target_member = guild.get_member(target_id)
    requesting_member = guild.get_member(requesting_user)
    print("Nome do usuário a ser banido: ", target_member)
    print("Nome do usuário solicitando banimento: ", requesting_member)
    print(requesting_member.guild_permissions.kick_members)
    # add kick functionality    

@client.event
async def textChannelCreate(id, name):
    guild = client.get_guild(id)
    print(guild)
    await guild.create_text_channel(name)

@client.event
async def textChannelDelete(id):
    channel = client.get_channel(id)
    print(channel)
    await channel.delete()

@client.command()
async def clear(ctx, amount):
    print("ctx: ", ctx)
    amount+=1
    await ctx.purge(limit=int(amount))

## Discord commands end

## Conversation timer

def startConvoTimer():
    count.start()

def resetConvoTimer():
    count.restart()


""" def stopConvo():
    global startConvo
    print("Conversa encerrada por solicitação do usuário.")
    startConvo = False
    count.cancel() """

@tasks.loop(seconds=30.0, count=2)
async def count():
    if count.current_loop == 0:
        return
    
    global startConvo
    global CHANNEL_ID
    print("O bot não está mais escutando.")
    startConvo = False
    CHANNEL_ID = 0
    count.cancel()

## Conversation timer end

## Gemini API initialization

model = genai.Client(api_key=GOOGLE_API_KEY)

chat = model.chats.create(
    model=MODEL,
    config=types.GenerateContentConfig(
        safety_settings=[
            types.SafetySetting(
                category=types.HarmCategory.HARM_CATEGORY_HARASSMENT,
                threshold=types.HarmBlockThreshold.OFF
            ),
            types.SafetySetting(
                category=types.HarmCategory.HARM_CATEGORY_HATE_SPEECH,
                threshold=types.HarmBlockThreshold.OFF
            ),
            types.SafetySetting(
                category=types.HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT,
                threshold=types.HarmBlockThreshold.OFF
            ),
            types.SafetySetting(
                category=types.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT,
                threshold=types.HarmBlockThreshold.OFF
            ),
        ],
        tools=[clearMsgs, createTextChannel, deleteTextChannel, kickUser, stopConversation]
    ),    
    history=[],
)

## Gemini API initialization end

## Main bot loop

@client.event
async def on_message(message):
    global BOT_INSTRUCTIONS
    global startConvo
    global CHANNEL_ID
    if message.author == client.user:
        return
    print(message.author, message.content)
    
    if startConvo == False:
        if message.content.startswith('cleber'):
            CHANNEL_ID = message.channel.id
            startConvo = True
            if count.is_running():
                count.cancel()
            startConvoTimer()

    if startConvo == True and message.channel.id == CHANNEL_ID:
        resetConvoTimer()
        async with message.channel.typing():            
            informations = f"O nome da pessoa que mandou mensagem agora é '{message.author.name}', seu id é '{message.author.id}', esse servidor tem o id '{message.guild.id}'. Ao responder a mensagem, ignore tudo isso, use essas informações apenas para comandos específicos, não para respostas."
            print(informations)
            print("-"*80)
            # AI response
            response = chat.send_message(BOT_INSTRUCTIONS + informations + message.content)                
            channel = client.get_channel(CHANNEL_ID)        
            BOT_INSTRUCTIONS = ""
            if response.prompt_feedback != None:
                print(response.prompt_feedback)
                response.prompt_feedback
            await channel.send(f"<@{message.author.id}> {response.text}")
    elif startConvo == True and message.channel.id != CHANNEL_ID and message.content.startswith('cleber'):
        channel = client.get_channel(message.channel.id)
        await channel.send(f"<@{message.author.id}> Perai, parça. To falando com outro mano em outro canal, agora não dá não.")

client.run(BOT_TOKEN)