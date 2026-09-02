// All user-facing copy, Amharic-first. Mirrors gararide/strings_am.py.
export const S = {
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
} as const
