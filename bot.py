import os
import logging
import asyncio
from flask import Flask, request, Response
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler, MessageHandler,
    ContextTypes, filters
)

# ✅ Variabili ambiente
BOT_TOKEN = os.environ["BOT_TOKEN"]
SUPERVISOR_CHAT_ID = int(os.environ["SUPERVISOR_CHAT_ID"])
WEBHOOK_URL = os.environ["WEBHOOK_URL"]

# 🎯 Logging visivo
logging.basicConfig(format='[%(levelname)s] %(message)s', level=logging.INFO)
log = logging.getLogger(__name__)

# 🗂️ Stato utente temporaneo
user_state = {}

# 🚀 Flask + Telegram App
flask_app = Flask(__name__)
telegram_app = Application.builder().token(BOT_TOKEN).updater(None).build()

# 🟢 /start
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
    log.info(f"[START] Utente {update.message.from_user.id}")

# 🟡 Scelta servizio
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
    log.info(f"[SERVIZIO] {user_id} ha scelto {servizio}")

# 🟠 Scelta durata
async def scelta_mesi(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    mesi = query.data
    user_id = query.from_user.id

    if user_id in user_state:
        user_state[user_id]["mesi"] = mesi
        importo = "10 euro" if mesi == "1" else "25 euro"
        await query.edit_message_text(f"Inserisci il codice del buono Amazon da {importo}:")
        log.info(f"[DURATA] {user_id} ha scelto {mesi} mese/i")

# 🔴 Ricezione codice
async def ricevi_codice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    codice = update.message.text
    username = update.message.from_user.username or "Nessuno username"

    if user_id in user_state:
        servizio = user_state[user_id]["servizio"]
        mesi = user_state[user_id]["mesi"]
        await update.message.reply_text("Grazie! Verifica in corso. Un operatore ti contatterà a breve.")

        messaggio = (
            f"👤 ID Utente: {user_id}\n"
            f"📇 Username: @{username}\n"
            f"📦 Servizio: {servizio}\n"
            f"📅 Durata: {mesi} mese/i\n"
            f"🎁 Codice Amazon: {codice}"
        )
        await context.bot.send_message(chat_id=SUPERVISOR_CHAT_ID, text=messaggio)
        log.info(f"[CODICE] Ricevuto da {user_id}: {codice}")
        del user_state[user_id]

# 📬 Webhook POST endpoint
@flask_app.route('/web
