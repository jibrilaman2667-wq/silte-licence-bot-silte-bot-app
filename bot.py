import logging
import os
import pandas as pd
from docx import Document
from flask import Flask
from threading import Thread
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes

BOT_TOKEN = "8401109482:AAH90n3Y8iT1NBmI9hoBbBOyHWySDUzoH00"  # የቦት ቶከንዎ
ADMIN_IDS = [123456789]  # የራስዎን የቴሌግራም ID እዚህ ያስገቡ
CHANNEL_USERNAME = "@https://t.me/SilteiZoneTransportRoad14"  # የቴሌግራም ቻናልዎ ዩዘርናም (በ @ ይጻፉ)

EXCEL_FILE = "licences.xlsx"
WORD_FILE = "licences.docx"

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# Flask ሰርቨር ለ Render ፖርት ክፍት እንዲሆን
app_flask = Flask(__name__)

@app_flask.route('/')
def home():
    return "Silte Transport Bot is running!"

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app_flask.run(host="0.0.0.0", port=port)

# ሁለቱንም ፋይሎች (Excel እና Word) አንብቦ በአንድ ላይ የሚያቀላቅል ፊንክሽን
def load_all_data():
    all_dfs = []
    
    if os.path.exists(EXCEL_FILE):
        try:
            df_excel = pd.read_excel(EXCEL_FILE, dtype=str)
            all_dfs.append(df_excel)
        except Exception as e:
            logging.error(f"Excel reading error: {e}")
            
    if os.path.exists(WORD_FILE):
        try:
            doc = Document(WORD_FILE)
            word_data = []
            for table in doc.tables:
                for row in table.rows[1:]:
                    row_data = [cell.text.strip() for cell in row.cells]
                    word_data.append(row_data)
            if word_data:
                df_word = pd.DataFrame(word_data, columns=['licence_no', 'name', 'phone', 'category', 'round', 'status'])
                all_dfs.append(df_word)
        except Exception as e:
            logging.error(f"Word reading error: {e}")
            
    if all_dfs:
        combined_df = pd.concat(all_dfs, ignore_index=True)
        return combined_df
    return pd.DataFrame()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome_message = (
        "እንኳን ወደ የስልጤ ዞን ትራንስፖርትና መንገድ ልማት መምሪያ የመንጃ ፈቃድ ማሳወቂያ ቦት በደህና መጡ! 🚘\n\n"
        "የመንጃ ፈቃድዎ መምጣቱን ለማረጋገጥ ከሚከተሉት **አንድ መረጃ** ብቻ በመምረጥ ይጻፉልን፦\n"
        "1️⃣ **የመንጃ ፈቃድ ቁጥር**\n"
        "2️⃣ **ስልክ ቁጥር**\n"
        "3️⃣ **ሙሉ ስም**\n\n"
        "*(የፈቃድዎ ሁኔታ፣ የደረጃ ዓይነት እና የመጣበት ዙር በዝርዝር ይነገርዎታል)*"
    )
    
    bot_username = "Siltetransportlicencebot"  # የቦትዎ ዩዘርናም
    channel_link = f"https://t.me/{CHANNEL_USERNAME.replace('@', '')}"

    if update.effective_user.id in ADMIN_IDS:
        keyboard = [
            # 🟢 የቻናሉ ሊንክ ከላይ እንዲሆን ተደርጓል
            [InlineKeyboardButton("📢 ቻናላችንን ጆይን ለማድረግ (Join)", url=channel_link)],
            [InlineKeyboardButton("➕ Add me to your group", url=f"https://t.me/{bot_username}?startgroup=true")],
            [InlineKeyboardButton("↗️ Add me to your channel", url=f"https://t.me/{bot_username}?startchannel=true")],
            [InlineKeyboardButton("📊 አጠቃላይ መረጃዎችን ለማየት", callback_data="admin_stats")],
            [InlineKeyboardButton("📢 አዲሱን ዙር ወደ ቻናል ለመልቀቅ", callback_data="send_to_channel")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(welcome_message, reply_markup=reply_markup, parse_mode='Markdown')
    else:
        keyboard = [
            # 🟢 የቻናሉ ሊንክ ከላይ እንዲሆን ተደርጓል
            [InlineKeyboardButton("📢 ቻናላችንን ጆይን ለማድረግ (Join)", url=channel_link)],
            [InlineKeyboardButton("➕ Add me to your group", url=f"https://t.me/{bot_username}?startgroup=true")],
            [InlineKeyboardButton("↗️ Add me to your channel", url=f"https://t.me/{bot_username}?startchannel=true")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(welcome_message, reply_markup=reply_markup, parse_mode='Markdown')

async def check_licence(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_input = update.message.text.strip().lower()
    
    df = load_all_data()
    
    if not df.empty:
        df['licence_no'] = df['licence_no'].fillna('').astype(str).str.strip().str.lower()
        df['phone'] = df['phone'].fillna('').astype(str).str.strip().str.lower()
        df['name'] = df['name'].fillna('').astype(str).str.strip()
        df['name_lower'] = df['name'].str.lower()
        
        result = df[
            (df['licence_no'] == user_input) | 
            (df['phone'] == user_input) | 
            (df['name_lower'].str.contains(user_input))
        ]
        
        if not result.empty:
            response = "✅ **የተገኙ የመንጃ ፈቃድ መረጃዎች:**\n\n"
            for index, data in result.iterrows():
                row_number = index + 1
                response += (
                    f"📌 **ተራ ቁጥር (በሰንጠረዥ):** {row_number}\n"
                    f"👤 **ስም:** {data['name']}\n"
                    f"የመንጃ ፈቃድ ቁጥር: `{data['licence_no']}`\n"
                    f"📞 **ስልክ ቁጥር:** {data['phone']}\n"
                    f"🚗 **የመንጃ ፈቃድ ደረጃ:** {data['category']}\n"
                    f"🔢 **የመጣበት ዙር:** {data['round']}\n"
                    f"📌 **ሁኔታ:** {data['status']}\n\n"
                    f"------------------------\n"
                )
            response += "ℹ️ እባክዎ አስፈላጊ መረጃዎችን በመያዝ በመምሪያችን በአካል ቀርበው ይውሰዱ።"
        else:
            response = (
                f"❌ **መረጃው አልተገኘም!**\n\n"
                f" '{user_input}' የሚል መረጃ በመጡት ዝርዝር ውስጥ አልተገኘም።\n\n"
                f"እባክዎ መረጃውን በትክክል ማስገባትዎን ያረጋግጡ።"
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

    df = load_all_data()
    if query.data == "admin_stats" and not df.empty:
        total_count = len(df)
        text = f"📊 **የአስተዳዳሪ ዳሽቦርድ**\n\n• በዳታቤዝ ውስጥ ያሉ ጠቅላላ የመንጃ ፈቃዶች ብዛት: **{total_count}**"
        await query.edit_message_text(text=text, parse_mode='Markdown')
        
    elif query.data == "send_to_channel" and not df.empty:
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
            await query.edit_message_text(text=f"❌ መላክ አልተቻለም። ስህተት: {e}")

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
