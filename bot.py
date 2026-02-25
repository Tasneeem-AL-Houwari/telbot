import os
import pandas as pd
from collections import Counter
from openai import OpenAI
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

# ====== TOKENS ======
TOKEN = os.getenv("BOT_TOKEN")
OPENAI_KEY = os.getenv("OPENAI_API_KEY")

# ====== AI CLIENT ======
client_ai = OpenAI(api_key=OPENAI_KEY)

# قائمة لتخزين الرسائل مؤقتاً (ستضيع عند إعادة تشغيل ريندر)
messages_store = []

def ask_ai(context_text):
    try:
        response = client_ai.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system", 
                    "content": "أنت عضو ذكي ومرح في جروب تلجرام. رد بشكل طبيعي ومختصر. استخدم اللهجة العامية أحياناً."
                },
                {"role": "user", "content": context_text}
            ],
            temperature=0.8,
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"OpenAI Error: {e}")
        return "عذراً، عقلي مشتت قليلاً الآن! 🧠💨"

# ====== التحليل ======
async def analysis(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not messages_store:
        await update.message.reply_text("لا يوجد بيانات كافية للتحليل بعد 📊")
        return

    df = pd.DataFrame(messages_store)
    counts = Counter(df["user"])
    
    report = "📊 **أكثر المتفاعلين في الجروب:**\n\n"
    for user, count in counts.most_common(5):
        report += f"👤 {user}: {count} رسالة\n"
    
    await update.message.reply_text(report, parse_mode="Markdown")

# ====== المعالج الرئيسي للرسائل ======
# قائمة مؤقتة في الذاكرة للتجربة فوراً
temp_messages = []

async def handle_main(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return

    user_name = update.message.from_user.full_name
    text = update.message.text
    
    # حفظ في الذاكرة المؤقتة للتحليل
    temp_messages.append({"user": user_name, "text": text})
    save_message(user_name, text) # سيحاول الحفظ في القاعدة أيضاً

    # الحصول على يوزر البوت
    bot_info = await context.bot.get_me()
    bot_username = bot_info.username.lower()

    # شروط الرد (إذا ناداه أحد، أو رد عليه، أو حتى إذا كتب كلمة "بوت")
    is_reply_to_bot = (update.message.reply_to_message and 
                        update.message.reply_to_message.from_user.id == bot_info.id)
    is_mentioned = (f"@{bot_username}" in text.lower() or 
                    "بوت" in text or 
                    "يا ذكي" in text)

    if is_reply_to_bot or is_mentioned:
        # إظهار أن البوت "يكتب الآن" ليعطيك شعور بالتفاعل
        await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
        
        # سياق بسيط من آخر الرسائل في الذاكرة
        context_text = "\n".join([f"{m['user']}: {m['text']}" for m in temp_messages[-5:]])
        
        try:
            ai_response = ask_ai(context_text)
            await update.message.reply_text(ai_response)
        except Exception as e:
            print(f"Error calling AI: {e}")
            await update.message.reply_text("عقلي توقف عن التفكير فجأة! 🤯")

# ====== APP SETUP ======
app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("analysis", analysis))
# هاندلر واحد لكل الرسائل النصية
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_all_messages))

print("البوت يعمل الآن...")
app.run_polling()

