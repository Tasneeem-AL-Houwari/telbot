from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)
import pandas as pd
from collections import Counter
import os
from openai import OpenAI

# ====== TOKENS ======
TOKEN = os.getenv("BOT_TOKEN")
OPENAI_KEY = os.getenv("OPENAI_API_KEY")

# ====== AI CLIENT ======
client_ai = OpenAI(api_key=OPENAI_KEY)

def ask_ai(context_text):
    response = client_ai.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": "أنت عضو ذكي في جروب تلجرام. رد بشكل طبيعي، مختصر، وذكي حسب سياق النقاش. لا تكن رسميًا جدًا."
            },
            {"role": "user", "content": context_text}
        ],
        temperature=0.8,
    )

    return response.choices[0].message.content


# ====== STORAGE ======
messages = []


# ====== TRACK MESSAGES ======
async def track_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message and update.message.text:
        messages.append({
            "user": update.message.from_user.full_name,
            "text": update.message.text
        })


# ====== ANALYSIS COMMAND ======
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


# ====== SMART AI REPLY ======
async def smart_reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return

    bot_username = context.bot.username.lower()
    text = update.message.text.lower()

    # يرد فقط إذا تم مناداته أو الرد عليه
    if (
        bot_username in text
        or update.message.reply_to_message
    ):
        # جمع آخر 20 رسالة كسياق
        chat_id = update.effective_chat.id
        history = []

        async for msg in context.bot.get_chat(chat_id).get_history(limit=20):
            if msg.text:
                history.append(f"{msg.from_user.full_name}: {msg.text}")

        conversation = "\n".join(history)

        try:
            ai_response = ask_ai(conversation)
            await update.message.reply_text(ai_response)
        except Exception as e:
            await update.message.reply_text("صار خطأ بسيط بالذكاء الاصطناعي 😅")


# ====== APP SETUP ======
app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("analysis", analysis))

# تخزين كل الرسائل
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, track_messages))

# الرد الذكي
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, smart_reply))

app.run_polling()
