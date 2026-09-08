// User-facing copy in both languages. `S` points at the active set; the language
// button swaps it via setActiveLang(), and the app re-renders to pick it up.
export type Lang = 'am' | 'en'

const am = {
  appName: 'ጋራ ራይድ',
  loading: 'በመጫን ላይ…',
  retry: 'እንደገና ሞክር',
  back: 'ተመለስ',
  home: '🏠 መጀመሪያ',
  cancel: 'ተወው',

  // register bounce
  notRegisteredTitle: 'ገና አልተመዘገቡም',
  notRegisteredBody: 'ለመጀመር በቴሌግራም ቦቱ ላይ ስልክ ቁጥርዎን ያጋሩ።',

  // driver home
  driverHome: 'ምን ላግዝዎ?',
  postTrip: 'መንገድ ልለጥፍ',
  postTripSub: 'ባዶ ወንበሮችዎን ያጋሩ',
  requestsNear: 'የጎረቤቶች ጥያቄ',
  requestsNearSub: 'ወደ አቅጣጫዎ የሚሄዱ',
  myTrips: 'የእኔ መንገዶች',
  iNeedARide: 'ዛሬ ቦታ እፈልጋለሁ',

  // driver saved routes (one-tap repeat)
  myRoutes: 'የተለመዱ መንገዶቼ',
  saveRoute: '⭐ እንደ የተለመደ መንገድ አስቀምጥ',
  routeSaved: 'መንገዱ ተቀምጧል ⭐',
  postTomorrow: 'ነገ ለጥፍ',
  routePosted: 'ለነገ ተለጥፏል 👍',
  alreadyPosted: 'ይህ መንገድ ለነገ አስቀድሞ ተለጥፏል።',
  removeRoute: 'አስወግድ',
  seatsShort: (n: number) => `${n} ወንበር`,
  daysEveryday: 'በየቀኑ',
  daysWeekdays: 'ሰኞ–ዓርብ',
  dayShort: ['ሰኞ', 'ማክ', 'ረቡ', 'ሐሙ', 'ዓር', 'ቅዳ', 'እሁ'],

  // rider home
  riderHome: 'ወዴት ነው የሚሄዱት?',
  findRide: 'መንገድ ልፈልግ',
  findRideSub: 'ጎረቤት ወደዚያ እየሄደ ይሆናል',
  postRequest: 'ጥያቄ ልለጥፍ',
  postRequestSub: 'ሹፌር እንዲያገኝዎ',
  myBookings: 'የእኔ ቦታዎች',
  womenOnly: 'የሴቶች ምርጫ',
  saved: 'የተቀመጡ መንገዶች',

  // post a trip
  whereTo: 'ወዴት ነው የሚሄዱት?',
  dropoffsTitle: 'በመንገድ ላይ የት ማውረድ ይችላሉ?',
  dropoffsHint: 'የመጨረሻ መድረሻዎ ሁሌም ይካተታል።',
  destinationLabel: 'መድረሻ',
  whenLeave: 'ስንት ሰዓት ይነሳሉ?',
  anotherTime: 'ሌላ ሰዓት',
  freeSeats: 'ስንት ባዶ ወንበር አለ?',
  noteLabel: 'ማስታወሻ (አማራጭ)',
  notePlaceholder: 'ለምሳሌ፡ በቦሌ ቡልቡላ አልፋለሁ',
  post: 'ለጥፍ',
  posted: 'ተለጥፏል 👍',
  ridersPay: 'ተሳፋሪዎች የሚከፍሉት፡',
  seatsWord: 'ወንበር',

  // search / results
  when: 'መቼ?',
  tomorrowMorning: 'ነገ ጠዋት',
  today: 'ዛሬ',
  weekend: 'ቅዳሜ/እሁድ',
  neighboursGoing: 'ጎረቤቶች ወደዚያ እየሄዱ',
  noExact: (dest: string) => `ገና ወደ ${dest} የሚሄድ የለም።`,
  closeToWhat: 'ቅርብ የሆኑ፡',
  partway: 'እስከዚህ ድረስ',
  demandLine: (n: number) => `${n} ጎረቤቶች ወደዚያ መሄድ ይፈልጋሉ።`,
  postMyRequest: 'ጥያቄዬን ልለጥፍ',
  requestPosted: 'ጥያቄዎ ተለጥፏል ✋',

  // trip card
  takeSeat: 'ቦታ ልያዝ',
  bayAlpha: 'Bay Alpha — ዋና በር',
  payInCar: (amt: string) => `${amt} — በመኪና ውስጥ ይክፈሉ`,
  call: 'ደውል',
  cancelBooking: 'ተወው',
  notThisDriver: 'ይህን ሰው አልፈልግም',
  cantDrive: 'መንዳት አልችልም',
  paid: 'ተከፍሏል',
  noShow: 'አልመጣም',

  // women-only
  womenDriversOnly: 'ሴት ሹፌር ብቻ',
  womenPresent: 'ሌላ ሴት ያለችበት መኪና ብቻ',
  save: 'አስቀምጥ',

  // admin — desk roster
  addDriver: 'ሹፌር ጨምር',
  addDriverSub: 'የተረጋገጠ ሹፌር ወደ ዝርዝሩ',
  driverRoster: 'የሹፌሮች ዝርዝር',
  fldPhone: 'ስልክ ቁጥር',
  fldName: 'ሙሉ ስም',
  fldTower: 'ማማ / መነሻ',
  fldCar: 'መኪና',
  fldPlate: 'ታርጋ',
  fldSeats: 'የመኪና ወንበሮች',
  fldWomanDriver: 'ሴት ሹፌር',
  saveDriver: 'መዝግብ',
  driverAdded: 'ሹፌር ተመዝግቧል ✓',
  onboarded: 'ገብቷል',
  pending: 'ይጠበቃል',
  noDriversYet: 'ገና ሹፌር የለም።',
  removeDriverConfirm: (name: string) => `${name}ን ከሹፌሮች ዝርዝር ማስወገድ ይፈልጋሉ? ክፍት መንገዶቻቸው ይሰረዛሉ።`,
  driverRemoved: 'ሹፌር ተወግዷል',

  // empty
  noneYet: 'ገና ምንም የለም።',
  noRequestsYet: 'ገና ጥያቄ የለም።',
  seatTaken: 'ይቅርታ — ቦታው ተይዟል።',
}

export type Strings = typeof am

const en: Strings = {
  appName: 'Gara Ride',
  loading: 'Loading…',
  retry: 'Try again',
  back: 'Back',
  home: '🏠 Home',
  cancel: 'Cancel',

  notRegisteredTitle: 'Not registered yet',
  notRegisteredBody: 'Share your phone number with the Telegram bot to get started.',

  driverHome: 'How can we help?',
  postTrip: 'Post a trip',
  postTripSub: 'Share your empty seats',
  requestsNear: "Neighbours' requests",
  requestsNearSub: 'Heading your way',
  myTrips: 'My trips',
  iNeedARide: 'I need a ride today',

  myRoutes: 'My usual routes',
  saveRoute: '⭐ Save as a usual route',
  routeSaved: 'Route saved ⭐',
  postTomorrow: 'Post for tomorrow',
  routePosted: 'Posted for tomorrow 👍',
  alreadyPosted: 'This route is already posted for tomorrow.',
  removeRoute: 'Remove',
  seatsShort: (n: number) => `${n} seat${n === 1 ? '' : 's'}`,
  daysEveryday: 'Every day',
  daysWeekdays: 'Mon–Fri',
  dayShort: ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],

  riderHome: 'Where are you going?',
  findRide: 'Find a ride',
  findRideSub: 'A neighbour may be headed there',
  postRequest: 'Post a request',
  postRequestSub: 'So a driver can find you',
  myBookings: 'My seats',
  womenOnly: 'Women preference',
  saved: 'Saved routes',

  whereTo: 'Where are you going?',
  dropoffsTitle: 'Where can you drop off along the way?',
  dropoffsHint: 'Your final destination is always included.',
  destinationLabel: 'Destination',
  whenLeave: 'What time do you leave?',
  anotherTime: 'Another time',
  freeSeats: 'How many free seats?',
  noteLabel: 'Note (optional)',
  notePlaceholder: 'e.g. I pass through Bole Bulbula',
  post: 'Post',
  posted: 'Posted 👍',
  ridersPay: 'Riders pay:',
  seatsWord: 'seats',

  when: 'When?',
  tomorrowMorning: 'Tomorrow morning',
  today: 'Today',
  weekend: 'Weekend',
  neighboursGoing: 'Neighbours heading there',
  noExact: (dest: string) => `No one is going to ${dest} yet.`,
  closeToWhat: 'Close matches:',
  partway: 'Part of the way',
  demandLine: (n: number) => `${n} neighbours want to go there.`,
  postMyRequest: 'Post my request',
  requestPosted: 'Your request is posted ✋',

  takeSeat: 'Take a seat',
  bayAlpha: 'Bay Alpha — main gate',
  payInCar: (amt: string) => `${amt} — pay in the car`,
  call: 'Call',
  cancelBooking: 'Cancel',
  notThisDriver: 'Not this person',
  cantDrive: "I can't drive",
  paid: 'Paid',
  noShow: 'No-show',

  womenDriversOnly: 'Women drivers only',
  womenPresent: 'Only cars with another woman',
  save: 'Save',

  addDriver: 'Add driver',
  addDriverSub: 'A verified driver to the roster',
  driverRoster: 'Driver roster',
  fldPhone: 'Phone number',
  fldName: 'Full name',
  fldTower: 'Tower / pickup',
  fldCar: 'Car',
  fldPlate: 'Plate',
  fldSeats: 'Car seats',
  fldWomanDriver: 'Woman driver',
  saveDriver: 'Save',
  driverAdded: 'Driver saved ✓',
  onboarded: 'Joined',
  pending: 'Pending',
  noDriversYet: 'No drivers yet.',
  removeDriverConfirm: (name: string) => `Remove ${name} from the driver roster? Their open trips will be cancelled.`,
  driverRemoved: 'Driver removed',

  noneYet: 'Nothing yet.',
  noRequestsYet: 'No requests yet.',
  seatTaken: 'Sorry — that seat is taken.',
}

const LANGS: Record<Lang, Strings> = { am, en }

// eslint-disable-next-line import/no-mutable-exports
export let S: Strings = am

export function setActiveLang(lang: Lang): void {
  S = LANGS[lang]
}
