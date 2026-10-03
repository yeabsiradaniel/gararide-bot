// User-facing copy in both languages. `S` points at the active set; the language
// button swaps it via setActiveLang(), and the app re-renders to pick it up.
export type Lang = 'am' | 'en'

const am = {
  appName: 'ጋራ ራይድ',
  loading: 'በመጫን ላይ…',
  retry: 'እንደገና ሞክር',
  back: 'ተመለስ',
  home: 'መጀመሪያ',
  cancel: 'ተወው',
  continue_: 'ቀጥል',
  towerWord: 'ማማ',
  birr: 'ብር',
  tomorrow: 'ነገ',
  morning: 'ጠዋት',
  afternoon: 'ከሰዓት',
  errorGeneric: 'ስህተት ተፈጥሯል',
  profile: 'መገለጫ',
  profileTitle: 'የእኔ መገለጫ',
  langRow: 'ቋንቋ',
  roleDriver: 'ሹፌር',
  roleRider: 'ተሳፋሪ',
  contactSupport: 'ድጋፍ አግኙ',
  supportTitle: 'ድጋፍ አግኙ',
  supportHint: 'መልዕክትዎ ለአስተዳዳሪ ይደርሳል።',
  supportPlaceholder: 'እንዴት ልንረዳዎ?',
  sendMessage: 'መልዕክት ላክ',
  supportSent: 'መልዕክትዎ ተልኳል።',
  rateLimited: 'በጣም ፈጣን ነው። ትንሽ ቆይተው እንደገና ይሞክሩ።',

  // consent
  // first-open walkthrough
  howItWorks: 'እንዴት እንደሚሰራ',
  getStarted: 'እንጀምር',
  riderSteps: [
    { icon: 'search', title: 'መንገድ ይፈልጉ', sub: 'ጎረቤት ወደ አቅጣጫዎ እየሄደ ሊሆን ይችላል።' },
    { icon: 'ticket', title: 'ቦታ ይያዙ', sub: 'መጀመሪያ ሹፌሩን፣ መኪናውንና ታርጋውን ያያሉ።' },
    { icon: 'check', title: 'በመኪና ይክፈሉ', sub: 'ጋራ ራይድ ገንዘብ አይይዝም።' },
  ] as { icon: string; title: string; sub: string }[],
  driverSteps: [
    { icon: 'car', title: 'ወንበሮችዎን ይለጥፉ', sub: 'ወዴት እንደሚሄዱ ያጋሩ።' },
    { icon: 'users', title: 'ተሳፋሪዎች ይይዛሉ', sub: 'ማን እንደያዘና የት እንደሚወርድ ያያሉ።' },
    { icon: 'steering', title: 'እየመጣሁ → ደረስኩ', sub: 'ተሳፋሪዎች ቆጠራ ያገኛሉ፤ ክፍያ በመኪና ይሰበሰባል።' },
  ] as { icon: string; title: string; sub: string }[],

  consentTitle: 'ከመጀመርዎ በፊት',
  consentBody: 'ጋራ ራይድ ጎረቤቶችን ለጋራ ጉዞ ያገናኛል።\n\n• ተከባብረው በሰዓቱ ይሁኑ።\n• ክፍያውን በመኪና ውስጥ ይክፈሉ። ጋራ ራይድ ገንዘብ አይይዝም።\n• አገልግሎቱን ለማስኬድ ስምዎን፣ ስልክዎንና ጉዞዎችዎን እናስቀምጣለን።\n\nበመቀጠል እነዚህን ይስማማሉ።',
  agree: 'እስማማለሁ',

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
  hi: (name: string) => `ሰላም ${name}`,
  postRideInstead: 'መንገድ ልለጥፍ እፈልጋለሁ',

  // driver saved routes (one-tap repeat)
  myRoutes: 'የተለመዱ መንገዶቼ',
  saveRoute: 'እንደ የተለመደ መንገድ አስቀምጥ',
  routeSaved: 'መንገዱ ተቀምጧል',
  postTomorrow: 'ነገ ለጥፍ',
  routePosted: 'ለነገ ተለጥፏል',
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
  posted: 'ተለጥፏል',
  rosterLocked: 'ለነገ የመለጠፊያ ሰዓት አልፏል (21:00)። ዛሬ ይለጥፉ ወይም ነገ ይሞክሩ።',
  tooSoon: 'ቢያንስ ከመነሻ 2 ሰዓት በፊት መለጠፍ ያስፈልጋል።',
  editTripTitle: 'ጉዞ አስተካክል',
  tripUpdated: 'ጉዞው ተስተካክሏል',
  ridersPay: 'ተሳፋሪዎች የሚከፍሉት፡',
  seatsWord: 'ወንበር',
  collected: 'የተሰበሰበ',
  ofPaid: (paid: number, total: number) => `${paid}/${total} ከፍለዋል`,

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
  requestPosted: 'ጥያቄዎ ተለጥፏል',

  // trip card
  takeSeat: 'ቦታ ልያዝ',
  bayAlpha: 'Bay Alpha, ዋና በር',
  payInCar: (amt: string) => `${amt} · በመኪና ውስጥ ይክፈሉ`,
  call: 'ደውል',
  imComing: 'እየመጣሁ ነው',
  imComingSent: 'ሹፌሩ ተነገረው።',
  rideAgain: 'እንደገና ተሳፈር',
  shareRide: 'የጉዞ ዝርዝር አጋራ',
  shareRideMsg: (d: { driver: string; car: string; plate: string; dest: string; when: string; bay: string }) =>
    `ጋራ ራይድ · የእኔ ጉዞ\n`
    + `ሹፌር፡ ${d.driver} (የተረጋገጠ)\n`
    + `መኪና፡ ${d.car} · ${d.plate}\n`
    + `መድረሻ፡ ${d.dest}\n`
    + `ሰዓት፡ ${d.when}\n`
    + `መሳፈሪያ፡ ${d.bay}`,
  cancelBooking: 'ተወው',
  notThisDriver: 'ይህን ሰው አልፈልግም',
  reportProblem: 'ችግር ሪፖርት አድርግ',
  reportTitle: 'ምን ተፈጠረ?',
  reportSub: 'ይህ ለአስተዳዳሪ ይደርሳል። ሹፌሩ አያውቅም።',
  reportReasons: [
    { key: 'unsafe_driving', label: 'አደገኛ አነዳድ' },
    { key: 'no_show', label: 'አልመጣም' },
    { key: 'rude', label: 'ባለጌ ወይም ተገቢ ያልሆነ' },
    { key: 'wrong_car', label: 'መኪናው እንደተገለጸው አይደለም' },
    { key: 'other', label: 'ሌላ' },
  ] as { key: string; label: string }[],
  reportNotePlaceholder: 'ተጨማሪ ዝርዝር (አማራጭ)',
  sendReport: 'ሪፖርት ላክ',
  reportSent: 'ሪፖርትዎ ለአስተዳዳሪ ደርሷል። እናመሰግናለን።',
  cantDrive: 'መንዳት አልችልም',
  paid: 'ተከፍሏል',
  noShow: 'አልመጣም',
  rateRide: 'ጉዞው እንዴት ነበር?',
  rateThanks: 'ስለ ግምገማዎ እናመሰግናለን።',
  driverNoShow: 'ሹፌሩ አልመጣም',
  driverNoShowConfirm: 'ሹፌሩ አልመጣም ብለው ለአስተዳዳሪ ያሳውቁ?',
  driverNoShowSent: 'ለአስተዳዳሪ ተነግሯል። እናመሰግናለን።',

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
  fldColor: 'የመኪና ቀለም',
  fldPlate: 'ታርጋ',
  verified: 'የተረጋገጠ',
  fldSeats: 'የመኪና ወንበሮች',
  fldWomanDriver: 'ሴት ሹፌር',
  saveDriver: 'መዝግብ',
  editDriver: 'ሹፌር አስተካክል',
  saveChanges: 'ለውጦችን አስቀምጥ',
  driverAdded: 'ሹፌር ተመዝግቧል',
  onboarded: 'ገብቷል',
  pending: 'ይጠበቃል',
  noDriversYet: 'ገና ሹፌር የለም።',
  removeDriverConfirm: (name: string) => `${name}ን ከሹፌሮች ዝርዝር ማስወገድ ይፈልጋሉ? ክፍት መንገዶቻቸው ይሰረዛሉ።`,
  driverRemoved: 'ሹፌር ተወግዷል',
  // admin / ops
  opsTitle: 'ኦፕስ',
  statTrips: 'ዛሬ ጉዞዎች',
  statSeats: 'የተያዙ ወንበሮች',
  statNoShows: 'ያልመጡ',
  statRequests: 'ክፍት ጥያቄዎች',
  statUsers: 'የተመዘገቡ',
  reportsHeading: 'ሪፖርቶች',
  resolveBtn: 'ፈታ',
  byWord: 'በ',
  recruitHeading: 'ሹፌር ይፈለጋል ለ',
  waitingWord: 'በመጠባበቅ',
  noUnmatched: 'በዚህ ሳምንት ያልተሟሉ ፍለጋዎች የሉም።',
  broadcastTitle: 'ማሰራጫ',
  broadcastSub: 'ለሁሉም / ለሹፌሮች / ለተሳፋሪዎች መልዕክት',
  broadcastHint: 'ማስታወቂያ ይላኩ። በቦቱ በኩል ለሰዎች ይደርሳል።',
  audEveryone: 'ሁሉም',
  audDrivers: 'ሹፌሮች',
  audRiders: 'ተሳፋሪዎች',
  sendBroadcast: 'ማሰራጫ ላክ',
  broadcastPlaceholder: 'መልዕክትዎ…',
  sentTo: (n: number) => `ለ${n} ተልኳል።`,

  // boarding / dwell
  onMyWay: 'እየመጣሁ ነው',
  howFarOut: 'ምን ያህል ርቀት ላይ ነዎት?',
  minsOut: (n: number) => `${n} ደቂቃ`,
  onTheWay: 'ሹፌሩ እየመጣ ነው',
  arrivesIn: 'በሚደርሱበት፡',
  iveArrived: 'ደረስኩ',
  driverHere: 'ሹፌሩ ደርሷል',
  boardWithin: 'በዚህ ጊዜ ውስጥ ይሳፈሩ፡',
  boardingEnded: 'የመሳፈሪያ ጊዜ አልቋል',
  // status badges
  cancelledBadge: 'ተሰርዟል',
  bookingClosed: 'የመያዣ ጊዜው አልፏል።',
  timeConflict: 'በዚህ ሰዓት አካባቢ አስቀድመው የያዙት ጉዞ አለ። መጀመሪያ ይሰርዙት።',
  waitlistAsk: 'ቦታው ተይዟል። ቦታ ሲከፈት እንድናሳውቅዎ ይፈልጋሉ?',
  waitlistJoined: 'ቦታ ሲከፈት እናሳውቅዎታለን።',

  // history / receipts
  tabUpcoming: 'የሚመጡ',
  tabHistory: 'ታሪክ',
  statusCompleted: 'ተጠናቋል',
  statusNoShow: 'አልመጣም',
  noHistory: 'ገና ያለፈ ጉዞ የለም።',

  // empty
  noneYet: 'ገና ምንም የለም።',
  noRequestsYet: 'ገና ጥያቄ የለም።',
  seatTaken: 'ይቅርታ፣ ቦታው ተይዟል።',
}

export type Strings = typeof am

const en: Strings = {
  appName: 'Gara Ride',
  loading: 'Loading…',
  retry: 'Try again',
  back: 'Back',
  home: 'Home',
  cancel: 'Cancel',
  continue_: 'Continue',
  towerWord: 'Tower',
  birr: 'birr',
  tomorrow: 'Tomorrow',
  morning: 'AM',
  afternoon: 'PM',
  errorGeneric: 'Something went wrong',
  profile: 'Profile',
  profileTitle: 'My profile',
  langRow: 'Language',
  roleDriver: 'Driver',
  roleRider: 'Rider',
  contactSupport: 'Contact support',
  supportTitle: 'Contact support',
  supportHint: 'Your message reaches an admin.',
  supportPlaceholder: 'How can we help?',
  sendMessage: 'Send message',
  supportSent: 'Your message was sent.',
  rateLimited: 'That was quick — please wait a moment and try again.',

  howItWorks: 'How it works',
  getStarted: "Let's go",
  riderSteps: [
    { icon: 'search', title: 'Find a ride', sub: 'A neighbour may be heading your way.' },
    { icon: 'ticket', title: 'Take a seat', sub: 'See the driver, car and plate first.' },
    { icon: 'check', title: 'Pay in the car', sub: 'Gara Ride never handles money.' },
  ],
  driverSteps: [
    { icon: 'car', title: 'Post your seats', sub: 'Share where you\'re going.' },
    { icon: 'users', title: 'Riders book', sub: 'You see who booked and their stop.' },
    { icon: 'steering', title: 'On my way → arrived', sub: 'Riders get a countdown; collect fares in the car.' },
  ],

  consentTitle: 'Before you start',
  consentBody: 'Gara Ride connects neighbours for shared rides.\n\n• Be respectful and on time.\n• Pay the fare in the car. Gara Ride never handles money.\n• We store your name, phone and trips to run the service.\n\nBy continuing you agree to these.',
  agree: 'I agree',

  notRegisteredTitle: 'Not registered yet',
  notRegisteredBody: 'Share your phone number with the Telegram bot to get started.',

  driverHome: 'How can we help?',
  postTrip: 'Post a trip',
  postTripSub: 'Share your empty seats',
  requestsNear: "Neighbours' requests",
  requestsNearSub: 'Heading your way',
  myTrips: 'My trips',
  iNeedARide: 'I need a ride today',
  hi: (name: string) => `Hi ${name}`,
  postRideInstead: 'I want to post a ride',

  myRoutes: 'My usual routes',
  saveRoute: 'Save as a usual route',
  routeSaved: 'Route saved',
  postTomorrow: 'Post for tomorrow',
  routePosted: 'Posted for tomorrow',
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
  posted: 'Posted',
  rosterLocked: 'Posting for tomorrow closes at 21:00. Post for today, or try again tomorrow.',
  tooSoon: 'Post at least 2 hours before departure.',
  editTripTitle: 'Edit trip',
  tripUpdated: 'Trip updated',
  ridersPay: 'Riders pay:',
  seatsWord: 'seats',
  collected: 'Collected',
  ofPaid: (paid: number, total: number) => `${paid}/${total} paid`,

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
  requestPosted: 'Your request is posted',

  takeSeat: 'Take a seat',
  bayAlpha: 'Bay Alpha, main gate',
  payInCar: (amt: string) => `${amt} · pay in the car`,
  call: 'Call',
  imComing: "I'm on my way",
  imComingSent: 'The driver has been told.',
  rideAgain: 'Ride again',
  shareRide: 'Share ride details',
  shareRideMsg: (d) =>
    `Gara Ride · my ride\n`
    + `Driver: ${d.driver} (Verified)\n`
    + `Car: ${d.car} · ${d.plate}\n`
    + `To: ${d.dest}\n`
    + `When: ${d.when}\n`
    + `Pickup: ${d.bay}`,
  cancelBooking: 'Cancel',
  notThisDriver: 'Not this person',
  reportProblem: 'Report a problem',
  reportTitle: 'What happened?',
  reportSub: 'This reaches an admin. The driver is never told.',
  reportReasons: [
    { key: 'unsafe_driving', label: 'Unsafe driving' },
    { key: 'no_show', label: "Didn't show up" },
    { key: 'rude', label: 'Rude or inappropriate' },
    { key: 'wrong_car', label: 'Car not as described' },
    { key: 'other', label: 'Other' },
  ],
  reportNotePlaceholder: 'More detail (optional)',
  sendReport: 'Send report',
  reportSent: 'Your report reached an admin. Thank you.',
  cantDrive: "I can't drive",
  paid: 'Paid',
  noShow: 'No-show',
  rateRide: 'How was the ride?',
  rateThanks: 'Thanks for the feedback.',
  driverNoShow: "Driver didn't show",
  driverNoShowConfirm: "Tell an admin the driver didn't show up?",
  driverNoShowSent: 'Reported to an admin. Thank you.',

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
  fldColor: 'Car colour',
  fldPlate: 'Plate',
  verified: 'Verified',
  fldSeats: 'Car seats',
  fldWomanDriver: 'Woman driver',
  saveDriver: 'Save',
  editDriver: 'Edit driver',
  saveChanges: 'Save changes',
  driverAdded: 'Driver saved',
  onboarded: 'Joined',
  pending: 'Pending',
  noDriversYet: 'No drivers yet.',
  removeDriverConfirm: (name: string) => `Remove ${name} from the driver roster? Their open trips will be cancelled.`,
  driverRemoved: 'Driver removed',
  opsTitle: 'Ops',
  statTrips: 'Trips today',
  statSeats: 'Seats filled',
  statNoShows: 'No-shows',
  statRequests: 'Open requests',
  statUsers: 'Registered',
  reportsHeading: 'Reports',
  resolveBtn: 'Resolve',
  byWord: 'by',
  recruitHeading: 'Recruit drivers for',
  waitingWord: 'waiting',
  noUnmatched: 'No unmatched searches this week.',
  broadcastTitle: 'Broadcast',
  broadcastSub: 'Message everyone / drivers / riders',
  broadcastHint: 'Send an announcement. It reaches people in the bot chat.',
  audEveryone: 'Everyone',
  audDrivers: 'Drivers',
  audRiders: 'Riders',
  sendBroadcast: 'Send broadcast',
  broadcastPlaceholder: 'Your message…',
  sentTo: (n: number) => `Sent to ${n}.`,

  onMyWay: "I'm on my way",
  howFarOut: 'How far out are you?',
  minsOut: (n: number) => `${n} min`,
  onTheWay: 'Driver is on the way',
  arrivesIn: 'Arrives in:',
  iveArrived: "I've arrived",
  driverHere: 'Driver is here',
  boardWithin: 'Board within:',
  boardingEnded: 'Boarding time is over',
  cancelledBadge: 'Cancelled',
  bookingClosed: 'Booking has closed for this trip.',
  timeConflict: 'You already have a ride booked around this time. Cancel it first.',
  waitlistAsk: "That seat's gone. Want us to notify you if one frees?",
  waitlistJoined: "We'll ping you if a seat frees.",

  tabUpcoming: 'Upcoming',
  tabHistory: 'History',
  statusCompleted: 'Completed',
  statusNoShow: 'No-show',
  noHistory: 'No past rides yet.',

  noneYet: 'Nothing yet.',
  noRequestsYet: 'No requests yet.',
  seatTaken: 'Sorry, that seat is taken.',
}

const LANGS: Record<Lang, Strings> = { am, en }

// eslint-disable-next-line import/no-mutable-exports
export let S: Strings = am
// eslint-disable-next-line import/no-mutable-exports
export let activeLang: Lang = 'am'

export function setActiveLang(lang: Lang): void {
  S = LANGS[lang]
  activeLang = lang
}

// Pick a value by the active language, falling back to Amharic if the English
// variant is missing. Used for data the backend sends in both languages (places).
export function loc(am_: string, en_?: string | null): string {
  return activeLang === 'en' && en_ ? en_ : am_
}

// Map a posting/editing error detail to a friendly, localized message.
export function postErrorMsg(detail?: string): string {
  if (detail === 'too_soon') return S.tooSoon
  if (detail === 'roster_locked') return S.rosterLocked
  return detail || ''
}
