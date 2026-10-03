"""All user-facing copy. No literals in handlers."""

# --- onboarding
WELCOME_DRIVER = (
    "ሰላም! ወደ ጋራ ራይድ እንኳን በደህና መጡ 🚗\n\n"
    "እርስዎ በአያት 49 የተረጋገጡ ሹፌር ነዎት።\n"
    "ለመጀመር ስልክ ቁጥርዎን ያጋሩ።"
)
WELCOME_RIDER = (
    "ሰላም! ወደ ጋራ ራይድ እንኳን በደህና መጡ 🙋\n\n"
    "ጎረቤትዎ ወደሚሄዱበት አቅጣጫ እየሄደ ነው። ባዶ ወንበሩን ይጋሩ።\n"
    "ለመጀመር ስልክ ቁጥርዎን ያጋሩ።"
)
SHARE_CONTACT = "📱 ስልኬን አጋራ"
NOT_ALLOWLISTED = (
    "ይቅርታ፣ ይህ ቁጥር ገና አልተመዘገበም።\n"
    "እባክዎ በአያት 49 የምዝገባ ጠረጴዛ ላይ ይመዝገቡ።"
)
REGISTERED = "ተመዝግበዋል 🎉"

# --- Mini App launcher
OPEN_APP = "🚗 ጋራ ራይድን ክፈት"
OPEN_APP_PROMPT = "ለመቀጠል ጋራ ራይድን ይክፈቱ።"

# --- homes
HOME_DRIVER = "ምን ልታገዝ?"
HOME_RIDER = "ወዴት ነው የሚሄዱት?"
BTN_POST_TRIP = "🚗 መንገድ ልለጥፍ"
BTN_REQUESTS_NEAR = "📋 የጎረቤቶች ጥያቄ"
BTN_MY_TRIPS = "🗓 የእኔ መንገዶች"
BTN_FIND_RIDE = "🔍 መንገድ ልፈልግ"
BTN_POST_REQUEST = "✋ ጥያቄ ልለጥፍ"
BTN_MY_BOOKINGS = "🎫 የእኔ ቦታዎች"
BTN_I_NEED_A_RIDE = "ዛሬ ቦታ እፈልጋለሁ"
BTN_HOME = "🏠 ወደ መጀመሪያ"
BTN_BACK = "⬅️ ተመለስ"
BTN_CANCEL = "❌ ተወው"

# --- driver: post a trip
ASK_DEST = "ወዴት ነው የሚሄዱት?"
ASK_DROPOFFS = "በመንገድ ላይ የት ማውረድ ይችላሉ?"
ASK_DROPOFFS_HINT = "የመጨረሻ መድረሻዎ ብቻ ቢሆንም ችግር የለም።"
ASK_SLOT = "ስንት ሰዓት ይነሳሉ?"
ASK_SEATS = "ስንት ባዶ ወንበር አለ?"
BTN_ANOTHER_TIME = "ሌላ ሰዓት"
BTN_DONE = "✅ ጨርሻለሁ"
TRIP_POSTED = "ተለጥፏል 👍"
ASK_ANOTHER_TIME_PROMPT = "ሰዓቱን ይጻፉ፣ ለምሳሌ 14:30"
DROPOFFS_PREFIX = "የሚያወርዱባቸው፡ "
SEATS_WORD = "ወንበር"
NO_REQUESTS_YET = "ገና ጥያቄ የለም።"

# --- rider: search
ASK_WHERE_TO = "ወዴት?"
ASK_WHEN = "መቼ?"
NO_EXACT_MATCH = "ገና ወደ {dest} በ{when} የሚሄድ የለም።"
NEAR_MISS_HEADER = "ቅርብ የሆኑ፡"
DEMAND_LINE = "{count} ጎረቤቶች ወደዚያ መሄድ ይፈልጋሉ።"
BTN_POST_MY_REQUEST = "✋ ጥያቄዬን ልለጥፍ"
BTN_NOTIFY_ME = "🔔 ሲከፈት ንገረኝ"
BTN_TAKE_SEAT = "✅ ቦታ ልያዝ"
WHEN_TOMORROW_MORNING = "ነገ ጠዋት"
SEAT_TAKEN = "ይቅርታ፣ ቦታው ተይዟል።"
REQUEST_POSTED = "ጥያቄዎ ተለጥፏል ✋"

# --- trip card
BTN_CALL = "📞 ደውል"
BTN_NOT_THIS_DRIVER = "ይህን ሰው አልፈልግም"
BTN_CANT_MAKE_IT = "መምጣት አልችልም"
BTN_CANT_DRIVE = "መንዳት አልችልም"
BTN_PAID = "💵 ተከፍሏል"
PAY_IN_CAR = "{amount} · በመኪና ውስጥ ይክፈሉ"
BAY_ALPHA = "Bay Alpha, ዋና በር"

# --- push notifications (sent by the bot when something happens)
TRIP_MATCHED = "ወደ {dest} ({when}) የሚሄድ ሹፌር ተገኘ 🔔 ቦታ ይያዙ።"
ON_THE_WAY = "ሹፌርዎ እየመጣ ነው 🚗 ወደ Bay Alpha ለመድረስ በግምት {mins} ደቂቃ።"
BOARDING_OPEN = "ሹፌርዎ Bay Alpha ደርሷል 🚗 ለመሳፈር {mins} ደቂቃ አለዎት።"
SEAT_BOOKED = "{name} ወደ {dest} ቦታ ያዙ 🎟"
BOOKING_CANCELLED = "{name} ወደ {dest} የያዙትን ቦታ ሰረዙ።"
TRIP_CANCELLED = "ወደ {dest} ({when}) የያዙት ጉዞ ተሰርዟል።"
TRIP_UPDATED = "ወደ {dest} የያዙት ጉዞ ተስተካክሏል። አሁን {when} ይነሳል።"
ADMIN_NEW_REPORT = "⚠️ አዲስ ሪፖርት\n{reporter} {reported}ን ሪፖርት አድርጓል፤ {reason}።\nለማየት የአስተዳደር Ops ገጽን ይክፈቱ።"
SUPPORT_MSG = "📨 የድጋፍ መልዕክት\nከ {name} ({phone}):\n{msg}"
REPORT_REASON_LABELS = {
    "unsafe_driving": "አደገኛ አነዳድ",
    "no_show": "አልመጣም",
    "rude": "ባለጌ ወይም ተገቢ ያልሆነ",
    "wrong_car": "መኪናው እንደተገለጸው አይደለም",
    "driver_no_show": "ሹፌሩ አልመጣም",
    "other": "ሌላ",
}

# --- inline buttons + callback toasts + interactive pushes
BTN_ON_WAY = "🚗 እየመጣሁ ነው"
BTN_ARRIVED = "📍 ደረስኩ"
BTN_PAID = "💵 {name} ከፍሏል"
BTN_NOSHOW = "{name} አልመጣም"
BTN_CANCEL_SEAT = "ቦታዬን ተወው"
BTN_RATE_UP = "👍 ጥሩ"
BTN_RATE_DOWN = "👎 መጥፎ"
BTN_POST_TODAY = "ለዛሬ ለጥፍ"
BTN_YES_DRIVING = "✅ አዎ፣ እነዳለሁ"
BTN_CANCEL_TRIP = "ጉዞውን ሰርዝ"
BTN_NOTIFY_SEAT = "🔔 ቦታ ሲከፈት ንገረኝ"
BTN_BOOK_NOW = "ያዝ"
BTN_IM_COMING = "🙋 እየመጣሁ ነው"
BTN_OPEN = "ክፈት"
ETA_5 = "~5 ደቂቃ"
ETA_10 = "~10 ደቂቃ"
ETA_15 = "~15 ደቂቃ"
CB_PICK_ETA = "ምን ያህል ርቀት ላይ ነዎት?"
CB_ON_WAY = "ተሳፋሪዎች እየመጡ መሆንዎን ተነገራቸው።"
CB_ARRIVED = "ተሳፋሪዎች መድረስዎን ተነገራቸው።"
CB_PAID = "እንደተከፈለ ተመዝግቧል።"
CB_NOSHOW_EARLY = "መጀመሪያ የመሳፈሪያ ጊዜውን ይጠብቁ።"
CB_NOSHOW = "እንዳልመጣ ተመዝግቧል።"
CB_CANCELLED = "ቦታዎ ተሰርዟል።"
CB_RATED = "ስለ ግምገማዎ እናመሰግናለን።"
CB_POSTED = "ተለጥፏል።"
CB_POSTED_ALREADY = "ለዚያ ቀን አስቀድሞ ተለጥፏል።"
CB_LOCKED = "ያንን ለመለጠፍ ጊዜው አልፏል።"
CB_NOT_YOURS = "ይህ ከአሁን በኋላ ለእርስዎ አይገኝም።"
CB_DONE = "ተከናውኗል።"
CB_WAITLISTED = "ቦታ ሲከፈት እናሳውቅዎታለን።"
CB_SEAT_GONE = "ይቅርታ — ቦታው ተይዟል።"
CB_TRIP_CANCELLED = "ጉዞው ተሰርዟል፤ ተሳፋሪዎች ተነገራቸው።"
CB_RIDER_COMING = "ሹፌሩ እርስዎ እየመጡ መሆኑን ተነገረው።"
RATE_PROMPT = "ወደ {dest} ከ{name} ጋር የነበረው ጉዞ እንዴት ነበር?"
DRIVER_REMINDER = "ወደ {dest} የሚሄዱት ጉዞ {when} ይነሳል። ሲነሱ ለተሳፋሪዎች ያሳውቁ።"
DRIVER_PAX = "{name} → {dest}"
MORNING_NUDGE = "የተለመደውን ወደ {dest} ({time}) ጉዞ ለነገ ይለጥፉ?"
EVENING_CONFIRM_Q = "ነገ {when} ወደ {dest} ይነዳሉ?"
DEMAND_NUDGE = "{count} ጎረቤት(ዎች) ወደ {dest} መሄድ ይፈልጋሉ። ጉዞ ይለጥፉ?"
SEAT_FREED = "ወደ {dest} ({when}) ቦታ ተከፈተ። ይያዙ?"
RIDER_COMING = "{name} ወደ መሳፈሪያው እየመጣ ነው።"
EARNINGS_SUMMARY = "ወደ {dest} የነበረው ጉዞ ተጠናቋል 🎉 — {n} ተሳፋሪ(ዎች)፣ {birr} ብር ተሰብስቧል።"

# --- women-only
ASK_WOMEN_ONLY = "የሴቶች ምርጫ"
BTN_WOMEN_DRIVERS_ONLY = "ሴት ሹፌር ብቻ"
BTN_WOMEN_PRESENT = "ሌላ ሴት ያለችበት መኪና ብቻ"
BTN_NO_PREFERENCE = "ምርጫ የለኝም"
