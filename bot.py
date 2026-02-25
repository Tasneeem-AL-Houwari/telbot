from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
import pandas as pd
from collections import Counter
import os

TOKEN = os.getenv("BOT_TOKEN")

messages = []

async def track_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text:
        messages.append({
            "user": update.message.from_user.full_name,
            "text": update.message.text
        })

async def analysis(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not messages:
        await update.message.reply_text("لا يوجد بيانات بعد 😅")
        return

    df = pd.DataFrame(messages)
    counts = Counter(df["user"])

    report = "📊 تحليل الجروب:\n\n"
    for user, count in counts.most_common():
        report += f"{user}: {count} رسالة\n"

    await update.message.reply_text(report)

app = ApplicationBuilder().token(TOKEN).build()

from telegram.ext import MessageHandler, filters

app.add_handler(CommandHandler("analysis", analysis))
app.add_handler(CommandHandler("start", analysis))
app.add_handler(CommandHandler("help", analysis))

# هذا السطر الجديد لقراءة كل الرسائل
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, track_messages))


app.run_polling()

