from telethon import TelegramClient, events

API_ID = 23825615
API_HASH = "cd2ef60a7380768e30fe5514da7143e6"

client = TelegramClient("venduti_session", API_ID, API_HASH)


@client.on(events.NewMessage(chats="@subitovendutibot"))
async def new_message_handler(event):
    print("\n" + "=" * 70)
    print("📩 NUOVO MESSAGGIO DA SUBITO VENDUTI")
    print("=" * 70)

    print(event.message.text or "[messaggio senza testo]")

    print("=" * 70)


async def main():
    print("✅ Telegram collegato")
    print("👂 In ascolto di @subitovendutibot...")
    print("⏹️ Premi CTRL+C per fermare")
    
    await client.run_until_disconnected()


client.start()
client.loop.run_until_complete(main())