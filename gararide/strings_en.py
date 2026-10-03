"""English copy — mirrors strings_am.py key for key."""

# --- onboarding
WELCOME_DRIVER = (
    "Hi! Welcome to Gara Ride 🚗\n\n"
    "You're a verified driver at Ayat 49.\n"
    "Share your phone number to get started."
)
WELCOME_RIDER = (
    "Hi! Welcome to Gara Ride 🙋\n\n"
    "A neighbour is heading your way. Share their empty seat.\n"
    "Share your phone number to get started."
)
SHARE_CONTACT = "📱 Share my number"
NOT_ALLOWLISTED = (
    "Sorry, this number isn't registered yet.\n"
    "Please sign up at the Ayat 49 registration desk."
)
REGISTERED = "You're registered 🎉"

# --- Mini App launcher
OPEN_APP = "🚗 Open Gara Ride"
OPEN_APP_PROMPT = "Open Gara Ride to continue."

# --- homes
HOME_DRIVER = "How can we help?"
HOME_RIDER = "Where are you going?"
BTN_POST_TRIP = "🚗 Post a trip"
BTN_REQUESTS_NEAR = "📋 Neighbours' requests"
BTN_MY_TRIPS = "🗓 My trips"
BTN_FIND_RIDE = "🔍 Find a ride"
BTN_POST_REQUEST = "✋ Post a request"
BTN_MY_BOOKINGS = "🎫 My seats"
BTN_I_NEED_A_RIDE = "I need a ride today"
BTN_HOME = "🏠 Home"
BTN_BACK = "⬅️ Back"
BTN_CANCEL = "❌ Cancel"

# --- driver: post a trip
ASK_DEST = "Where are you going?"
ASK_DROPOFFS = "Where can you drop off along the way?"
ASK_DROPOFFS_HINT = "Your final destination alone is fine too."
ASK_SLOT = "What time do you leave?"
ASK_SEATS = "How many free seats?"
BTN_ANOTHER_TIME = "Another time"
BTN_DONE = "✅ Done"
TRIP_POSTED = "Posted 👍"
ASK_ANOTHER_TIME_PROMPT = "Type the time, e.g. 14:30"
DROPOFFS_PREFIX = "Drop-offs: "
SEATS_WORD = "seats"
NO_REQUESTS_YET = "No requests yet."

# --- rider: search
ASK_WHERE_TO = "Where to?"
ASK_WHEN = "When?"
NO_EXACT_MATCH = "No one is going to {dest} at {when} yet."
NEAR_MISS_HEADER = "Close matches:"
DEMAND_LINE = "{count} neighbours want to go there."
BTN_POST_MY_REQUEST = "✋ Post my request"
BTN_NOTIFY_ME = "🔔 Tell me when it opens"
BTN_TAKE_SEAT = "✅ Take a seat"
WHEN_TOMORROW_MORNING = "Tomorrow morning"
SEAT_TAKEN = "Sorry, that seat is taken."
REQUEST_POSTED = "Your request is posted ✋"

# --- trip card
BTN_CALL = "📞 Call"
BTN_NOT_THIS_DRIVER = "Not this person"
BTN_CANT_MAKE_IT = "I can't make it"
BTN_CANT_DRIVE = "I can't drive"
BTN_PAID = "💵 Paid"
PAY_IN_CAR = "{amount} · pay in the car"
BAY_ALPHA = "Bay Alpha, main gate"

# --- push notifications (sent by the bot when something happens)
TRIP_MATCHED = "A driver is now going to {dest} ({when}). Grab a seat 🔔"
ON_THE_WAY = "Your driver is on the way 🚗 about {mins} min to Bay Alpha."
BOARDING_OPEN = "Your driver is at Bay Alpha 🚗 you have {mins} minutes to board."
SEAT_BOOKED = "{name} took a seat to {dest} 🎟"
BOOKING_CANCELLED = "{name} cancelled their seat to {dest}."
TRIP_CANCELLED = "Your ride to {dest} ({when}) was cancelled."
TRIP_UPDATED = "Your ride to {dest} was updated. Now leaving {when}."
ADMIN_NEW_REPORT = "⚠️ New report\n{reporter} reported {reported} for {reason}.\nOpen the admin Ops screen to review."
SUPPORT_MSG = "📨 Support message\nFrom {name} ({phone}):\n{msg}"
REPORT_REASON_LABELS = {
    "unsafe_driving": "Unsafe driving",
    "no_show": "Didn't show up",
    "rude": "Rude or inappropriate",
    "wrong_car": "Car not as described",
    "driver_no_show": "Driver didn't show up",
    "other": "Other",
}

# --- inline buttons + callback toasts + interactive pushes
BTN_ON_WAY = "🚗 On my way"
BTN_ARRIVED = "📍 I've arrived"
BTN_PAID = "💵 {name} paid"
BTN_NOSHOW = "{name} no-show"
BTN_CANCEL_SEAT = "Cancel my seat"
BTN_RATE_UP = "👍 Good"
BTN_RATE_DOWN = "👎 Bad"
BTN_POST_TODAY = "Post for today"
BTN_YES_DRIVING = "✅ Yes, driving"
BTN_CANCEL_TRIP = "Cancel the trip"
BTN_NOTIFY_SEAT = "🔔 Notify me if a seat frees"
BTN_BOOK_NOW = "Grab it"
BTN_IM_COMING = "🙋 I'm on my way"
BTN_OPEN = "Open"
ETA_5 = "~5 min"
ETA_10 = "~10 min"
ETA_15 = "~15 min"
CB_PICK_ETA = "How far out are you?"
CB_ON_WAY = "Riders told you're on the way."
CB_ARRIVED = "Riders told you've arrived."
CB_PAID = "Marked paid."
CB_NOSHOW_EARLY = "Wait out the boarding time first."
CB_NOSHOW = "Marked as a no-show."
CB_CANCELLED = "Your seat is cancelled."
CB_RATED = "Thanks for the feedback."
CB_POSTED = "Posted — good to go."
CB_POSTED_ALREADY = "Already posted for that day."
CB_LOCKED = "Too late to post that one."
CB_NOT_YOURS = "That's not available to you anymore."
CB_DONE = "Done."
CB_WAITLISTED = "We'll ping you if a seat frees."
CB_SEAT_GONE = "Sorry — that seat is gone."
CB_TRIP_CANCELLED = "Trip cancelled; riders notified."
CB_RIDER_COMING = "We told the driver you're coming."
RATE_PROMPT = "How was your ride to {dest} with {name}?"
DRIVER_REMINDER = "Your trip to {dest} leaves {when}. Let your riders know when you set off."
DRIVER_PAX = "{name} → {dest}"
MORNING_NUDGE = "Post your usual run to {dest} ({time}) for tomorrow?"
EVENING_CONFIRM_Q = "Still driving to {dest} {when}?"
DEMAND_NUDGE = "{count} neighbour(s) want {dest}. Post a trip?"
SEAT_FREED = "A seat just opened to {dest} ({when}). Grab it?"
RIDER_COMING = "{name} is on the way to the pickup."
EARNINGS_SUMMARY = "Trip to {dest} done 🎉 — {n} rider(s), {birr} birr collected."

# --- women-only
ASK_WOMEN_ONLY = "Women preference"
BTN_WOMEN_DRIVERS_ONLY = "Women drivers only"
BTN_WOMEN_PRESENT = "Only cars with another woman"
BTN_NO_PREFERENCE = "No preference"
