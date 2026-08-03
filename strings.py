"""All user-facing Amharic text for the bot, in one place."""

WELCOME = (
    "👋 እንኳን ወደ ጋራ ራይድ በደህና መጡ!\n\n"
    "በአንድ አቅጣጫ የሚጓዙ ሹፌሮች ነጻ መቀመጫ ይለጥፋሉ — እርስዎ ይመርጣሉ፣ "
    "ቦታ ይይዛሉ፣ ዋጋውንም ይካፈላሉ። እስከ 60% ይቆጥባሉ።\n\n"
    "ምን ማድረግ ይፈልጋሉ?"
)

BTN_POST = "🚙 መንገድ ልለጥፍ (ሹፌር)"
BTN_FIND = "🙋 መንገድ ልፈልግ (ተጓዥ)"
BTN_APP = "📱 ሚኒ አፑን ክፈት"
BTN_HOME = "🏠 ዋና ገጽ"
BTN_BACK = "← ተመለስ"
BTN_BOOK = "✅ ቦታ ልያዝ"
BTN_CONFIRM = "✅ አረጋግጥ"
BTN_CANCEL = "❌ ሰርዝ"
BTN_POST_AGAIN = "🚙 ሌላ መንገድ ልለጥፍ"
BTN_MY_BOOKINGS = "🎫 የእኔ ቦታዎች"
BTN_MY_RIDES = "🚗 የእኔ መንገዶች"
BTN_SKIP = "ዝለል"

CHOOSE_DIRECTION = "🧭 አቅጣጫ ይምረጡ 👇"
CHOOSE_FROM = "📍 መነሻ መቆሚያ ይምረጡ 👇"
CHOOSE_TO = "🏁 መድረሻ መቆሚያ ይምረጡ 👇"
CHOOSE_TIME = "🕐 መኪናው መቼ ይነሣል?"
CHOOSE_SEATS = "💺 ስንት ነጻ መቀመጫ አለዎት?"
CHOOSE_RIDE = "🚗 የሚሄድበትን መንገድ ያልፋል — መኪና ይምረጡ 👇"

ASK_CAR = (
    "🚙 የመኪናዎን አይነትና የሰሌዳ ቁጥር ይጻፉ\n"
    "(ለምሳሌ፦ Corolla 3-AA 12345)\n\n"
    "ተጓዦች መኪናዎን እንዲለዩ ይረዳቸዋል።"
)

CONFIRM_POST = (
    "📋 መንገድዎን ያረጋግጡ\n\n"
    "🛣 መንገድ፦ {from_name} → {to_name}\n"
    "🕐 መነሻ፦ {time}\n"
    "💺 ነጻ መቀመጫ፦ {seats}\n"
    "🚙 መኪና፦ {car}\n"
    "💵 ዋጋ በአንድ መቀመጫ፦ {fare} ብር ከመቆሚያ እስከ መቆሚያ ይለያያል\n\n"
    "(ተጓዥ ብቻውን ቢጓዝ {solo} ብር ይከፍል ነበር)"
)

POSTED = (
    "✅ መንገድዎ ተለጥፏል!\n\n"
    "ተጓዦች በማንኛውም መቆሚያ መጫን ይችላሉ — ቦታ ሲይዙ እናሳውቅዎታለሁ። መልካም ጉዞ! 🚗"
)

NO_RIDES = (
    "😕 በዚህ መንገድ ላይ ገና ምንም መኪና የለም።\n"
    "ሌላ መቆሚያ ወይም አቅጣጫ ይሞክሩ።"
)

RIDE_LINE = "🕐 {time} · {ride_from} → {ride_to} · {left} ቀሪ · {fare} ብር"

RIDE_DETAILS = (
    "🚗 {driver}\n"
    "🚙 {car}\n"
    "⭐ {rating}\n\n"
    "🛣 የመኪናው መንገድ፦ {ride_from} → {ride_to}\n"
    "📍 የእርስዎ፦ {seg_from} → {seg_to}\n"
    "🕐 መነሻ፦ {time}\n"
    "💺 ቀሪ መቀመጫ፦ {left}/{total}\n"
    "💵 የእርስዎ ዋጋ፦ {fare} ብር\n"
    "💰 ቁጠባ፦ {save} ብር (ብቻዎን {solo} ብር ይከፍላሉ ነበር)"
)

BOOKED = (
    "🎉 ቦታዎ ተያዟል!\n\n"
    "🎫 ኮድ፦ {code}\n"
    "🚗 ሹፌር፦ {driver} — {phone}\n"
    "🕐 {time} በ{from_name} ይጠብቁ።\n\n"
    "💳 ክፍያ፦ {fare} ብር በቴሌብር ለሹፌሩ ቁጥር ({phone}) ይላኩ።\n"
    "(ለማሳየት ብቻ — እውነተኛ ክፍያ አይደለም)"
)

RIDE_FULL = "😕 ይቅርታ — ይህ መኪና ሙሉ ሞልቷል። ሌላ ይምረጡ።"
CANCELLED = "ተሰርዟል።"

MY_BOOKINGS_EMPTY = "🎫 ገና ቦታ አልያዙም።\n«መንገድ ልፈልግ» ብለው መኪና ይምረጡ!"
BOOKING_LINE = "🎫 {code} · {time} · {from_name} → {to_name} · {fare} ብር"
BOOKING_CANCELLED = "✅ ቦታዎ ({code}) ተሰርዟል። መቀመጫው ለሌላ ተጓዥ ክፍት ሆኗል።"

MY_RIDES_EMPTY = "🚗 ገና መንገድ አልለጠፉም።\n«መንገድ ልለጥፍ» ብለው ነጻ መቀመጫዎን ያካፈሉ!"
MY_RIDE_LINE = (
    "🕐 {time} · {from_name} → {to_name}\n"
    "💺 ተጓዦች፦ {taken}/{total}{riders}"
)
RIDE_CANCELLED = "✅ መንገዱ ({time} {from_name} → {to_name}) ተሰርዟል። ተጓዦች ታውቀዋል።"

NOTIFY_DRIVER_BOOKING = (
    "🎉 አዲስ ተጓዥ ቦታ ይዟል!\n\n"
    "👤 {rider}\n"
    "📍 መንገዱ፦ {from_name} → {to_name}\n"
    "🕐 መነሻ፦ {time}\n"
    "💺 ቀሪ መቀመጫ፦ {left}/{total}"
)

NOTIFY_DRIVER_CANCEL = "ℹ️ ተጓዥ {rider} ቦታውን ({code}) ሰርዟል። መቀመጫው ክፍት ሆኗል።"

NOTIFY_RIDER_RIDE_CANCELLED = (
    "😕 ይቅርታ — {driver} የለጠፈው መንገድ ({time} {from_name} → {to_name}) ተሰርዟል።\n"
    "የእርስዎ ቦታ ({code}) ተሰርዟል። ሌላ መኪና ይፈልጉ።"
)

STATS = (
    "📊 የጋራ ራይድ ስታቲስቲክስ\n\n"
    "🚗 የተለጠፉ መንገዶች፦ {rides_posted} (ንቁ፦ {rides_active})\n"
    "🎫 የተያዙ ቦታዎች፦ {bookings}\n"
    "💺 የተሞሉ መቀመጫዎች፦ {seats_filled}\n"
    "💰 ጠቅላላ የተጓዥ ቁጠባ፦ {rider_savings} ብር"
)

NO_TOKEN = (
    "BOT_TOKEN is not set — starting ONLY the mini-app web server.\n"
    "To run the full bot:\n"
    "  1. Create a bot with @BotFather on Telegram and copy the token\n"
    "  2. Set it:  set BOT_TOKEN=123:abc   (cmd)  or  $env:BOT_TOKEN='123:abc'   (PowerShell)\n"
    "  3. Run again:  python bot.py\n"
    "Mini app preview:  http://localhost:8080"
)
