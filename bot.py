import logging
import os
import pandas as pd
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes

BOT_TOKEN = "8401109482:AAH90n3Y8iT1NBmI9hoBbBOyHWySDUzoH00"
ADMIN_IDS = [123456789]
CSV_FILE = "licences.csv"

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome_message = (
        "እንኳን ወደ የስልጤ ዞን ትራንስፖርትና መንገድ ልማት መምሪያ የመንጃ ፈቃድ ማሳወቂያ ቦት በደህና መጡ! 🚘\n\n"
        "የመንጃ ፈቃድዎ መምጣቱን ለማረጋገጥ ከሚከተሉት አንዱን ይጻፉልን፦\n"
        "1️⃣ **የመንጃ ፈቃድ ቁጥር**\n"
        "2️⃣ **ስልክ ቁጥር**\n"
        "3️⃣ **ሙሉ ስም**\n\n"
        "*(የመንጃ ፈቃድዎ የወጣበትን ዙር ጨምሮ ሙሉ መረጃውን እናሳይዎታለን)*"
    )
    if update.effective_user.id in ADMIN_IDS:
        keyboard = [[InlineKeyboardButton("📊 አጠቃላይ መረጃዎችን ለማየት", callback_data="admin_stats")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(welcome_message, reply_markup=reply_markup, parse_mode='Markdown')
    else:
        await update.message.reply_text(welcome_message, parse_mode='Markdown')

async def check_licence(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_input = update.message.text.strip().lower()
    
    if os.path.exists(CSV_FILE):
        df = pd.read_csv(CSV_FILE)
        
        # ዓምዶቹን ወደ ስትሪንግ እና ወደ ትንሽ ፊደል መቀየር
        df['licence_no'] = df['licence_no'].astype(str).str.lower()
        df['phone'] = df['phone'].astype(str).str.lower()
        df['name_lower'] = df['name'].astype(str).str.lower()
        
        # በላይሰንስ ቁጥር፣ በስልክ ቁጥር ወይም በስም መፈለግ
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
            response += "ℹ️ እባክዎ አስፈላጊውን መታወቂያ በመያዝ በመምሪያችን በአካል ቀርበው ይውሰዱ።"
        else:
            response = (
                f"❌ **መረጃው አልተገኘም!**\n\n"
                f" '{user_input}' የሚል መረጃ በወጡት ዝርዝር ውስጥ አልተገኘም።\n"
                f"እባክዎ መረጃውን በትክክል ማስገባትዎን ያረጋግጡ።"
            )
    else:
        response = "የመረጃ ቋቱ በአሁኑ ሰዓት ዝግጁ አይደለም። እባክዎ ትንሽ ቆይተው ይሞክሩ።"
        
    await update.message.reply_text(response, parse_mode='Markdown')

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data == "admin_stats" and os.path.exists(CSV_FILE):
        df = pd.read_csv(CSV_FILE)
        total_count = len(df)
        text = f"📊 **የአስተዳዳሪ ዳሽቦርድ**\n\n• በዳታቤዝ ውስጥ ያሉ ጠቅላላ የመንጃ ፈቃዶች ብዛት: **{total_count}**"
        await query.edit_message_text(text=text, parse_mode='Markdown')

def main():
    application = ApplicationBuilder().token(BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(button_handler))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, check_licence))
    application.run_polling()

if __name__ == '__main__':
    main()
