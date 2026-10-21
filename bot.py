import logging
import os
import pandas as pd
from flask import Flask
from threading import Thread
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes

BOT_TOKEN = "8401109482:AAH90n3Y8iT1NBmI9hoBbBOyHWySDUzoH00"
ADMIN_IDS = [123456789]  # <-- የራስዎን የቴሌግራም ID እዚህ ያስገቡ
CHANNEL_USERNAME = "@https://t.me/SilteiZoneTransportRoad14"  # <-- የቴሌግራም ቻናልዎ ዩዘርናም (ምሳሌ: @Siltetransport)
CSV_FILE = "licences.csv"

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# Flask ሰርቨር ለ Render ፖርት ክፍት እንዲሆን
app_flask = Flask(__name__)

@app_flask.route('/')
def home():
    return "Silte Transport Bot is running!"

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app_flask.run(host="0.0.0.0", port=port)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome_message = (
        "እንኳን ወደ የስልጤ ዞን ትራንስፖርትና መንገድ ልማት መምሪያ የመንጃ ፈቃድ ማሳወቂያ ቦት በደህና መጡ! 🚘\n\n"
        "የመንጃ ፈቃድዎ መምጣቱን ለማረጋገጥ ከሚከተሉት **አንድ መረጃ** ብቻ በመምረጥ ይጻፉልን፦\n"
        "1️⃣ **የመንጃ ፈቃድ ቁጥር** (ምሳሌ፦ 10-00001 ወይም 12345)\n"
        "2️⃣ **ስልክ ቁጥር** (ምሳሌ፦ 0911121314)\n"
        "3️⃣ **ሙሉ ስም** (ምሳሌ፦ አህመድ ሀሰን)\n\n"
        "*(የፈቃድዎ ሁኔታ፣ የደረጃ ዓይነት እና የወጣበት ዙር በዝርዝር ይነገርዎታል)*"
    )
    if update.effective_user.id in ADMIN_IDS:
        keyboard = [
            [InlineKeyboardButton("📊 አጠቃላይ መረጃዎችን ለማየት", callback_data="admin_stats")],
            [InlineKeyboardButton("📢 አዲሱን ዙር ወደ ቻናል ለመልቀቅ", callback_data="send_to_channel")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(welcome_message, reply_markup=reply_markup, parse_mode='Markdown')
    else:
        await update.message.reply_text(welcome_message, parse_mode='Markdown')

async def check_licence(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_input = update.message.text.strip().lower()
    
    if os.path.exists(CSV_FILE):
        df = pd.read_csv(CSV_FILE)
        df['licence_no'] = df['licence_no'].astype(str).str.lower()
        df['phone'] = df['phone'].astype(str).str.lower()
        df['name_lower'] = df['name'].astype(str).str.lower()
        
        result = df[
            (df['licence_no'] == user_input) | 
            (df['phone'] == user_input) | 
            (df['name_lower'].str.contains(user_input))
        ]
        
        if not result.empty:
            response = "✅ **የተገኙ የመንጃ ፈቃድ መረጃዎች:**\n\n"
            for index, data in result.iterrows():
                response += (
                    f"👤 **ስም:** {data['name']}\n"
                    f"ሹፌር/የፈቃድ ቁጥር: `{data['licence_no']}`\n"
                    f"📞 **ስልክ ቁጥር:** {data['phone']}\n"
                    f"🚗 **የመንጃ ፈቃድ ደረጃ:** {data['category']}\n"
                    f"🔢 **የወጣበት ዙር:** {data['round']}\n"
                    f"📌 **ሁኔታ:** {data['status']}\n\n"
                    f"------------------------\n"
                )
            response += "ℹ️ እባክዎ አስፈላጊ መረጃዎችን በመያዝ በመምሪያችን በአካል ቀርበው ይውሰዱ።"
        else:
            response = (
                f"❌ **መረጃው አልተገኘም!**\n\n"
                f" '{user_input}' የሚል መረጃ በወጡት ዝርዝር ውስጥ አልተገኘም።\n\n"
                f"እባክዎ መረጃውን በትክክል ማስገባትዎን ያረጋግጡ (የፈቃድ ቁጥር፣ ስልክ ቁጥር ወይም ሙሉ ስም በመጠቀም መፈለግ ይችላሉ)።"
            )
    else:
        response = "የመረጃ ቋቱ በአሁኑ ሰዓት ዝግጁ አይደለም። እባክዎ ትንሽ ቆይተው ይሞክሩ።"
        
    await update.message.reply_text(response, parse_mode='Markdown')

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if query.from_user.id not in ADMIN_IDS:
        await query.edit_message_text(text="❌ ይህንን ትእዛዝ ለመፈጸም ፈቃድ አልዎትም!")
        return

    if query.data == "admin_stats" and os.path.exists(CSV_FILE):
        df = pd.read_csv(CSV_FILE)
        total_count = len(df)
        text = f"📊 **የአስተዳዳሪ ዳሽቦርድ**\n\n• በዳታቤዝ ውስጥ ያሉ ጠቅላላ የመንጃ ፈቃዶች ብዛት: **{total_count}**"
        await query.edit_message_text(text=text, parse_mode='Markdown')
        
    elif query.data == "send_to_channel" and os.path.exists(CSV_FILE):
        df = pd.read_csv(CSV_FILE)
        if df.empty:
            await query.edit_message_text(text="❌ ዳታቤዙ ባዶ ነው!")
            return
            
        latest_round = df['round'].iloc[-1]
        latest_data = df[df['round'] == latest_round]
        
        channel_message = f"📢 **አዲስ የመንጃ ፈቃድ ማሳወቂያ ({latest_round})** 🚗\n\n"
        channel_message += f"የስልጤ ዞን ትራንስፖርትና መንገድ ልማት መምሪያ ያወጣውን የ{latest_round} የመንጃ ፈቃድ ማስታወሻ ከዚህ በታች እንገልፃለን።\n\n"
        channel_message += f"👥 **አጠቃላይ የተለቀቁ ብዛት:** {len(latest_data)} ሰዎች\n\n"
        channel_message += "የፈቃድዎን ሁኔታ ለማረጋገጥ ቦታችንን ይጠቀሙ 👉 @Siltetransportlicencebot\n\n"
        channel_message += "ℹ️ እባክዎ አስፈላጊ መረጃዎችን በመያዝ በመምሪያችን በአካል ቀርበው ይውሰዱ።"
        
        try:
            await context.bot.send_message(chat_id=CHANNEL_USERNAME, text=channel_message, parse_mode='Markdown')
            await query.edit_message_text(text="✅ ማስታወሻው ወደ ቴሌግራም ቻናልዎ በተሳካ ሁኔታ ተልኳል!")
        except Exception as e:
            await query.edit_message_text(text=f"❌ መላክ አልተቻለም። ቦቱ አድሚን መሆኑን እና ዩዘርናሙ ትክክል መሆኑን ያረጋግጡ።\nስህተት: {e}")

def main():
    t = Thread(target=run_flask)
    t.start()

    application = ApplicationBuilder().token(BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(button_handler))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, check_licence))
    application.run_polling()

if __name__ == '__main__':
    main()
