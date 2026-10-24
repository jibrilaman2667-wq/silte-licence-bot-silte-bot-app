import logging
import os
import pandas as pd
from docx import Document
from flask import Flask
from threading import Thread
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes

BOT_TOKEN = "8401109482:AAEgy1f_fAOi2m0tLSt8QKzR5VV5PGQVIFM"  # የቦት ቶከንዎ
ADMIN_IDS = [-1001784521352]  # የራስዎን የቴሌግራም ID እዚህ ያስገቡ
CHANNEL_USERNAME = "@SilteiZoneTransportRoad14"  # የቴሌግራም ቻናልዎ ዩዘርናም (በ @ ይጻፉ)

EXCEL_FILE = "licences.xlsx"
WORD_FILE = "licences.docx"

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

app_flask = Flask(__name__)

@app_flask.route('/')
def home():
    return "Silte Transport Bot is running!"

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app_flask.run(host="0.0.0.0", port=port)

def load_all_data():
    all_dfs = []
    
    if os.path.exists(EXCEL_FILE):
        try:
            df_excel = pd.read_excel(EXCEL_FILE, dtype=str)
            
            # ዓምዶቹን በቁጥር (Index) በመውሰድ ስህተትን በቋሚነት ማስወገድ
            # የኤክሰሉ ቅደም ተከተል: 1=licence_no, 2=name, 3=phone, 4=category, 5=round
            cols = df_excel.columns.tolist()
            new_columns = ['id', 'licence_no', 'name', 'phone', 'category', 'round']
            
            # ካሉት ዓምዶች ብዛት ጋር በማስተካከል መሰየም
            rename_dict = {}
            for i, col in enumerate(cols):
                if i == 1:
                    rename_dict[col] = 'licence_no'
                elif i == 2:
                    rename_dict[col] = 'name'
                elif i == 3:
                    rename_dict[col] = 'phone'
                elif i == 4:
                    rename_dict[col] = 'category'
                elif i == 5:
                    rename_dict[col] = 'round'
                    
            df_excel = df_excel.rename(columns=rename_dict)
            
            # ስታተስ ዓምድ ከሌለ ባዶ መፍጠር
            if 'status' not in df_excel.columns:
                df_excel['status'] = ''
                
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
    
    channel_link = f"https://t.me/{CHANNEL_USERNAME.replace('@', '')}"

    keyboard = [
        [InlineKeyboardButton("📢 ቻናላችንን ጆይን ለማድረግ (Join)", url=channel_link)]
    ]
    
    if update.effective_user.id in ADMIN_IDS:
        keyboard.append([InlineKeyboardButton("📊 አጠቃላይ መረጃዎችን ለማየት", callback_data="admin_stats")])
        keyboard.append([InlineKeyboardButton("📢 አዲሱን ዙር ወደ ቻናል ለመልቀቅ", callback_data="send_to_channel")])

    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(welcome_message, reply_markup=reply_markup, parse_mode='Markdown')

async def check_licence(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_input = update.message.text.strip().lower()
    
    df = load_all_data()
    
    if not df.empty:
        # አስፈላጊ ዓምዶች መኖራቸውን ማረጋገጥ
        for col in ['licence_no', 'phone', 'name', 'status']:
            if col not in df.columns:
                df[col] = ''
                
        df['licence_no'] = df['licence_no'].fillna('').astype(str).str.strip().str.lower()
        df['phone'] = df['phone'].fillna('').astype(str).str.strip().str.lower()
        df['name'] = df['name'].fillna('').astype(str).str.strip()
        df['name_lower'] = df['name'].str.lower()
        df['status_lower'] = df['status'].fillna('').astype(str).str.strip().str.lower()
        
        result = df[
            (df['licence_no'] == user_input) | 
            (df['phone'] == user_input) | 
            (df['name_lower'].str.contains(user_input))
        ]
        
        if not result.empty:
            response = ""
            for index, data in result.iterrows():
                row_number = index + 1
                status_text = data['status'].strip() if pd.notna(data['status']) else ""
                status_lower = status_text.lower()
                
                if "ምርመራ" in status_lower or "ሪማርክ" in status_lower:
                    response += (
                        f"❌ **የመንጃ ፈቃድዎ አልመጣም!**\n\n"
                        f"👤 **ስም:** {data['name']}\n"
                        f"🔢 **የመንጃ ፈቃድ ቁጥር:** `{data['licence_no']}`\n"
                        f"🔴 **ሁኔታ:** 🛑 ቀይ ተደርጓል (አልመጣም)\n"
                        f"📝 **ምክንያት/ሪማርክ:** {status_text}\n\n"
                        f"ℹ️ እባክዎ ተጨማሪ መረጃ ለማግኘት በአካል ቀርበው ያመልክቱ።\n"
                        f"------------------------\n"
                    )
                else:
                    category_val = data['category'] if pd.notna(data['category']) and str(data['category']).strip() != 'nan' else "ተገልጿል"
                    round_val = data['round'] if pd.notna(data['round']) else "1ኛ"
                    
                    response += (
                        f"✅ **የመንጃ ፈቃድዎ መጥቷል!**\n\n"
                        f"📌 **ተራ ቁጥር:** {row_number}\n"
                        f"👤 **ስም:** {data['name']}\n"
                        f"🔢 **የመንጃ ፈቃድ ቁጥር:** `{data['licence_no']}`\n"
                        f"🔄 **የመጣበት ዙር:** {round_val}\n"
                        f"🚗 **የመንጃ ፈቃድ ደረጃ:** {category_val}\n\n"
                        f"ℹ️ እባክዎ አስፈላጊ መረጃዎችን በመያዝ በመምሪያችን በአካል ቀርበው ይውሰዱ።\n"
                        f"------------------------\n"
                    )
        else:
            response = "እባክዎ የመንጃ ፈቃድዎ አልመጣም፤ ካስገቡ ከቆየ በአካል ቀርበው ያመልክቱ።"
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
        latest_round = df['round'].iloc[-1] if 'round' in df.columns else "1ኛ"
        latest_data = df[df['round'] == latest_round] if 'round' in df.columns else df
        
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
