"""GaraRIde demo bot + mini-app web server, in one process.

Run:  set BOT_TOKEN=<token from @BotFather>  &&  python bot.py
Without a token it still serves the mini app on http://localhost:8080
so the UI can be developed and previewed before the bot exists.
"""
from __future__ import annotations

import asyncio
import logging
import os
from datetime import datetime, timedelta
from pathlib import Path

from aiohttp import web
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update, WebAppInfo
from telegram.ext import (Application, CallbackQueryHandler, CommandHandler,
                          ContextTypes, MessageHandler, filters)

import data
import strings as S

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
log = logging.getLogger("gararide")

BASE_DIR = Path(__file__).parent
WEBAPP_DIR = BASE_DIR / "webapp"
PORT = int(os.environ.get("PORT", "8080"))
WEBAPP_URL = os.environ.get("WEBAPP_URL", f"http://localhost:{PORT}")

store = data.Store()
if not store.open_rides(include_full=True):
    store.seed()

TG_APP: Application | None = None  # set in main(); used by API handlers for notifications


# ---------------------------------------------------------------- helpers

def webapp_button() -> InlineKeyboardButton:
    """Mini-app buttons must be HTTPS; fall back to a plain URL for local dev."""
    if WEBAPP_URL.startswith("https"):
        return InlineKeyboardButton(S.BTN_APP, web_app=WebAppInfo(WEBAPP_URL))
    return InlineKeyboardButton(S.BTN_APP + " (local)", url=WEBAPP_URL)


def home_markup() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(S.BTN_POST, callback_data="post")],
        [InlineKeyboardButton(S.BTN_FIND, callback_data="find")],
        [InlineKeyboardButton(S.BTN_MY_BOOKINGS, callback_data="my:bookings"),
         InlineKeyboardButton(S.BTN_MY_RIDES, callback_data="my:rides")],
        [webapp_button()],
    ])


def stop_buttons(prefix: str, indices: list[int]) -> list[list[InlineKeyboardButton]]:
    return [[InlineKeyboardButton(data.STOPS[i]["name"], callback_data=f"{prefix}:{i}")]
            for i in indices]


def fmt_time(dt: datetime) -> str:
    today = datetime.now().date()
    if dt.date() == today:
        return dt.strftime("%H:%M")
    if dt.date() == today + timedelta(days=1):
        return "ነገ " + dt.strftime("%H:%M")
    return dt.strftime("%b %d %H:%M")


def time_options() -> list[tuple[str, datetime]]:
    """Departure choices: soon today + tomorrow morning commute."""
    now = datetime.now()
    opts = [(f"min:{m}", now + timedelta(minutes=m), label)
            for m, label in ((30, "በ30 ደቂቃ"), (60, "በ1 ሰዓት"), (120, "በ2 ሰዓት"))]
    tomorrow = now + timedelta(days=1)
    for hour in (7, 8):
        dt = tomorrow.replace(hour=hour, minute=0, second=0, microsecond=0)
        opts.append((f"at:{dt.isoformat()}", dt, f"ነገ ጠዋት {dt.strftime('%H:%M')}"))
    return opts


def car_label(ud: dict) -> str:
    return ud.get("car") or "—"


def confirm_text(ud: dict) -> str:
    frm, to = ud["from"], ud["to"]
    return S.CONFIRM_POST.format(
        from_name=data.STOPS[frm]["name"], to_name=data.STOPS[to]["name"],
        time=fmt_time(ud["depart_at"]), seats=ud["seats"], car=car_label(ud),
        fare=data.fare_per_seat(frm, to), solo=data.solo_estimate(frm, to),
    )


def confirm_markup() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(S.BTN_CONFIRM, callback_data="confirm")],
        [InlineKeyboardButton(S.BTN_CANCEL, callback_data="home")],
    ])


async def tg_notify(chat_id: int | None, text: str) -> None:
    if chat_id and TG_APP:
        try:
            await TG_APP.bot.send_message(chat_id, text)
        except Exception as exc:  # user blocked the bot etc.
            log.warning("notify %s failed: %s", chat_id, exc)


async def notify_driver_booking(ride: dict, booking: dict) -> None:
    await tg_notify(ride.get("driver_id"), S.NOTIFY_DRIVER_BOOKING.format(
        rider=booking["rider"],
        from_name=data.STOPS[booking["from"]]["name"],
        to_name=data.STOPS[booking["to"]]["name"],
        time=fmt_time(ride["depart_at"]),
        left=ride["seats_total"] - ride["seats_taken"], total=ride["seats_total"],
    ))


# ---------------------------------------------------------------- bot flow

async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    context.user_data.clear()
    await update.message.reply_text(S.WELCOME, reply_markup=home_markup())


async def cmd_stats(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(S.STATS.format(**store.stats()))


async def on_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Free-text step: driver entering their car + plate."""
    ud = context.user_data
    if not ud.get("awaiting_car"):
        return
    ud["awaiting_car"] = False
    text = update.message.text.strip()
    if text not in (S.BTN_SKIP, "-", "skip"):
        ud["car"] = text[:60]
    await update.message.reply_text(confirm_text(ud), reply_markup=confirm_markup())


async def dispatch(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    payload = query.data
    ud = context.user_data
    user = update.effective_user

    async def edit(text: str, markup: InlineKeyboardMarkup) -> None:
        await query.edit_message_text(text, reply_markup=markup)

    back_home = InlineKeyboardMarkup([[InlineKeyboardButton(S.BTN_HOME, callback_data="home")]])

    # ---- navigation
    if payload == "noop":
        return

    if payload == "home":
        ud.clear()
        await edit(S.WELCOME, home_markup())
        return

    if payload in ("post", "find"):
        ud.clear()
        ud["mode"] = payload
        kb = [[InlineKeyboardButton(label, callback_data=f"dir:{key}")]
              for key, label in data.DIRECTIONS.items()]
        kb.append([InlineKeyboardButton(S.BTN_CANCEL, callback_data="home")])
        await edit(S.CHOOSE_DIRECTION, InlineKeyboardMarkup(kb))
        return

    if payload.startswith("dir:"):
        ud["direction"] = payload.split(":")[1]
        m2b = ud["direction"] == "m2b"
        indices = list(range(len(data.STOPS) - 1)) if m2b else list(range(1, len(data.STOPS)))
        kb = stop_buttons("from", indices)
        kb.append([InlineKeyboardButton(S.BTN_BACK, callback_data=ud["mode"])])
        await edit(S.CHOOSE_FROM, InlineKeyboardMarkup(kb))
        return

    if payload.startswith("from:"):
        ud["from"] = int(payload.split(":")[1])
        m2b = ud["direction"] == "m2b"
        indices = (list(range(ud["from"] + 1, len(data.STOPS))) if m2b
                   else list(range(0, ud["from"])))
        kb = stop_buttons("to", indices)
        kb.append([InlineKeyboardButton(S.BTN_BACK, callback_data=f"dir:{ud['direction']}")])
        await edit(S.CHOOSE_TO, InlineKeyboardMarkup(kb))
        return

    if payload.startswith("to:"):
        ud["to"] = int(payload.split(":")[1])
        if ud["mode"] == "post":
            kb = [[InlineKeyboardButton(label, callback_data=key)]
                  for key, _, label in time_options()]
            kb.append([InlineKeyboardButton(S.BTN_BACK, callback_data=f"from:{ud['from']}")])
            await edit(S.CHOOSE_TIME, InlineKeyboardMarkup(kb))
        else:  # rider: show rides covering their segment
            await show_ride_list(edit, ud)
        return

    # ---- driver continues: time -> seats -> car -> confirm
    if payload.startswith("min:") or payload.startswith("at:"):
        key, value = payload.split(":", 1)
        depart = (datetime.now() + timedelta(minutes=int(value)) if key == "min"
                  else datetime.fromisoformat(value))
        ud["depart_at"] = depart
        kb = [[InlineKeyboardButton(str(n), callback_data=f"seats:{n}") for n in (1, 2, 3, 4)]]
        kb.append([InlineKeyboardButton(S.BTN_BACK, callback_data=f"to:{ud['to']}")])
        await edit(S.CHOOSE_SEATS, InlineKeyboardMarkup(kb))
        return

    if payload.startswith("seats:"):
        ud["seats"] = int(payload.split(":")[1])
        ud["awaiting_car"] = True
        kb = [[InlineKeyboardButton(S.BTN_SKIP, callback_data="car:skip")]]
        await edit(S.ASK_CAR, InlineKeyboardMarkup(kb))
        return

    if payload == "car:skip":
        ud["awaiting_car"] = False
        ud.pop("car", None)
        await edit(confirm_text(ud), confirm_markup())
        return

    if payload == "confirm":
        driver = {
            "name": user.full_name, "car": car_label(ud), "plate": "",
            "rating": 5.0, "phone": "(ከሚኒ አፑ ይመለከቱ)",
        }
        store.add_ride(ud["from"], ud["to"], ud["depart_at"], ud["seats"],
                       driver, driver_id=user.id)
        kb = InlineKeyboardMarkup([
            [InlineKeyboardButton(S.BTN_POST_AGAIN, callback_data="post")],
            [InlineKeyboardButton(S.BTN_HOME, callback_data="home")],
        ])
        await edit(S.POSTED, kb)
        return

    # ---- rider: ride details -> book
    if payload == "back:list":
        await show_ride_list(edit, ud)
        return

    if payload.startswith("ride:"):
        ud["ride_id"] = payload.split(":", 1)[1]
        ride = store.rides.get(ud["ride_id"])
        if ride is None:
            await show_ride_list(edit, ud)
            return
        seg_f, seg_t = ud.get("from", ride["from"]), ud.get("to", ride["to"])
        fare = data.fare_per_seat(seg_f, seg_t)
        solo = data.solo_estimate(seg_f, seg_t)
        text = S.RIDE_DETAILS.format(
            driver=ride["driver"]["name"],
            car=ride["driver"]["car"], rating=ride["driver"]["rating"],
            ride_from=data.STOPS[ride["from"]]["name"], ride_to=data.STOPS[ride["to"]]["name"],
            seg_from=data.STOPS[seg_f]["name"], seg_to=data.STOPS[seg_t]["name"],
            time=fmt_time(ride["depart_at"]),
            left=ride["seats_total"] - ride["seats_taken"], total=ride["seats_total"],
            fare=fare, save=solo - fare, solo=solo,
        )
        kb = InlineKeyboardMarkup([
            [InlineKeyboardButton(S.BTN_BOOK, callback_data=f"book:{ride['id']}")],
            [InlineKeyboardButton(S.BTN_BACK, callback_data="back:list")],
        ])
        await edit(text, kb)
        return

    if payload.startswith("book:"):
        ride_id = payload.split(":", 1)[1]
        ride = store.rides.get(ride_id)
        if ride is None:
            await show_ride_list(edit, ud)
            return
        try:
            booking = store.book(ride_id, user.full_name, rider_id=user.id,
                                 from_idx=ud.get("from"), to_idx=ud.get("to"))
        except ValueError:
            await edit(S.RIDE_FULL, InlineKeyboardMarkup(
                [[InlineKeyboardButton(S.BTN_BACK, callback_data="back:list")]]))
            return
        text = S.BOOKED.format(
            code=booking["code"], driver=ride["driver"]["name"],
            phone=ride["driver"]["phone"], time=fmt_time(ride["depart_at"]),
            from_name=data.STOPS[booking["from"]]["name"], fare=booking["fare"],
        )
        await edit(text, back_home)
        await notify_driver_booking(ride, booking)
        return

    # ---- my bookings (rider)
    if payload == "my:bookings":
        await show_my_bookings(edit, user.id)
        return

    if payload.startswith("cancel:"):
        code = payload.split(":", 1)[1]
        booking = store.cancel_booking(code)
        if booking is None:
            await show_my_bookings(edit, user.id)
            return
        ride = store.rides.get(booking["ride_id"])
        if ride:
            await tg_notify(ride.get("driver_id"), S.NOTIFY_DRIVER_CANCEL.format(
                rider=booking["rider"], code=code))
        await edit(S.BOOKING_CANCELLED.format(code=code), InlineKeyboardMarkup([
            [InlineKeyboardButton(S.BTN_MY_BOOKINGS, callback_data="my:bookings")],
            [InlineKeyboardButton(S.BTN_HOME, callback_data="home")],
        ]))
        return

    # ---- my rides (driver)
    if payload == "my:rides":
        await show_my_rides(edit, user.id)
        return

    if payload.startswith("delride:"):
        ride_id = payload.split(":", 1)[1]
        ride, dropped = store.cancel_ride(ride_id)
        if ride is None:
            await show_my_rides(edit, user.id)
            return
        for b in dropped:
            await tg_notify(b.get("rider_id"), S.NOTIFY_RIDER_RIDE_CANCELLED.format(
                driver=ride["driver"]["name"], time=fmt_time(ride["depart_at"]),
                from_name=data.STOPS[ride["from"]]["name"],
                to_name=data.STOPS[ride["to"]]["name"], code=b["code"]))
        await edit(S.RIDE_CANCELLED.format(
            time=fmt_time(ride["depart_at"]),
            from_name=data.STOPS[ride["from"]]["name"],
            to_name=data.STOPS[ride["to"]]["name"]), back_home)
        return

    log.warning("unhandled callback payload: %s", payload)


async def show_ride_list(edit, ud: dict) -> None:
    frm, to = ud.get("from"), ud.get("to")
    if frm is not None and to is not None:
        rides = store.matching_rides(frm, to)
        fare = data.fare_per_seat(frm, to)
    else:
        rides = store.open_rides(direction=ud.get("direction"))
        fare = None
    if not rides:
        kb = InlineKeyboardMarkup([[InlineKeyboardButton(S.BTN_BACK, callback_data=ud.get("mode", "home"))]])
        await edit(S.NO_RIDES, kb)
        return
    kb = []
    for r in rides:
        line = S.RIDE_LINE.format(
            time=fmt_time(r["depart_at"]),
            ride_from=data.STOPS[r["from"]]["name"],
            ride_to=data.STOPS[r["to"]]["name"],
            left=r["seats_total"] - r["seats_taken"],
            fare=fare if fare is not None else data.fare_per_seat(r["from"], r["to"]),
        )
        kb.append([InlineKeyboardButton(line, callback_data=f"ride:{r['id']}")])
    kb.append([InlineKeyboardButton(S.BTN_HOME, callback_data="home")])
    await edit(S.CHOOSE_RIDE, InlineKeyboardMarkup(kb))


async def show_my_bookings(edit, rider_id: int) -> None:
    bookings = store.bookings_by_rider(rider_id)
    if not bookings:
        await edit(S.MY_BOOKINGS_EMPTY, InlineKeyboardMarkup(
            [[InlineKeyboardButton(S.BTN_HOME, callback_data="home")]]))
        return
    kb = []
    for b in bookings:
        ride = store.rides.get(b["ride_id"])
        time = fmt_time(ride["depart_at"]) if ride else "—"
        line = S.BOOKING_LINE.format(
            code=b["code"], time=time,
            from_name=data.STOPS[b["from"]]["name"],
            to_name=data.STOPS[b["to"]]["name"], fare=b["fare"])
        kb.append([InlineKeyboardButton("❌ " + line, callback_data=f"cancel:{b['code']}")])
    kb.append([InlineKeyboardButton(S.BTN_HOME, callback_data="home")])
    await edit("🎫 የእኔ ቦታዎች — ለመሰረዝ ይንኩ 👇", InlineKeyboardMarkup(kb))


async def show_my_rides(edit, driver_id: int) -> None:
    rides = [r for r in store.rides_by_driver(driver_id)
             if r["depart_at"] > datetime.now() - timedelta(minutes=10)]
    if not rides:
        await edit(S.MY_RIDES_EMPTY, InlineKeyboardMarkup(
            [[InlineKeyboardButton(S.BTN_HOME, callback_data="home")]]))
        return
    kb = []
    for r in rides:
        riders = store.bookings_for_ride(r["id"])
        names = "\n👤 " + "، ".join(b["rider"] for b in riders) if riders else ""
        text = S.MY_RIDE_LINE.format(
            time=fmt_time(r["depart_at"]),
            from_name=data.STOPS[r["from"]]["name"],
            to_name=data.STOPS[r["to"]]["name"],
            taken=r["seats_taken"], total=r["seats_total"], riders=names)
        kb.append([InlineKeyboardButton(text, callback_data="noop")])
        kb.append([InlineKeyboardButton("❌ መንገዱን ሰርዝ", callback_data=f"delride:{r['id']}")])
    kb.append([InlineKeyboardButton(S.BTN_HOME, callback_data="home")])
    await edit("🚗 የእኔ መንገዶች 👇", InlineKeyboardMarkup(kb))


# ------------------------------------------------------------- web server

@web.middleware
async def cors(request: web.Request, handler):
    if request.method == "OPTIONS":
        resp = web.Response()
    else:
        resp = await handler(request)
    resp.headers["Access-Control-Allow-Origin"] = "*"
    resp.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
    resp.headers["Access-Control-Allow-Headers"] = "Content-Type"
    return resp


async def api_state(request: web.Request) -> web.Response:
    return web.json_response({
        "stops": data.STOPS,
        "directions": data.DIRECTIONS,
        "rides": [data.ride_json(r) for r in store.open_rides(include_full=True)],
        "bookings": [data.booking_json(b) for b in store.bookings.values()],
    })


async def api_post_ride(request: web.Request) -> web.Response:
    body = await request.json()
    frm, to = int(body["from"]), int(body["to"])
    if frm == to:
        return web.json_response({"error": "same_stop"}, status=400)
    if body.get("depart_at"):
        depart = datetime.fromisoformat(body["depart_at"])
        if depart.tzinfo is not None:  # normalize UTC/offset ISO to naive local
            depart = depart.astimezone().replace(tzinfo=None)
    else:
        depart = datetime.now() + timedelta(minutes=int(body.get("minutes", 30)))
    driver = {
        "name": (body.get("driver_name") or "አዲስ ሹፌር").strip(),
        "car": (body.get("car") or "—").strip(),
        "plate": "", "rating": 5.0, "phone": "(ለማሳየት)",
    }
    ride = store.add_ride(frm, to, depart, int(body["seats"]), driver,
                          driver_id=body.get("driver_id"))
    return web.json_response(data.ride_json(ride))


async def api_book(request: web.Request) -> web.Response:
    body = await request.json()
    ride_id = body["ride_id"]
    try:
        booking = store.book(ride_id, (body.get("name") or "ተጓዥ").strip(),
                             rider_id=body.get("rider_id"),
                             from_idx=body.get("from"), to_idx=body.get("to"))
    except ValueError as exc:
        return web.json_response({"error": str(exc)}, status=409)
    ride = store.rides[ride_id]
    await notify_driver_booking(ride, booking)
    return web.json_response({"booking": data.booking_json(booking),
                              "ride": data.ride_json(ride)})


async def api_cancel(request: web.Request) -> web.Response:
    body = await request.json()
    booking = store.cancel_booking(body.get("code", ""))
    if booking is None:
        return web.json_response({"error": "not_found"}, status=404)
    ride = store.rides.get(booking["ride_id"])
    if ride:
        await tg_notify(ride.get("driver_id"), S.NOTIFY_DRIVER_CANCEL.format(
            rider=booking["rider"], code=booking["code"]))
    return web.json_response({"ok": True})


def build_webapp() -> web.Application:
    app = web.Application(middlewares=[cors])
    app.router.add_get("/api/state", api_state)
    app.router.add_post("/api/rides", api_post_ride)
    app.router.add_post("/api/book", api_book)
    app.router.add_post("/api/cancel", api_cancel)
    app.router.add_get("/", lambda req: web.FileResponse(WEBAPP_DIR / "index.html"))
    app.router.add_static("/", WEBAPP_DIR)
    return app


async def start_web_server(application: Application) -> None:
    runner = web.AppRunner(build_webapp())
    await runner.setup()
    await web.TCPSite(runner, "0.0.0.0", PORT).start()
    log.info("mini app served on port %s (public URL: %s)", PORT, WEBAPP_URL)


def main() -> None:
    global TG_APP
    token = os.environ.get("BOT_TOKEN")
    if not token:
        print(S.NO_TOKEN)
        web.run_app(build_webapp(), port=PORT, print=None)
        return
    # Python 3.14 no longer creates an implicit event loop; run_polling needs one.
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    app = Application.builder().token(token).post_init(start_web_server).build()
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("stats", cmd_stats))
    app.add_handler(CallbackQueryHandler(dispatch))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, on_text))
    TG_APP = app
    app.run_polling()


if __name__ == "__main__":
    main()
