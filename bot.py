import logging
from flask import Flask, request, Response
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler, MessageHandler,
    ContextTypes, filters
)
from config import BOT_TOKEN, SUPERVISOR_CHAT_ID, WEBHOOK_URL

# Logging visivo
logging.basicConfig(format='[%(levelname)s] %(message)s', level=logging.INFO)
log = logging.getLogger(__name__)

# Stato temporaneo utenti
user_state = {}

# Flask app per webhook
flask_app = Flask(__name__)
telegram_app = Application.builder().token(BOT_TOKEN).updater(None).build()

# Comando /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("IPTV", callback_data="IPTV")],
        [InlineKeyboardButton("CALCIO LIVE", callback_data="CALCIO")],
        [InlineKeyboardButton("CINEMA E CALCIO", callback_data="CINEMA")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "Benvenuto! Procediamo con l'acquisto automatizzato, a cosa sei interessato?",
        reply_markup=reply_markup
    )
    log.info(f"Utente {update.message.from_user.id} ha avviato /start")

# Scelta servizio
async def scelta_servizio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    servizio = query.data
    user_id = query.from_user.id
    user_state[user_id] = {"servizio": servizio}

    keyboard = [
        [InlineKeyboardButton("1 mese", callback_data="1")],
        [InlineKeyboardButton("3 mesi", callback_data="3")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text("Quanti mesi vuoi acquistare?", reply_markup=reply_markup)
    log.info(f"Utente {user_id} ha selezionato il servizio: {servizio}")

# Scelta durata
async def scelta_mesi(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    mesi = query.data
    user_id = query.from_user.id

    if user_id in user_state:
        user_state[user_id]["mesi"] = mesi
        importo = "10 euro" if mesi == "1" else "25 euro"
        msg = f"Inserisci il codice del buono Amazon da {importo}:"
        await query.edit_message_text(msg)
        log.info(f"Utente {user_id} ha scelto durata: {mesi} mese/i")

# Ricezione codice
async def ricevi_codice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    codice = update.message.text
    username = update.message.from_user.username or "Nessuno username"

    if user_id in user_state:
        servizio = user_state[user_id]["servizio"]
        mesi = user_state[user_id]["mesi"]
        await update.message.reply_text("Grazie! Stiamo verificando il codice che hai inviato. Un operatore ti contatterà a breve.")

        messaggio = (
            f"👤 Utente ID: {user_id}\n"
            f"📇 Username: @{username}\n"
            f"📦 Servizio: {servizio}\n"
            f"📅 Durata: {mesi} mese/i\n"
            f"🎁 Codice Amazon: {codice}"
        )
        await context.bot.send_message(chat_id=SUPERVISOR_CHAT_ID, text=messaggio)
        log.info(f"Utente {user_id} ha inserito codice: {codice}")
        del user_state[user_id]

# Webhook endpoint
@flask_app.route('/webhook', methods=['POST'])
def webhook():
    telegram_app.update_queue.put(Update.de_json(request.get_json(force=True), telegram_app.bot))
    return Response(status=200)

# Health check
@flask_app.route('/healthcheck')
def health():
    return "OK", 200

# Avvio
async def main():
    await telegram_app.bot.set_webhook(url=WEBHOOK_URL)
    telegram_app.add_handler(CommandHandler("start", start))
    telegram_app.add_handler(CallbackQueryHandler(scelta_servizio, pattern="^(IPTV|CALCIO|CINEMA)$"))
    telegram_app.add_handler(CallbackQueryHandler(scelta_mesi, pattern="^(1|3)$"))
    telegram_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, ricevi_codice))
    await telegram_app.initialize()
    await telegram_app.start()

import asyncio
if __name__ == "__main__":
    asyncio.run(main())
    import os
    port = int(os.environ.get("PORT", 8000))
    flask_app.run(host="0.0.0.0", port=port)

