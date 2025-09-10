import discord
import google.generativeai as genai
from collections import defaultdict
from dotenv import load_dotenv
import tweepy
import os
import asyncio
import random
import datetime


load_dotenv()


DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
TWITTER_API_KEY = os.getenv("TWITTER_API_KEY")
TWITTER_API_SECRET = os.getenv("TWITTER_API_SECRET")
TWITTER_ACCESS_TOKEN = os.getenv("TWITTER_ACCESS_TOKEN")
TWITTER_ACCESS_SECRET = os.getenv("TWITTER_ACCESS_SECRET")
TWITTER_BEARER_TOKEN = os.getenv("TWITTER_BEARER_TOKEN")
DISCORD_CHANNEL_ID = int(os.getenv("DISCORD_CHANNEL_ID", 0))  # Opcional

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("models/gemini-2.0-flash-lite")

intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)
conversation_history = defaultdict(list)

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
    base_prompt = (
        "Você é Tsukimura-Temari, uma personagem fictícia introspectiva, poética e misteriosa. "
        "Suas palavras são elegantes, profundas e muitas vezes carregadas de emoção e filosofia."
    )


@client.event
async def on_ready():
    print(f"🤖 Bot conectado como {client.user}")
    asyncio.create_task(auto_post_task())  


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
            await message.channel.send(reply[:4000])

        
            try:
                twitter_client.create_tweet(text=reply[:280])
                print("✅ Postado no Twitter (resposta)")
            except Exception as e:
                print("⚠️ Erro ao postar no Twitter (resposta):", e)

        except Exception as e:
            await message.channel.send("⚠️ Erro ao gerar resposta.")
            print("Erro:", e)

async def auto_post_task():
    await client.wait_until_ready()
    channel = client.get_channel(DISCORD_CHANNEL_ID) if DISCORD_CHANNEL_ID else None

    max_posts_per_day = 3
    posts_today = 0
    last_post_day = None
    while not client.is_closed():
        try:
            now = datetime.datetime.now()
            current_day = now.date()

    
            if current_day != last_post_day:
                posts_today = 0
                last_post_day = current_day

            if posts_today >= max_posts_per_day:
                print("🛑 Limite de postagens diárias atingido. Aguardando até amanhã.")
                await asyncio.sleep(3600) 
                continue
            prompt = (
                f"{base_prompt}\n\n"
                '''
              <instruction>
            Crie uma breve reflexão introspectiva e poética, como se vinda de uma personagem elegante e melancólica. O texto deve evocar sentimentos profundos, como solidão, saudade ou questionamento existencial, mas sem mencionar que está sozinha ou se dirigindo a alguém. Use no máximo 275 caracteres.
            </instruction>

            <example>
            Tsukimura-Temari: O tempo escorre entre os dedos como seda molhada — suave, inevitável. O que somos senão ecos de passos dados em corredores que já esquecemos?
            </example>

            <personality>
            Fale como Tsukimura-Temari: com elegância contida, uma tristeza sutil e sensibilidade filosófica. Cada frase deve carregar o peso do não dito, com ritmo poético e vocabulário refinado.
            </personality>
                '''
            
            )

            response = model.generate_content(prompt)
            reply = response.text.strip()

            max_tweet_length = 275
            if len(reply) > max_tweet_length:
                reply = reply[:max_tweet_length].rsplit(" ", 1)[0] + "…"

            if channel:
                await channel.send(reply[:4000])
            try:
                twitter_client.create_tweet(text=reply)
                posts_today += 1
                print(f"✅ [{now.strftime('%H:%M:%S')}] Postagem #{posts_today} feita.")
            except Exception as e:
                print("⚠️ Erro ao postar no Twitter:", e)

        except Exception as e:
            print("⚠️ Erro na geração automática:", e)

        
        wait_time = random.randint(21600, 36000)  
        next_post = now + datetime.timedelta(seconds=wait_time)
        print(f"⏳ Próxima tentativa de postagem em ~{wait_time // 3600}h ({next_post.strftime('%H:%M:%S')})")
        await asyncio.sleep(wait_time)
client.run(DISCORD_TOKEN)
