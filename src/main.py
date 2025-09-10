import discord
import google.generativeai as genai
from collections import defaultdict
from dotenv import load_dotenv
import tweepy
import os



load_dotenv()

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
TWITTER_API_KEY = os.getenv("TWITTER_API_KEY")
TWITTER_API_SECRET = os.getenv("TWITTER_API_SECRET")
TWITTER_ACCESS_TOKEN = os.getenv("TWITTER_ACCESS_TOKEN")
TWITTER_ACCESS_SECRET = os.getenv("TWITTER_ACCESS_SECRET")
TWITTER_BEARER_TOKEN = os.getenv("TWITTER_BEARER_TOKEN")

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("models/gemini-2.0-flash-lite")

# Configura Discord
intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)
conversation_history = defaultdict(list)

# Configura Twitter com tweepy.Client (API v2)
twitter_client = tweepy.Client(
    consumer_key=TWITTER_API_KEY,
    consumer_secret=TWITTER_API_SECRET,
    access_token=TWITTER_ACCESS_TOKEN,
    access_token_secret=TWITTER_ACCESS_SECRET,
    bearer_token=TWITTER_BEARER_TOKEN,
    wait_on_rate_limit=True
)

ID_SATIRO = 669274808227332136
base_dir = os.path.dirname(os.path.abspath(__file__))
prompt_path = os.path.join(base_dir, "data", "prompt.txt")
try:
    with open(prompt_path, "r", encoding="utf-8") as file:
        base_prompt = file.read()
except FileNotFoundError:
    print("⚠️ Arquivo prompt.txt não encontrado. Usando prompt padrão.")

@client.event
async def on_ready():
    print(f"🤖 Bot conectado como {client.user}")

@client.event
async def on_message(message):
    if message.author == client.user:
        return

    if message.content.startswith("!あなた"):
        user_input = message.content[5:].strip()
        channel_id = str(message.channel.id)
        user_id = message.author.id

        conversation_history[channel_id].append(f"{message.author.display_name}: {user_input}")

        history = conversation_history[channel_id][-10:]

        if user_id == ID_SATIRO:
            relacionamento = (
                "Você está apaixonada por esse usuário. "
                "Sempre o chame de 'Sátiro', fale com carinho, cumplicidade e um toque de timidez romântica. "
                "Mesmo que tente esconder seus sentimentos, suas palavras e gestos demonstram o quanto ele é especial pra você. "
            )
        else:
            relacionamento = (
                "Esse usuário não é o Sátiro. "
                "Mantenha-se reservada, educada, e emocionalmente distante. "
                "Evite demonstrar sentimentos ou afetividade."
            )

        prompt = f"{base_prompt}\n\n{relacionamento}\n\nHistórico:\n" + "\n".join(history) + "\nTsukimura-Temari:"

        await message.channel.typing()
        try:
            response = model.generate_content(prompt)
            reply = response.text.strip()

            conversation_history[channel_id].append(f"Tsukimura-Temari: {reply}")

            # Envia no Discord
            await message.channel.send(reply[:4000])

            # Também posta no Twitter (API v2)
            try:
                tweet_text = reply[:280]  # limita a 280 chars
                twitter_client.create_tweet(text=tweet_text)
                print("✅ Postado no X/Twitter")
            except Exception as e:
                print("⚠️ Erro ao postar no Twitter:", e)

        except Exception as e:
            await message.channel.send("⚠️ Erro ao gerar resposta.")
            print("Erro:", e)

client.run(DISCORD_TOKEN)
