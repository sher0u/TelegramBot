# 🤖 KADER DZ Telegram Bot

Professional Telegram bot helping Algerian and Arab students study and live in Russia.

**Owner:** Youssefi Abdelkader ([@Yousfi_Abdelkader](https://t.me/Yousfi_Abdelkader))
**Website:** [kaderdz.ru](https://kaderdz.ru)

---

## ✨ Features

### For Users
- 👤 **About Me** — Full profile with stats
- 🎯 **Live Enrollment** — Currently 2026/2027 academic year
- 📑 **Services Menu** — Registration, translation, money transfer, consultation
- 🎓 **Study Information** — Why Russia, levels, languages, recognition
- 💰 **Cost Guide** — Detailed pricing for visa, tuition, housing, food
- 🏘️ **Life in Russia** — Weather, religion, safety, cities
- 📘 **Complete Guide** — Before & after arrival in Russia
- ⚠️ **Honest Section** — Real negatives explained transparently
- 📝 **Inquiry Form** — Multi-step form forwarded directly to admin
- 📞 **Direct Contact** — WhatsApp / Telegram / Website buttons
- 🌐 **Official Links** — Channel, YouTube, group chat

### For Admins
- 📊 `/stats` — User statistics
- 📤 `/broadcast <msg>` — Send plain message to all users
- 📣 `/announce <msg>` — Broadcast with Markdown formatting
- 📋 `/users` — Export all user IDs to file
- 🛡️ Role-based access via `ADMIN_IDS` env var

### Technical
- ✅ Clean modular architecture (`bot.py` / `keyboards.py` / `content.py` / `admin.py`)
- ✅ Global error handler — no crashes
- ✅ Persistent user storage (`users.json`)
- ✅ Conversation flow for inquiry form
- ✅ Smart message editing (edits existing message instead of spamming)
- ✅ Auto-load `.env` configuration
- ✅ Rate-limit protection on broadcasts
- ✅ Logging with timestamps
- ✅ Inquiry submissions auto-forwarded to admin

---

## 🚀 Setup

### 1. Clone & install

```bash
git clone https://github.com/sher0u/TelegramBot.git
cd TelegramBot
pip install -r requirements.txt
```

### 2. Configure

```bash
cp .env.example .env
nano .env   # Fill in BOT_TOKEN, ADMIN_IDS, INQUIRY_FORWARD_CHAT
```

Get your bot token from [@BotFather](https://t.me/BotFather).
Get your Telegram user ID from [@userinfobot](https://t.me/userinfobot).

### 3. Run

```bash
python bot.py
```

You should see: `🤖 KADER DZ Bot is running...`

---

## 📁 Project Structure

```
TelegramBot/
├── bot.py              # Main entry point, routing, conversation handler
├── content.py          # All text content (Arabic) — easy to edit
├── keyboards.py        # All inline keyboards
├── admin.py            # Admin commands (/admin /stats /broadcast /users)
├── user_storage.py     # Persistent user tracking
├── requirements.txt    # Python dependencies
├── start.sh            # Glitch.com startup script
├── glitch.json         # Glitch.com config
├── .env.example        # Configuration template
├── .gitignore          # Excludes secrets & cache
└── README.md           # This file
```

---

## 🎯 Available Commands

### User commands
| Command | Description |
|---------|-------------|
| `/start` | Open main menu |
| `/help` | Show all commands |
| `/about` | About Youssefi Abdelkader |
| `/contact` | Direct contact links |
| `/website` | Link to kaderdz.ru |
| `/cancel` | Cancel an in-progress inquiry form |

### Admin commands
| Command | Description |
|---------|-------------|
| `/admin` | Show admin panel |
| `/stats` | Detailed statistics |
| `/broadcast <msg>` | Send plain message to all users |
| `/announce <msg>` | Send Markdown-formatted broadcast |
| `/users` | Export all user IDs as `.txt` |

---

## 🌍 Deployment

### Glitch.com (Free)
Already configured via `glitch.json` and `start.sh`.
1. Import this repo to glitch.com
2. Add `BOT_TOKEN` to the `.env` editor in Glitch
3. The bot starts automatically.

### VPS / Server
```bash
nohup python bot.py > bot.log 2>&1 &
```

### Docker (optional)
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
CMD ["python", "bot.py"]
```

---

## 📝 Editing Content

All Arabic text lives in `content.py` — edit freely without touching logic.
All menus and buttons live in `keyboards.py`.

---

## 🔒 Security Notes

- ✅ `.env` is in `.gitignore` — never commit secrets
- ✅ `users.json` is auto-generated, also gitignored
- ✅ Admin commands require ID-based authentication
- ✅ Inquiry submissions forwarded directly to admin (not stored)
