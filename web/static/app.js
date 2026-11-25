/* FarmaBot Web — ndërfaqja (pa librari të jashtme).
 * Pjesët: tekstet (SQ/EN) · ikonat · API · hyrja · paneli anësor · biseda · cilësimet · admin. */
"use strict";

/* ================================================================ tekstet */
const TEKSTE = {
  sq: {
    newChat: "Bisedë e re", search: "Kërko bisedat", today: "Sot", yesterday: "Dje", week: "7 ditët e fundit",
    month: "30 ditët e fundit", older: "Më herët", noChats: "Bisedat e tua do të shfaqen këtu.", noResults: "Asnjë bisedë nuk u gjet.",
    rename: "Riemërto", del: "Fshi", export: "Shkarko bisedën", copy: "Kopjo", copied: "U kopjua",
    toggleSidebar: "Hap / mbyll panelin", greeting: ["Mirëmëngjes", "Mirëdita", "Mirëmbrëma"],
    helpQ: "Si mund të të ndihmoj sot?",
    placeholder: "Përshkruaj si ndihesh…", think: "Mendo më thellë", thinkHelp: "Bota e rilexon mesazhin me një model që arsyeton dhe e verifikon në bazë. Zgjat më shumë.",
    disclaimer: "FarmaBot jep informacion të përgjithshëm, jo diagnozë. Në urgjencë telefono 127 ose 112.",
    sugg: ["Më dhemb koka prej dy ditësh", "Kam temperaturë dhe grip", "Teshtij shumë dhe më lotojnë sytë", "Më djeg stomaku pas ngrënies"],
    thinking: "Po mendoj", searching: "Po kërkoj në bazën e njohurive", thoughtFor: s => `Mendoi për ${s}`, answered: s => `U përgjigj për ${s}`,
    seconds: n => (n < 2 ? "1 sekondë" : `${Math.round(n)} sekonda`), reasoning: "Arsyetimi i modelit",
    dose: "Doza (të rritur)", max: "Maksimumi", duration: "Kohëzgjatja", how: "Si merret", warnings: "Paralajmërime dhe efekte anësore",
    sideEffect: "Efekt anësor", notForYou: "Nuk sugjerohen për ty", whenDoctor: "Kur duhet të shkosh te mjeku",
    child: "Për fëmijët doza varet nga pesha dhe mosha. Përdor formën pediatrike dhe pyet farmacistin ose pediatrin.",
    leaflet: n => `Fletëudhëzuesi zyrtar FDA: ${n} (anglisht)`, sources: "Burime",
    settings: "Cilësimet", healthProfile: "Profili shëndetësor", admin: "Paneli i administratorit", signOut: "Dil", signIn: "Hyr ose regjistrohu",
    guest: "Vizitor", guestNote: "Pa llogari: asgjë nuk ruhet pasi mbyll faqen.", user: "Përdorues", administrator: "Administrator",
    general: "Të përgjithshme", account: "Llogaria", theme: "Tema", themeSystem: "Sistemi", themeLight: "E bardhë", themeDark: "E zezë",
    language: "Gjuha", thinkDefault: "Mendo më thellë si parazgjedhje", thinkDefaultHelp: "Vlen për mesazhet e reja.",
    shortcuts: "Shkurtoret e tastierës", scNew: "Bisedë e re", scSidebar: "Hap / mbyll panelin", scSend: "Dërgo", scNewline: "Rresht i ri",
    age: "Mosha", agePh: "p.sh. 30", conditions: "Gjendje dhe ilaçe që merr", filter: "Filtro…", allergies: "Alergji ose ilaçe të tjera",
    allergiesPh: "p.sh. alergji nga penicilina", save: "Ruaj", saved: "U ruajt", cancel: "Anulo", close: "Mbyll",
    profileNote: "Ilaçet që nuk të përshtaten hiqen automatikisht nga sugjerimet.",
    username: "Emri i përdoruesit", password: "Fjalëkalimi", changePw: "Ndrysho fjalëkalimin", currentPw: "Fjalëkalimi aktual",
    newPw: "Fjalëkalimi i ri (min. 8 karaktere)", pwChanged: "Fjalëkalimi u ndryshua", deleteAccount: "Fshi llogarinë",
    deleteAccountHelp: "Fshihen llogaria, profili dhe të gjitha bisedat. Kjo nuk kthehet pas.",
    deleteUser: "Fshi përdoruesin", deleteUserQ: u => `Të fshihet përdoruesi “${u}”?`,
    deleteUserHelp: n => `Fshihen llogaria, profili shëndetësor dhe të gjitha bisedat e tij (${n} mesazhe). Kjo nuk kthehet pas; nëse duhet, bëj më parë një backup.`,
    userDeleted: u => `Përdoruesi “${u}” u fshi`,
    confirmDeleteChat: t => `Të fshihet biseda “${t}”?`, confirmDeleteAccount: "Të fshihet llogaria dhe të gjitha të dhënat?",
    welcome: "Mirë se erdhe në FarmaBot", welcomeSub: "Asistenti yt i farmacisë, në shqip dhe anglisht.",
    login: "Hyr", register: "Regjistrohu", continueGuest: "Vazhdo pa llogari", or: "ose",
    nameOpt: "Emri ose pseudonimi (opsional)", ageOpt: "Mosha (opsionale)", repeatPw: "Përsërit fjalëkalimin",
    consent: "Pranoj që profili dhe bisedat e mia të ruhen. Mund t'i fshij kur të dua.", createAccount: "Krijo llogarinë",
    email: "Email-i", emailOrUser: "Email-i ose emri i përdoruesit", emailHelp: "Për rivendosjen e fjalëkalimit, nëse e harron.",
    forgot: "Ke harruar fjalëkalimin?", forgotTitle: "Rivendos fjalëkalimin", forgotSub: "Shkruaj email-in e llogarisë dhe do të të dërgojmë një lidhje për të zgjedhur fjalëkalim të ri.",
    sendLink: "Dërgo lidhjen", linkSent: "Nëse ky email ka llogari, të kemi dërguar një lidhje. Shiko edhe dosjen Spam. Lidhja vlen 30 minuta.",
    smtpMissing: "Dërgimi i email-eve nuk është konfiguruar ende në këtë server. Kërkoji administratorit lidhjen (logs/emailet.log).",
    backToLogin: "Kthehu te hyrja", resetTitle: "Zgjidh fjalëkalimin e ri", resetSub: "Fjalëkalimi duhet të ketë të paktën 8 karaktere.",
    resetDone: "Fjalëkalimi u ndryshua. Tani mund të hysh me fjalëkalimin e ri.", showPw: "Shfaq fjalëkalimin", hidePw: "Fshih fjalëkalimin",
    emailSaved: "Email-i u ruajt", noEmail: "Pa email: nuk mund ta rivendosësh fjalëkalimin nëse e harron.", saveEmail: "Ruaj email-in",
    pwMismatch: "Fjalëkalimet nuk përputhen.", usernameHelp: "3–30 karaktere: shkronja (edhe ç, ë), shifra dhe _ . -",
    feat1: "Nga simptoma te ilaçi pa recetë, me doza nga databaza.", feat2: "Heq ilaçet që nuk të përshtaten: shtatzëni, ulçerë, ilaçe që merr.",
    feat3: "Njeh shenjat e rrezikut dhe të dërgon te mjeku.",
    error: "Ndodhi një gabim", serviceErr: "Kontrollo që Neo4j dhe Ollama janë ndezur.", sessionEnded: "Sesioni mbaroi. Hyr përsëri.",
    overview: "Përmbledhje", users: "Përdoruesit", medicines: "Ilaçet", backup: "Backup",
    accounts: "Llogari", persons: "Persona", questions: "Pyetje", question: "Pyetja", drugs: "Ilaçe", symptoms: "Simptoma",
    topSymptoms: "Simptomat më të shpeshta", topDrugs: "Ilaçet më të sugjeruara", recentQ: "Pyetjet e fundit", noData: "Ende pa të dhëna.",
    role: "Roli", name: "Emri", messages: "Mesazhe", created: "Krijuar", lastLogin: "Hyrja e fundit", actions: "",
    newAccount: "Llogari e re", viewChats: "Shiko bisedat", setPw: "Vendos fjalëkalim", makeAdmin: "Bëje admin", makeUser: "Bëje përdorues",
    create: "Krijo", searchDrugs: "Kërko ilaçin…", newDrug: "Ilaç i ri", edit: "Ndrysho", forSymptoms: "Për simptomat",
    restrictions: "Kundërindikime dhe kujdes", contraindication: "Kundërindikim", caution: "Kujdes",
    pharmacistNote: "Ndryshimet ruhen në Neo4j dhe te data/njohurite.json. Para përdorimit real duhet t'i kontrollojë një farmacist.",
    drugId: "ID (pa hapësira)", activeIng: "Lënda aktive", form: "Forma", tradeNames: "Emra tregtarë (me presje)",
    contraFor: "Kundërindikohet për (hiqet automatikisht)", cautionFor: "Kujdes për (shfaqet paralajmërim)",
    backupNow: "Bëj backup tani", backupDone: d => `Backup-i u ruajt te ${d}`, backupHelp: "Ruan gjithë databazën (JSON + skript Cypher) në Desktop.",
    recentBackups: "Backup-et e fundit", connection: "Lidhja", backToChat: "Kthehu te biseda", noChatsUser: "Pa biseda.", deletedByUser: "Fshirë nga përdoruesi",
    chatDeleteNote: "Biseda hiqet nga lista jote. Administratori i FarmaBot-it mund ta shohë ende.",
    good: "Përgjigje e mirë", bad: "Përgjigje e gabuar", thanksFb: "Faleminderit! Reagimi u ruajt.",
    whatWrong: "Çfarë nuk shkoi?", r_nuk_kuptoi: "Nuk e kuptoi simptomën", r_ilac_gabim: "Ilaçi nuk ishte i duhuri",
    r_e_paqarte: "Përgjigja ishte e paqartë ose e gabuar", r_tjeter: "Tjetër", commentOpt: "Shpjego shkurt (opsionale)",
    send: "Dërgo", training: "Trajnimi", evalRun: "Nis vlerësimin", evalRunning: "Po vlerësoj…",
    evalHelp: "Kalon rreth 270 pyetje provë (simptoma, urgjenca, siguria, anglisht, biseda) dhe mat saktësinë. Zgjat rreth 1 minutë.",
    lastEval: "Vlerësimi i fundit", overall: "Saktësia e përgjithshme", passed: "Kaloi", failed: "Nuk kaloi",
    category: "Kategoria", correct: "Saktë", threshold: "Kufiri", progress: "Përparimi", noEval: "Ende pa vlerësim. Kliko “Nis vlerësimin”.",
    evalErrors: "Gabimet e vlerësimit", evalErrorsHint: "Mos i kopjo këto fraza te baza: përndryshe vlerësimi nuk mat më asgjë. Mëso konceptin me fjalë të tjera.",
    expected: "Pritej", got: "U gjet", feedback: "Reagimet negative të përdoruesve", noFeedback: "Asnjë reagim negativ i hapur.",
    question: "Pyetja", answer: "Përgjigjja", reason: "Arsyeja", teach: "Mësoji botit", chooseSymptom: "Zgjidh simptomën e saktë…",
    resolve: "Shëno si zgjidhur", taught: s => `U mësua: “${s}”`, manualTeach: "Mësim manual", phrase: "Fraza (si e shkruajnë njerëzit)",
    phrasePh: "p.sh. më ka zënë i ftohti", symptom: "Simptoma", recentLessons: "Mësimet e fundit", likes: "Pëlqime", complaints: "Ankesa të hapura",
    historyEval: "Historiku i saktësisë", urgency: "Urgjencat", accuracy: "Saktësia",
  },
  en: {
    newChat: "New chat", search: "Search chats", today: "Today", yesterday: "Yesterday", week: "Previous 7 days",
    month: "Previous 30 days", older: "Older", noChats: "Your chats will appear here.", noResults: "No chats found.",
    rename: "Rename", del: "Delete", export: "Download chat", copy: "Copy", copied: "Copied",
    toggleSidebar: "Open / close sidebar", greeting: ["Good morning", "Good afternoon", "Good evening"],
    helpQ: "How can I help you today?",
    placeholder: "Describe how you feel…", think: "Think deeper", thinkHelp: "Re-reads your message with a reasoning model and checks it against the database. Takes longer.",
    disclaimer: "FarmaBot gives general information, not a diagnosis. In an emergency call 112 (Albania: 127).",
    sugg: ["I've had a headache for two days", "I have a fever and the flu", "I sneeze a lot and my eyes water", "My stomach burns after eating"],
    thinking: "Thinking", searching: "Searching the knowledge base", thoughtFor: s => `Thought for ${s}`, answered: s => `Answered in ${s}`,
    seconds: n => (n < 2 ? "1 second" : `${Math.round(n)} seconds`), reasoning: "Model reasoning",
    dose: "Dose (adults)", max: "Maximum", duration: "Duration", how: "How to take", warnings: "Warnings and side effects",
    sideEffect: "Side effect", notForYou: "Not suggested for you", whenDoctor: "When to see a doctor",
    child: "For children the dose depends on weight and age. Use the paediatric form and ask a pharmacist or paediatrician.",
    leaflet: n => `Official FDA leaflet: ${n}`, sources: "Sources",
    settings: "Settings", healthProfile: "Health profile", admin: "Admin panel", signOut: "Sign out", signIn: "Sign in or sign up",
    guest: "Guest", guestNote: "No account: nothing is kept after you close the page.", user: "User", administrator: "Administrator",
    general: "General", account: "Account", theme: "Theme", themeSystem: "System", themeLight: "Light", themeDark: "Dark",
    language: "Language", thinkDefault: "Think deeper by default", thinkDefaultHelp: "Applies to new messages.",
    shortcuts: "Keyboard shortcuts", scNew: "New chat", scSidebar: "Open / close sidebar", scSend: "Send", scNewline: "New line",
    age: "Age", agePh: "e.g. 30", conditions: "Conditions and medicines you take", filter: "Filter…", allergies: "Allergies or other medicines",
    allergiesPh: "e.g. penicillin allergy", save: "Save", saved: "Saved", cancel: "Cancel", close: "Close",
    profileNote: "Medicines that don't suit you are removed from suggestions automatically.",
    username: "Username", password: "Password", changePw: "Change password", currentPw: "Current password",
    newPw: "New password (min. 8 characters)", pwChanged: "Password changed", deleteAccount: "Delete account",
    deleteAccountHelp: "Your account, profile and all chats are deleted. This cannot be undone.",
    deleteUser: "Delete user", deleteUserQ: u => `Delete the user “${u}”?`,
    deleteUserHelp: n => `The account, health profile and all their chats (${n} messages) are deleted. This cannot be undone; make a backup first if needed.`,
    userDeleted: u => `User “${u}” deleted`,
    confirmDeleteChat: t => `Delete the chat “${t}”?`, confirmDeleteAccount: "Delete your account and all data?",
    welcome: "Welcome to FarmaBot", welcomeSub: "Your pharmacy assistant, in Albanian and English.",
    login: "Sign in", register: "Sign up", continueGuest: "Continue without an account", or: "or",
    nameOpt: "Name or nickname (optional)", ageOpt: "Age (optional)", repeatPw: "Repeat the password",
    consent: "I agree that my profile and chats are stored. I can delete them any time.", createAccount: "Create account",
    email: "Email", emailOrUser: "Email or username", emailHelp: "Used to reset your password if you forget it.",
    forgot: "Forgot password?", forgotTitle: "Reset your password", forgotSub: "Enter your account email and we'll send you a link to choose a new password.",
    sendLink: "Send link", linkSent: "If this email has an account, we've sent a link. Check your spam folder too. The link is valid for 30 minutes.",
    smtpMissing: "Email sending isn't set up on this server yet. Ask the administrator for the link (logs/emailet.log).",
    backToLogin: "Back to sign in", resetTitle: "Choose a new password", resetSub: "The password must have at least 8 characters.",
    resetDone: "Your password was changed. You can now sign in with the new password.", showPw: "Show password", hidePw: "Hide password",
    emailSaved: "Email saved", noEmail: "No email: you can't reset your password if you forget it.", saveEmail: "Save email",
    pwMismatch: "The passwords do not match.", usernameHelp: "3–30 characters: letters (also ç, ë), digits and _ . -",
    feat1: "From symptom to over-the-counter medicine, with doses from the database.", feat2: "Removes medicines that don't suit you: pregnancy, ulcer, medicines you take.",
    feat3: "Recognises danger signs and sends you to a doctor.",
    error: "Something went wrong", serviceErr: "Check that Neo4j and Ollama are running.", sessionEnded: "Your session ended. Please sign in again.",
    overview: "Overview", users: "Users", medicines: "Medicines", backup: "Backup",
    accounts: "Accounts", persons: "People", questions: "Questions", question: "Question", drugs: "Medicines", symptoms: "Symptoms",
    topSymptoms: "Most frequent symptoms", topDrugs: "Most suggested medicines", recentQ: "Recent questions", noData: "No data yet.",
    role: "Role", name: "Name", messages: "Messages", created: "Created", lastLogin: "Last sign-in", actions: "",
    newAccount: "New account", viewChats: "View chats", setPw: "Set password", makeAdmin: "Make admin", makeUser: "Make user",
    create: "Create", searchDrugs: "Search medicines…", newDrug: "New medicine", edit: "Edit", forSymptoms: "For symptoms",
    restrictions: "Contraindications and cautions", contraindication: "Contraindication", caution: "Caution",
    pharmacistNote: "Changes are saved to Neo4j and data/njohurite.json. A pharmacist must review them before real use.",
    drugId: "ID (no spaces)", activeIng: "Active ingredient", form: "Form", tradeNames: "Trade names (comma-separated)",
    contraFor: "Contraindicated for (removed automatically)", cautionFor: "Caution for (shows a warning)",
    backupNow: "Back up now", backupDone: d => `Backup saved to ${d}`, backupHelp: "Saves the whole database (JSON + Cypher script) to the Desktop.",
    recentBackups: "Recent backups", connection: "Connection", backToChat: "Back to chat", noChatsUser: "No chats.", deletedByUser: "Deleted by the user",
    chatDeleteNote: "The chat is removed from your list. The FarmaBot administrator can still see it.",
    good: "Good answer", bad: "Bad answer", thanksFb: "Thank you! Your feedback was saved.",
    whatWrong: "What went wrong?", r_nuk_kuptoi: "It didn't understand the symptom", r_ilac_gabim: "The medicine wasn't right",
    r_e_paqarte: "The answer was unclear or wrong", r_tjeter: "Other", commentOpt: "Explain briefly (optional)",
    send: "Send", training: "Training", evalRun: "Run evaluation", evalRunning: "Evaluating…",
    evalHelp: "Runs about 270 test questions (symptoms, emergencies, safety, English, conversations) and measures accuracy. Takes about 1 minute.",
    lastEval: "Latest evaluation", overall: "Overall accuracy", passed: "Passed", failed: "Failed",
    category: "Category", correct: "Correct", threshold: "Threshold", progress: "Progress", noEval: "No evaluation yet. Click “Run evaluation”.",
    evalErrors: "Evaluation errors", evalErrorsHint: "Don't copy these phrases into the knowledge base, or the evaluation stops measuring anything. Teach the concept in other words.",
    expected: "Expected", got: "Got", feedback: "Negative user feedback", noFeedback: "No open negative feedback.",
    question: "Question", answer: "Answer", reason: "Reason", teach: "Teach the bot", chooseSymptom: "Choose the correct symptom…",
    resolve: "Mark as resolved", taught: s => `Learned: “${s}”`, manualTeach: "Manual lesson", phrase: "Phrase (how people write it)",
    phrasePh: "e.g. I've caught a chill", symptom: "Symptom", recentLessons: "Recent lessons", likes: "Likes", complaints: "Open complaints",
    historyEval: "Accuracy history", urgency: "Emergencies", accuracy: "Accuracy",
  },
};

/* ================================================================ ikonat (vija, 20px) */
const P = {
  panel: '<rect x="3" y="3" width="18" height="18" rx="3"/><path d="M9 3v18"/>',
  newchat: '<path d="M12 20h9"/><path d="M16.4 3.6a2 2 0 0 1 2.9 2.9L7 18.8l-4 1 1-4Z"/>',
  search: '<circle cx="11" cy="11" r="7"/><path d="m20 20-3.5-3.5"/>',
  more: '<circle cx="5" cy="12" r="1.3"/><circle cx="12" cy="12" r="1.3"/><circle cx="19" cy="12" r="1.3"/>',
  pencil: '<path d="M16.4 3.6a2 2 0 0 1 2.9 2.9L7 18.8l-4 1 1-4Z"/>',
  trash: '<path d="M3 6h18"/><path d="M8 6V4h8v2"/><path d="M19 6l-1 14H6L5 6"/>',
  settings: '<circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.7 1.7 0 0 0 .3 1.8l.1.1a2 2 0 1 1-2.8 2.8l-.1-.1a1.7 1.7 0 0 0-1.8-.3 1.7 1.7 0 0 0-1 1.5V21a2 2 0 1 1-4 0v-.1a1.7 1.7 0 0 0-1.1-1.5 1.7 1.7 0 0 0-1.8.3l-.1.1a2 2 0 1 1-2.8-2.8l.1-.1a1.7 1.7 0 0 0 .3-1.8 1.7 1.7 0 0 0-1.5-1H3a2 2 0 1 1 0-4h.1a1.7 1.7 0 0 0 1.5-1.1 1.7 1.7 0 0 0-.3-1.8l-.1-.1a2 2 0 1 1 2.8-2.8l.1.1a1.7 1.7 0 0 0 1.8.3H9a1.7 1.7 0 0 0 1-1.5V3a2 2 0 1 1 4 0v.1a1.7 1.7 0 0 0 1 1.5 1.7 1.7 0 0 0 1.8-.3l.1-.1a2 2 0 1 1 2.8 2.8l-.1.1a1.7 1.7 0 0 0-.3 1.8V9a1.7 1.7 0 0 0 1.5 1H21a2 2 0 1 1 0 4h-.1a1.7 1.7 0 0 0-1.5 1Z"/>',
  heart: '<path d="M19 14c1.5-1.5 3-3.2 3-5.5A5.5 5.5 0 0 0 16.5 3c-1.8 0-3 .5-4.5 2-1.5-1.5-2.7-2-4.5-2A5.5 5.5 0 0 0 2 8.5c0 2.3 1.5 4 3 5.5l7 7Z"/><path d="M3.2 12H8l1.5-3 3 6 1.5-3h6.8"/>',
  shield: '<path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10Z"/>',
  logout: '<path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/><path d="m16 17 5-5-5-5"/><path d="M21 12H9"/>',
  login: '<path d="M15 3h4a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2h-4"/><path d="m10 17 5-5-5-5"/><path d="M15 12H3"/>',
  sun: '<circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M2 12h2M20 12h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4"/>',
  moon: '<path d="M21 12.8A9 9 0 1 1 11.2 3a7 7 0 0 0 9.8 9.8Z"/>',
  monitor: '<rect x="2" y="3" width="20" height="14" rx="2"/><path d="M8 21h8M12 17v4"/>',
  up: '<path d="M12 19V5"/><path d="m5 12 7-7 7 7"/>',
  copy: '<rect x="9" y="9" width="13" height="13" rx="2"/><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/>',
  check: '<path d="M20 6 9 17l-5-5"/>',
  chev: '<path d="m9 18 6-6-6-6"/>',
  bulb: '<path d="M9 18h6M10 22h4"/><path d="M12 2a7 7 0 0 0-4 12.7c.6.5 1 1.3 1 2.3h6c0-1 .4-1.8 1-2.3A7 7 0 0 0 12 2Z"/>',
  download: '<path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><path d="m7 10 5 5 5-5"/><path d="M12 15V3"/>',
  x: '<path d="M18 6 6 18M6 6l12 12"/>',
  pill: '<path d="m10.5 20.5 10-10a4.95 4.95 0 1 0-7-7l-10 10a4.95 4.95 0 1 0 7 7Z"/><path d="m8.5 8.5 7 7"/>',
  alert: '<path d="m21.7 18-8-14a2 2 0 0 0-3.4 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.7-3Z"/><path d="M12 9v4M12 17h.01"/>',
  user: '<circle cx="12" cy="8" r="4"/><path d="M4 21a8 8 0 0 1 16 0"/>',
  globe: '<circle cx="12" cy="12" r="10"/><path d="M2 12h20"/><path d="M12 2a15 15 0 0 1 4 10 15 15 0 0 1-4 10 15 15 0 0 1-4-10 15 15 0 0 1 4-10Z"/>',
  key: '<circle cx="7.5" cy="15.5" r="5.5"/><path d="m21 2-9.6 9.6M15.5 7.5l3 3L22 7l-3-3"/>',
  file: '<path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8Z"/><path d="M14 2v6h6"/>',
  plus: '<path d="M12 5v14M5 12h14"/>',
  eye: '<path d="M2 12s3.5-7 10-7 10 7 10 7-3.5 7-10 7S2 12 2 12Z"/><circle cx="12" cy="12" r="3"/>',
  eyeoff: '<path d="M9.9 4.2A10 10 0 0 1 12 4c6.5 0 10 8 10 8a17 17 0 0 1-2.2 3.2M6.6 6.6C3.7 8.5 2 12 2 12s3.5 8 10 8a9.7 9.7 0 0 0 5.4-1.6"/><path d="M14.1 14.1a3 3 0 1 1-4.2-4.2"/><path d="m2 2 20 20"/>',
  thumbup: '<path d="M7 10v12"/><path d="M15 5.9 14 10h5.8a2 2 0 0 1 2 2.3l-1.4 8A2 2 0 0 1 18.4 22H4a2 2 0 0 1-2-2v-8a2 2 0 0 1 2-2h2.8a2 2 0 0 0 1.8-1.1L12 2a3.1 3.1 0 0 1 3 3.9Z"/>',
  thumbdown: '<path d="M17 14V2"/><path d="M9 18.1 10 14H4.2a2 2 0 0 1-2-2.3l1.4-8A2 2 0 0 1 5.6 2H20a2 2 0 0 1 2 2v8a2 2 0 0 1-2 2h-2.8a2 2 0 0 0-1.8 1.1L12 22a3.1 3.1 0 0 1-3-3.9Z"/>',
  play: '<polygon points="6 3 20 12 6 21 6 3"/>',
  mail: '<rect x="2" y="4" width="20" height="16" rx="2"/><path d="m22 7-10 6L2 7"/>',
  database: '<ellipse cx="12" cy="5" rx="9" ry="3"/><path d="M3 5v14c0 1.7 4 3 9 3s9-1.3 9-3V5"/><path d="M3 12c0 1.7 4 3 9 3s9-1.3 9-3"/>',
};
const ic = (n, s = 18) => `<svg width="${s}" height="${s}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">${P[n]}</svg>`;

/* ================================================================ gjendja */
const ruaj = (k, v) => { try { localStorage.setItem("fb." + k, v); } catch (e) { /* pa storage */ } };
const lexo = (k, d) => { try { return localStorage.getItem("fb." + k) ?? d; } catch (e) { return d; } };

const S = {
  sesioni: null,         // {llogaria, vizitor, profili, gjendjet}
  bisedat: [],
  aktive: null,          // {id, titull, mesazhet}
  duke_pritur: false,
  kerkimi: "",
  pamja: "biseda",       // "biseda" | "admin"
  adminTab: "permbledhje",
  gjuha: lexo("gjuha", (navigator.language || "sq").startsWith("en") ? "en" : "sq"),
  tema: lexo("tema", "system"),
  mendo: lexo("mendo", "0") === "1",
  paneli: lexo("paneli", window.innerWidth > 768 ? "1" : "0") === "1",
};
const t = k => TEKSTE[S.gjuha][k];
const $ = (sel, el = document) => el.querySelector(sel);
const esc = s => String(s ?? "").replace(/[&<>"']/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));

/* ================================================================ tema dhe gjuha */
const mqErret = window.matchMedia("(prefers-color-scheme: dark)");
function aplikoTemen() {
  const erret = S.tema === "dark" || (S.tema === "system" && mqErret.matches);
  document.documentElement.setAttribute("data-theme", erret ? "dark" : "light");
}
mqErret.addEventListener?.("change", aplikoTemen);
function vendosTemen(v) { S.tema = v; ruaj("tema", v); aplikoTemen(); }
function vendosGjuhen(v) { S.gjuha = v; ruaj("gjuha", v); document.documentElement.lang = v; vizato(); }

/* ================================================================ API */
async function api(metoda, url, trupi) {
  const r = await fetch(url, { method: metoda, headers: trupi ? { "Content-Type": "application/json" } : {},
    body: trupi ? JSON.stringify(trupi) : undefined, credentials: "same-origin" });
  let d = {};
  try { d = await r.json(); } catch (e) { /* pa trup */ }
  if (r.status === 401 && url !== "/api/hyr") { S.sesioni = { llogaria: null, vizitor: false }; vizato(); throw new Error(d.gabim || t("sessionEnded")); }
  if (!r.ok) throw new Error(d.gabim || `${t("error")} (${r.status})`);
  return d;
}

/* ================================================================ njoftime, menu, modale */
function toast(tekst, gabim = false) {
  const el = document.createElement("div");
  el.className = "toast" + (gabim ? " err" : "");
  el.textContent = tekst;
  $("#toasts").appendChild(el);
  setTimeout(() => el.remove(), gabim ? 5000 : 2200);
}

let menuAktive = null;
function mbyllMenune() { menuAktive?.remove(); menuAktive = null; document.querySelectorAll(".more.open").forEach(b => b.classList.remove("open")); }
function hapMenune(ankori, artikujt, { lart = false } = {}) {
  mbyllMenune();
  const m = document.createElement("div");
  m.className = "menu";
  m.innerHTML = artikujt.map((a, i) => a === "-" ? "<hr>" : a.koke ? `<div class="menu-head">${esc(a.koke)}</div>`
    : `<button data-i="${i}" class="${a.rrezik ? "danger" : ""}">${a.ikona ? ic(a.ikona) : ""}<span>${esc(a.tekst)}</span></button>`).join("");
  document.body.appendChild(m);
  const r = ankori.getBoundingClientRect();
  const w = Math.max(m.offsetWidth, 220);
  let left = Math.min(r.left, window.innerWidth - w - 8);
  m.style.left = Math.max(8, left) + "px";
  if (lart) m.style.bottom = (window.innerHeight - r.top + 6) + "px";
  else m.style.top = Math.min(r.bottom + 4, window.innerHeight - m.offsetHeight - 8) + "px";
  m.addEventListener("click", e => {
    const b = e.target.closest("button[data-i]");
    if (!b) return;
    const a = artikujt[+b.dataset.i];
    mbyllMenune();
    a.veprim();
  });
  menuAktive = m;
  setTimeout(() => document.addEventListener("click", mbyllMenune, { once: true }), 0);
}

function modal({ titull, trup, fund = "", gjere = false, pasHapjes }) {
  const o = document.createElement("div");
  o.className = "overlay";
  o.innerHTML = `<div class="modal${gjere ? " wide" : ""}" role="dialog" aria-modal="true">
    <div class="modal-head"><h2>${esc(titull)}</h2><button class="icon-btn" data-mbyll aria-label="${t("close")}">${ic("x")}</button></div>
    <div class="modal-body">${trup}</div>${fund ? `<div class="modal-foot">${fund}</div>` : ""}</div>`;
  const mbyll = () => { o.remove(); document.removeEventListener("keydown", esc_); };
  const esc_ = e => { if (e.key === "Escape") mbyll(); };
  o.addEventListener("mousedown", e => { if (e.target === o) mbyll(); });
  o.querySelectorAll("[data-mbyll]").forEach(b => b.addEventListener("click", mbyll));
  document.addEventListener("keydown", esc_);
  document.body.appendChild(o);
  syte(o);
  pasHapjes?.(o, mbyll);
  o.querySelector("input, textarea, select")?.focus();
  return { el: o, mbyll };
}

function konfirmo(pyetja, { butoni = t("del"), rrezik = true, pershkrimi = "" } = {}) {
  return new Promise(res => {
    const m = modal({ titull: pyetja, trup: pershkrimi ? `<p class="hint" style="margin:0">${esc(pershkrimi)}</p>` : "",
      fund: `<button class="btn" data-mbyll>${t("cancel")}</button>
      <button class="btn ${rrezik ? "danger" : "primary"}" data-po>${esc(butoni)}</button>`,
      pasHapjes: (o, mbyll) => {
        o.querySelector("[data-po]").addEventListener("click", () => { mbyll(); res(true); });
        o.querySelectorAll("[data-mbyll]").forEach(b => b.addEventListener("click", () => res(false)));
      } });
    if (!pershkrimi) m.el.querySelector(".modal-body").remove();
  });
}

/* ================================================================ markdown (i sigurt: escape para çdo gjëje) */
function inline(s) {
  return s
    .replace(/`([^`]+)`/g, "<code>$1</code>")
    .replace(/\*\*([^*]+?)\*\*/g, "<strong>$1</strong>")
    .replace(/(^|[^*])\*([^*\s][^*]*?)\*(?!\*)/g, "$1<em>$2</em>")
    .replace(/(^|\s)_([^_]+?)_(?=\s|$|[.,;:!?])/g, "$1<em>$2</em>")
    .replace(/\[([^\]]+)\]\((https?:\/\/[^\s)]+)\)/g, '<a href="$2" target="_blank" rel="noopener noreferrer">$1</a>');
}
function md(tekst) {
  const rreshta = esc(tekst || "").split("\n");
  let html = "", para = [], lista = null;
  const mbyllPara = () => { if (para.length) { html += `<p>${para.map(inline).join("<br>")}</p>`; para = []; } };
  const mbyllListe = () => { if (lista) { html += `<${lista.lloji}>${lista.el.map(x => `<li>${inline(x)}</li>`).join("")}</${lista.lloji}>`; lista = null; } };
  for (const r of rreshta) {
    let m;
    if (!r.trim()) { mbyllPara(); mbyllListe(); continue; }
    if ((m = r.match(/^\s*#{1,4}\s+(.*)$/))) { mbyllPara(); mbyllListe(); html += `<h4>${inline(m[1])}</h4>`; continue; }
    if ((m = r.match(/^\s*(?:[-*•])\s+(.*)$/)) || (m = r.match(/^\s*\d+[.)]\s+(.*)$/))) {
      const lloji = /^\s*\d/.test(r) ? "ol" : "ul";
      mbyllPara();
      if (lista && lista.lloji !== lloji) mbyllListe();
      if (!lista) lista = { lloji, el: [] };
      lista.el.push(m[1]);
      continue;
    }
    mbyllListe();
    para.push(r);
  }
  mbyllPara(); mbyllListe();
  return html;
}

/* ================================================================ vizatimi kryesor */
function vizato() {
  const root = $("#root");
  if (!S.sesioni) { root.innerHTML = ""; return; }
  if (!S.sesioni.llogaria && !S.sesioni.vizitor) { vizatoHyrjen(); return; }
  root.innerHTML = `<div class="app${S.paneli ? "" : " collapsed"}" id="app">
    <aside class="sidebar" id="sidebar"></aside>
    <div class="scrim" id="scrim"></div>
    <main class="main" id="main"></main></div>`;
  $("#scrim").addEventListener("click", () => nderroPanelin(false));
  vizatoPanelin();
  vizatoKryesoren();
}

function nderroPanelin(v) {
  S.paneli = v ?? !S.paneli;
  ruaj("paneli", S.paneli ? "1" : "0");
  $("#app")?.classList.toggle("collapsed", !S.paneli);
}

/* ---------------------------------------------------------------- hyrja */
/* Butoni i syrit: shfaq / fsheh fjalëkalimin te çdo fushë fjalëkalimi brenda `el`. */
function syte(el) {
  el.querySelectorAll('input[type="password"]').forEach(inp => {
    if (inp.parentElement.classList.contains("pw")) return;
    const w = document.createElement("div");
    w.className = "pw";
    inp.replaceWith(w);
    w.appendChild(inp);
    const b = document.createElement("button");
    b.type = "button";
    b.className = "pw-eye";
    b.setAttribute("aria-label", t("showPw"));
    b.title = t("showPw");
    b.innerHTML = ic("eye", 18);
    b.addEventListener("click", () => {
      const fshehur = inp.type === "password";
      inp.type = fshehur ? "text" : "password";
      b.innerHTML = ic(fshehur ? "eyeoff" : "eye", 18);
      b.title = fshehur ? t("hidePw") : t("showPw");
      b.setAttribute("aria-label", b.title);
      inp.focus();
    });
    w.appendChild(b);
  });
}

function vizatoHyrjen(skeda = "hyr", { token = null, mesazh = "" } = {}) {
  const reg = skeda === "regj", harrova = skeda === "harrova", rivendos = skeda === "rivendos";
  let forma;
  if (harrova) {
    forma = `<h1>${t("forgotTitle")}</h1><p class="sub">${t("forgotSub")}</p>
      <form id="auth-form" novalidate>
        <div class="field"><label for="f-email">${t("email")}</label><input class="input" id="f-email" type="email" autocomplete="email" required></div>
        <div class="error-text" id="f-err" role="alert"></div><div class="ok-text" id="f-ok" role="status"></div>
        <button class="btn primary block" style="height:44px;margin-top:.3rem" type="submit">${ic("mail", 16)}${t("sendLink")}</button>
      </form>
      <button class="link-btn" id="a-kthehu">${t("backToLogin")}</button>`;
  } else if (rivendos) {
    forma = `<h1>${t("resetTitle")}</h1><p class="sub">${t("resetSub")}</p>
      <form id="auth-form" novalidate>
        <div class="field"><label for="f-p">${t("newPw")}</label><input class="input" id="f-p" type="password" autocomplete="new-password" required></div>
        <div class="field"><label for="f-p2">${t("repeatPw")}</label><input class="input" id="f-p2" type="password" autocomplete="new-password" required></div>
        <div class="error-text" id="f-err" role="alert"></div>
        <button class="btn primary block" style="height:44px;margin-top:.3rem" type="submit">${t("save")}</button>
      </form>
      <button class="link-btn" id="a-kthehu">${t("backToLogin")}</button>`;
  } else {
    forma = `<h1>${t("welcome")}</h1><p class="sub">${t("welcomeSub")}</p>
      <div class="seg"><button class="${reg ? "" : "on"}" data-skeda="hyr">${t("login")}</button><button class="${reg ? "on" : ""}" data-skeda="regj">${t("register")}</button></div>
      ${mesazh ? `<div class="note info" style="margin:0 0 1rem">${esc(mesazh)}</div>` : ""}
      <form id="auth-form" novalidate>
        <div class="field"><label for="f-u">${reg ? t("username") : t("emailOrUser")}</label>
          <input class="input" id="f-u" autocomplete="username" required ${reg ? `aria-describedby="f-uh"` : ""}>
          ${reg ? `<span class="hint" id="f-uh">${t("usernameHelp")}</span>` : ""}</div>
        ${reg ? `<div class="field"><label for="f-email">${t("email")}</label><input class="input" id="f-email" type="email" autocomplete="email" required aria-describedby="f-eh">
            <span class="hint" id="f-eh">${t("emailHelp")}</span></div>
          <div class="field"><label for="f-m">${t("ageOpt")}</label><input class="input" id="f-m" type="number" min="0" max="110" inputmode="numeric"></div>` : ""}
        <div class="field"><div class="label-row"><label for="f-p">${reg ? t("newPw") : t("password")}</label>
            ${reg ? "" : `<button type="button" class="link-btn sm" id="a-harrova">${t("forgot")}</button>`}</div>
          <input class="input" id="f-p" type="password" autocomplete="${reg ? "new-password" : "current-password"}" required></div>
        ${reg ? `<div class="field"><label for="f-p2">${t("repeatPw")}</label><input class="input" id="f-p2" type="password" autocomplete="new-password"></div>
          <label class="check" style="margin-bottom:.9rem"><input type="checkbox" id="f-c"><span>${t("consent")}</span></label>` : ""}
        <div class="error-text" id="f-err" role="alert"></div>
        <button class="btn primary block" style="height:44px;margin-top:.3rem" type="submit">${reg ? t("createAccount") : t("login")}</button>
      </form>
      <div class="divider">${t("or")}</div>
      <button class="btn block" style="height:44px" id="a-vizitor">${t("continueGuest")}</button>
      <div class="feature-list">${["feat1", "feat2", "feat3"].map(k => `<div>${ic("check", 16)}<span>${t(k)}</span></div>`).join("")}</div>`;
  }
  $("#root").innerHTML = `<div class="auth">
    <div class="auth-top"><div class="brand"><img src="/assets/ikona.png" alt="">FarmaBot</div>
      <div style="display:flex;gap:.3rem">
        <button class="icon-btn" id="a-gjuha" title="${t("language")}" aria-label="${t("language")}">${ic("globe")}</button>
        <button class="icon-btn" id="a-tema" title="${t("theme")}" aria-label="${t("theme")}">${ic(document.documentElement.dataset.theme === "dark" ? "sun" : "moon")}</button>
      </div></div>
    <div class="auth-center"><div class="auth-card"><img class="logo" src="/assets/ikona.png" alt="">${forma}</div></div>
    <div class="auth-foot">${t("disclaimer")}</div></div>`;
  syte($("#root"));
  const rivizato = () => vizatoHyrjen(skeda, { token, mesazh });
  document.querySelectorAll("[data-skeda]").forEach(b => b.addEventListener("click", () => vizatoHyrjen(b.dataset.skeda)));
  $("#a-gjuha").addEventListener("click", () => { S.gjuha = S.gjuha === "sq" ? "en" : "sq"; ruaj("gjuha", S.gjuha); document.documentElement.lang = S.gjuha; rivizato(); });
  $("#a-tema").addEventListener("click", () => { vendosTemen(document.documentElement.dataset.theme === "dark" ? "light" : "dark"); rivizato(); });
  $("#a-vizitor")?.addEventListener("click", async () => { S.sesioni = await api("POST", "/api/vizitor"); await nisAplikacionin(); });
  $("#a-harrova")?.addEventListener("click", () => vizatoHyrjen("harrova"));
  $("#a-kthehu")?.addEventListener("click", () => { history.replaceState(null, "", "/"); vizatoHyrjen("hyr"); });

  $("#auth-form").addEventListener("submit", async e => {
    e.preventDefault();
    const err = $("#f-err"), btn = e.submitter || $("#auth-form button[type=submit]");
    err.textContent = "";
    btn.disabled = true;
    try {
      if (harrova) {
        const r = await api("POST", "/api/harrova", { email: $("#f-email").value.trim(), gjuha: S.gjuha });
        $("#f-ok").textContent = r.smtp ? t("linkSent") : t("smtpMissing");
        return;
      }
      if (rivendos) {
        if ($("#f-p").value !== $("#f-p2").value) { err.textContent = t("pwMismatch"); return; }
        await api("POST", "/api/rivendos", { token, fjalekalimi: $("#f-p").value });
        history.replaceState(null, "", "/");
        vizatoHyrjen("hyr", { mesazh: t("resetDone") });
        return;
      }
      const u = $("#f-u").value.trim(), p = $("#f-p").value;
      if (reg) {
        if (p !== $("#f-p2").value) { err.textContent = t("pwMismatch"); return; }
        S.sesioni = await api("POST", "/api/regjistrohu", { perdoruesi: u, email: $("#f-email").value.trim(), fjalekalimi: p,
          mosha: $("#f-m").value || null, pelqim: $("#f-c").checked });
      } else {
        S.sesioni = await api("POST", "/api/hyr", { perdoruesi: u, fjalekalimi: p });
      }
      await nisAplikacionin();
    } catch (x) { err.textContent = x.message; }
    finally { if (document.body.contains(btn)) btn.disabled = false; }
  });
  ($("#f-u") || $("#f-email") || $("#f-p"))?.focus();
}

/* ---------------------------------------------------------------- paneli anësor */
function grupet(lista) {
  const sot = new Date(); sot.setHours(0, 0, 0, 0);
  const dite = 86400000, g = { today: [], yesterday: [], week: [], month: [], older: [] };
  for (const b of lista) {
    const d = new Date(b.perditesuar || 0).getTime();
    const k = d >= sot ? "today" : d >= sot - dite ? "yesterday" : d >= sot - 7 * dite ? "week" : d >= sot - 30 * dite ? "month" : "older";
    g[k].push(b);
  }
  return g;
}

function vizatoPanelin() {
  const ses = S.sesioni, l = ses.llogaria;
  const emri = l ? (ses.profili?.emer || l.perdoruesi) : t("guest");
  const nistoret = emri.split(/\s+/).map(x => x[0]).join("").slice(0, 2).toUpperCase();
  $("#sidebar").innerHTML = `
    <div class="sb-top"><div class="brand"><img src="/assets/ikona.png" alt="">FarmaBot</div>
      <button class="icon-btn" id="sb-mbyll" title="${t("toggleSidebar")} (Ctrl+B)" aria-label="${t("toggleSidebar")}">${ic("panel")}</button></div>
    <div class="sb-actions"><button class="sb-item" id="sb-re">${ic("newchat")}<span>${t("newChat")}</span></button>
      ${l?.roli === "admin" ? `<button class="sb-item${S.pamja === "admin" ? " active" : ""}" id="sb-admin">${ic("shield")}<span>${t("admin")}</span></button>` : ""}</div>
    <div class="sb-search">${ic("search", 15)}<input id="sb-kerko" placeholder="${t("search")}" value="${esc(S.kerkimi)}" aria-label="${t("search")}"></div>
    <nav class="sb-list" id="sb-lista" aria-label="${t("search")}"></nav>
    <div class="sb-bottom"><button class="user-btn" id="sb-user">
      <span class="avatar${l ? "" : " guest"}">${l ? esc(nistoret) : ic("user", 16)}</span>
      <span style="min-width:0"><span class="nm" style="display:block;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">${esc(emri)}</span>
      <span class="rl">${l ? (l.roli === "admin" ? t("administrator") : t("user")) : t("guestNote").split(":")[0]}</span></span></button></div>`;
  $("#sb-mbyll").addEventListener("click", () => nderroPanelin(false));
  $("#sb-re").addEventListener("click", bisedeERe);
  $("#sb-admin")?.addEventListener("click", () => { S.pamja = "admin"; location.hash = "#/admin"; vizatoPanelin(); vizatoKryesoren(); mbyllNeCelular(); });
  $("#sb-kerko").addEventListener("input", e => { S.kerkimi = e.target.value; vizatoListen(); });
  $("#sb-user").addEventListener("click", e => { e.stopPropagation(); menuPerdoruesit(e.currentTarget); });
  vizatoListen();
}

function mbyllNeCelular() { if (window.innerWidth <= 768) nderroPanelin(false); }

function vizatoListen() {
  const q = S.kerkimi.trim().toLowerCase();
  const lista = S.bisedat.filter(b => !q || (b.titull || "").toLowerCase().includes(q));
  const el = $("#sb-lista");
  if (!el) return;
  if (!lista.length) { el.innerHTML = `<div class="sb-empty">${q ? t("noResults") : t("noChats")}</div>`; return; }
  const g = grupet(lista);
  el.innerHTML = Object.entries(g).filter(([, v]) => v.length).map(([k, v]) =>
    `<div class="sb-group">${t(k)}</div>` + v.map(b => `<div class="conv${S.aktive?.id === b.id && S.pamja === "biseda" ? " active" : ""}" data-id="${esc(b.id)}">
      <a href="#/c/${esc(b.id)}" title="${esc(b.titull)}">${esc(b.titull)}</a>
      <button class="icon-btn sm more" aria-label="${t("rename")}, ${t("del")}">${ic("more", 16)}</button></div>`).join("")).join("");
  el.querySelectorAll(".conv").forEach(c => {
    const id = c.dataset.id, b = S.bisedat.find(x => x.id === id);
    c.querySelector("a").addEventListener("click", e => { e.preventDefault(); hapBiseden(id); });
    c.querySelector(".more").addEventListener("click", e => {
      e.stopPropagation();
      e.currentTarget.classList.add("open");
      hapMenune(e.currentTarget, [
        { tekst: t("rename"), ikona: "pencil", veprim: () => riemerto(c, b) },
        { tekst: t("export"), ikona: "download", veprim: async () => eksporto(b.id) },
        "-",
        { tekst: t("del"), ikona: "trash", rrezik: true, veprim: () => fshiBiseden(b) },
      ]);
    });
  });
}

function riemerto(c, b) {
  c.innerHTML = `<input value="${esc(b.titull)}" maxlength="80" aria-label="${t("rename")}">`;
  const inp = c.querySelector("input");
  inp.focus(); inp.select();
  let kryer = false;
  const perfundo = async ruajNe => {
    if (kryer) return; kryer = true;
    const v = inp.value.trim();
    if (ruajNe && v && v !== b.titull) {
      try { await api("PATCH", `/api/bisedat/${b.id}`, { titull: v }); b.titull = v; if (S.aktive?.id === b.id) { S.aktive.titull = v; vizatoKoken(); } }
      catch (x) { toast(x.message, true); }
    }
    vizatoListen();
  };
  inp.addEventListener("keydown", e => { if (e.key === "Enter") perfundo(true); if (e.key === "Escape") perfundo(false); });
  inp.addEventListener("blur", () => perfundo(true));
}

async function fshiBiseden(b) {
  if (!await konfirmo(t("confirmDeleteChat")(b.titull), { pershkrimi: S.sesioni?.llogaria ? t("chatDeleteNote") : "" })) return;
  try {
    await api("DELETE", `/api/bisedat/${b.id}`);
    S.bisedat = S.bisedat.filter(x => x.id !== b.id);
    if (S.aktive?.id === b.id) bisedeERe(); else vizatoListen();
  } catch (x) { toast(x.message, true); }
}

function menuPerdoruesit(ankori) {
  const l = S.sesioni.llogaria;
  const art = [];
  if (l) art.push({ koke: l.perdoruesi });
  art.push({ tekst: t("healthProfile"), ikona: "heart", veprim: () => hapCilesimet("profili") });
  art.push({ tekst: t("settings"), ikona: "settings", veprim: () => hapCilesimet("pergjithshme") });
  if (l?.roli === "admin") art.push({ tekst: t("admin"), ikona: "shield", veprim: () => $("#sb-admin").click() });
  art.push("-");
  art.push(l ? { tekst: t("signOut"), ikona: "logout", veprim: dil } : { tekst: t("signIn"), ikona: "login", veprim: dil });
  hapMenune(ankori, art, { lart: true });
}

async function dil() {
  try { await api("POST", "/api/dil"); } catch (e) { /* gjithsesi dalim */ }
  S.sesioni = { llogaria: null, vizitor: false }; S.bisedat = []; S.aktive = null; S.pamja = "biseda";
  history.replaceState(null, "", "/");
  vizato();
}

/* ---------------------------------------------------------------- pjesa kryesore */
function vizatoKryesoren() {
  if (S.pamja === "admin" && S.sesioni.llogaria?.roli === "admin") { vizatoAdminin(); return; }
  S.pamja = "biseda";
  const bosh = !S.aktive || !S.aktive.mesazhet.length;
  $("#main").innerHTML = `<header class="topbar" id="koka"></header>
    ${bosh ? `<div class="empty" id="bosh"><h1>${esc(pershendetja())}</h1>${htmlFusha()}
       <div class="suggestions">${t("sugg").map(s => `<button>${esc(s)}</button>`).join("")}</div></div>`
           : `<div class="thread" id="thread"><div class="thread-inner" id="mesazhet"></div></div>${htmlFusha()}`}`;
  vizatoKoken();
  lidhFushen();
  if (bosh) {
    document.querySelectorAll(".suggestions button").forEach(b => b.addEventListener("click", () => dergo(b.textContent)));
  } else {
    const el = $("#mesazhet");
    let pyetja = "";
    S.aktive.mesazhet.forEach((m, i) => {
      el.appendChild(elMesazhi(m, i === S.aktive.mesazhet.length - 1, pyetja));
      if (m.role === "user") pyetja = m.content;
    });
    poshte(false);
  }
}

function pershendetja() {
  const emri = S.sesioni.llogaria ? (S.sesioni.profili?.emer || "").split(/\s+/)[0] : "";
  if (!emri) return t("helpQ");
  const ora = new Date().getHours();
  return `${t("greeting")[ora >= 4 && ora < 12 ? 0 : ora < 18 ? 1 : 2]}, ${emri}`;
}

function vizatoKoken() {
  const k = $("#koka");
  if (!k) return;
  const titull = S.pamja === "admin" ? t("admin") : (S.aktive?.titull || "FarmaBot");
  k.innerHTML = `<button class="icon-btn only-collapsed" id="k-paneli" title="${t("toggleSidebar")} (Ctrl+B)" aria-label="${t("toggleSidebar")}">${ic("panel")}</button>
    <button class="icon-btn only-collapsed" id="k-re" title="${t("newChat")}" aria-label="${t("newChat")}">${ic("newchat")}</button>
    <div class="title">${esc(titull)}</div><div class="spacer"></div>
    ${S.aktive?.id && S.pamja === "biseda" ? `<button class="icon-btn" id="k-shkarko" title="${t("export")}" aria-label="${t("export")}">${ic("download")}</button>` : ""}
    <button class="icon-btn" id="k-tema" title="${t("theme")}" aria-label="${t("theme")}">${ic(document.documentElement.dataset.theme === "dark" ? "sun" : "moon")}</button>`;
  $("#k-paneli").addEventListener("click", () => nderroPanelin(true));
  $("#k-re").addEventListener("click", bisedeERe);
  $("#k-shkarko")?.addEventListener("click", () => eksporto(S.aktive.id));
  $("#k-tema").addEventListener("click", () => { vendosTemen(document.documentElement.dataset.theme === "dark" ? "light" : "dark"); vizatoKoken(); });
}

function htmlFusha() {
  return `<div class="composer-wrap"><form class="composer" id="fusha">
      <textarea id="teksti" rows="1" placeholder="${t("placeholder")}" aria-label="${t("placeholder")}"></textarea>
      <div class="composer-tools">
        <button type="button" class="pill${S.mendo ? " on" : ""}" id="mendo" title="${esc(t("thinkHelp"))}" aria-pressed="${S.mendo}">${ic("bulb", 16)}<span>${t("think")}</span></button>
        <button type="submit" class="send" id="dergo" disabled aria-label="${t("scSend")}">${ic("up", 18)}</button>
      </div></form><div class="disclaimer">${t("disclaimer")}</div></div>`;
}

function lidhFushen() {
  const ta = $("#teksti"), btn = $("#dergo");
  const rregullo = () => { ta.style.height = "auto"; ta.style.height = Math.min(ta.scrollHeight, 220) + "px"; btn.disabled = !ta.value.trim() || S.duke_pritur; };
  ta.addEventListener("input", rregullo);
  ta.addEventListener("keydown", e => { if (e.key === "Enter" && !e.shiftKey && !e.isComposing) { e.preventDefault(); if (!btn.disabled) $("#fusha").requestSubmit(); } });
  $("#fusha").addEventListener("submit", e => { e.preventDefault(); const v = ta.value.trim(); if (v && !S.duke_pritur) { ta.value = ""; rregullo(); dergo(v); } });
  $("#mendo").addEventListener("click", e => { S.mendo = !S.mendo; ruaj("mendo", S.mendo ? "1" : "0"); e.currentTarget.classList.toggle("on", S.mendo); e.currentTarget.setAttribute("aria-pressed", S.mendo); });
  if (window.innerWidth > 768) ta.focus();
}

function poshte(butë = true) {
  const th = $("#thread");
  if (th) { th.style.scrollBehavior = butë ? "smooth" : "auto"; th.scrollTop = th.scrollHeight; }
}

/* ---------------------------------------------------------------- mesazhet */
function etiketat(gj) { return TEKSTE[gj === "en" ? "en" : "sq"]; }

function htmlKartat(d) {
  if (!d || d.urgjence) return "";
  const E = etiketat(d.gjuha);
  let h = "";
  for (const b of d.barnat || []) {
    const fushat = d.pa_doza ? "" : `<div class="kv">${[[E.dose, b.doza], [E.max, b.doza_maks], [E.duration, b.kohezgjatja], [E.how, b.si_merret]]
      .filter(([, v]) => v).map(([k, v]) => `<div><small>${esc(k)}</small><span>${esc(v)}</span></div>`).join("")}</div>`;
    const kujdes = (b.kujdes_profili || []).map(k => `<div class="note warn"><strong>${esc(k.gjendje)}:</strong> ${esc(k.arsye)}</div>`).join("");
    const paral = [...(b.paralajmerime || []).map(esc), ...(b.efekte_anesore || []).map(x => `${esc(E.sideEffect)}: ${esc(x)}`)];
    h += `<div class="card"><div class="card-head"><div class="card-ico">${ic("pill", 18)}</div><div>
        <div class="card-title">${esc(b.emer)}</div><div class="card-sub">${esc([b.lende_aktive, b.forma].filter(Boolean).join(" · "))}</div></div></div>
      ${(b.emra_tregtare || []).length ? `<div class="chips">${b.emra_tregtare.map(x => `<span class="chip">${esc(x)}</span>`).join("")}</div>` : ""}
      ${fushat}${d.pa_doza ? `<div class="note info">${esc(E.child)}</div>` : ""}${kujdes}
      ${paral.length ? `<details class="more-info"><summary>${ic("chev", 14)}${esc(E.warnings)}</summary><ul>${paral.map(x => `<li>${x}</li>`).join("")}</ul></details>` : ""}</div>`;
  }
  if ((d.te_perjashtuara || []).length)
    h += `<div class="card excluded"><div class="card-title">${esc(E.notForYou)}</div><ul>${d.te_perjashtuara.map(x => `<li><strong>${esc(x.emer)}:</strong> ${esc(x.arsye)}</li>`).join("")}</ul></div>`;
  if ((d.alarmi || []).length)
    h += `<div class="card alarm"><details><summary>${ic("chev", 14)}${esc(E.whenDoctor)}</summary><ul>${d.alarmi.flatMap(s => s.shenjat.map(a => `<li><strong>${esc(s.emer)}:</strong> ${esc(a)}</li>`)).join("")}</ul></details></div>`;
  for (const f of d.fleteudhezuesit || [])
    h += `<div class="card leaflet"><details><summary>${ic("chev", 14)}${esc(E.leaflet(f.emer))}</summary>${f.seksione.map(s => `<div class="sec"><b>${esc(s.titull)}</b><p>${esc(s.tekst)}</p></div>`).join("")}
      ${f.url ? `<div class="sec"><a href="${esc(f.url)}" target="_blank" rel="noopener noreferrer">DailyMed</a></div>` : ""}</details></div>`;
  let burime = "";
  if ((d.burime || []).length)
    burime = `<div class="sources">${esc(E.sources)}: ${d.burime.map(b => b.url && /^https?:/.test(b.url) ? `<a href="${esc(b.url)}" target="_blank" rel="noopener noreferrer">${esc(b.emer)}</a>` : esc(b.emer)).join(", ")}</div>`;
  return (h ? `<div class="cards">${h}</div>` : "") + burime;
}

function htmlMendimi(d) {
  if (!d || !(d.hapat || []).length) return "";
  const E = etiketat(d.gjuha);
  const koha = E.seconds(d.sekonda || 0);
  const titull = d.mendimi ? E.thoughtFor(koha) : E.answered(koha);
  return `<div class="thought"><button class="thought-toggle" type="button">${esc(titull)}${ic("chev", 14)}</button>
    <div class="thought-body"><ol>${d.hapat.map(h => `<li>${md(h).replace(/^<p>|<\/p>$/g, "")}</li>`).join("")}</ol>
    ${d.mendimi ? `<div class="reason"><strong>${esc(E.reasoning)}</strong>\n${esc(d.mendimi)}</div>` : ""}</div></div>`;
}

function htmlVeprimet(bot = false) {
  return `<div class="msg-actions"><button class="icon-btn sm" data-kopjo title="${t("copy")}" aria-label="${t("copy")}">${ic("copy", 15)}</button>
    ${bot ? `<button class="icon-btn sm" data-reagim="1" title="${t("good")}" aria-label="${t("good")}">${ic("thumbup", 15)}</button>
    <button class="icon-btn sm" data-reagim="-1" title="${t("bad")}" aria-label="${t("bad")}">${ic("thumbdown", 15)}</button>` : ""}</div>`;
}

async function dergoReagimin(el, vlera, m, pyetja, trupi = {}) {
  await api("POST", "/api/reagim", { vlera, pyetja, pergjigjja: m.content, gjuha: m.te_dhena?.gjuha || S.gjuha,
    simptomat: (m.te_dhena?.alarmi || []).map(x => x.emer), ...trupi });
  el.querySelectorAll("[data-reagim]").forEach(b => { b.disabled = true; b.classList.toggle("on", +b.dataset.reagim === vlera); });
  toast(t("thanksFb"));
}

function hapAnkesen(el, m, pyetja) {
  const arsyet = ["r_nuk_kuptoi", "r_ilac_gabim", "r_e_paqarte", "r_tjeter"];
  modal({ titull: t("whatWrong"),
    trup: `<div style="display:grid;gap:.5rem;margin-bottom:1rem">${arsyet.map((a, i) =>
        `<label class="check"><input type="radio" name="arsye" value="${a.slice(2)}" ${i === 0 ? "checked" : ""}><span>${t(a)}</span></label>`).join("")}</div>
      <div class="field"><label for="fb-k">${t("commentOpt")}</label><textarea class="input" id="fb-k" maxlength="1000"></textarea></div>
      <div class="error-text" id="fb-err"></div>`,
    fund: `<button class="btn" data-mbyll>${t("cancel")}</button><button class="btn primary" id="fb-ok">${t("send")}</button>`,
    pasHapjes: (o, mbyll) => o.querySelector("#fb-ok").addEventListener("click", async () => {
      try {
        await dergoReagimin(el, -1, m, pyetja, { arsye: o.querySelector("input[name=arsye]:checked").value, koment: o.querySelector("#fb-k").value });
        mbyll();
      } catch (x) { o.querySelector("#fb-err").textContent = x.message; }
    }) });
}

function lidhVeprimet(el, tekst, m = null, pyetja = "") {
  el.querySelectorAll("[data-reagim]").forEach(b => b.addEventListener("click", async () => {
    if (+b.dataset.reagim === -1) { hapAnkesen(el, m, pyetja); return; }
    try { await dergoReagimin(el, 1, m, pyetja); } catch (x) { toast(x.message, true); }
  }));
  el.querySelector("[data-kopjo]")?.addEventListener("click", async e => {
    const b = e.currentTarget;
    try { await navigator.clipboard.writeText(tekst); b.innerHTML = ic("check", 15); toast(t("copied")); setTimeout(() => (b.innerHTML = ic("copy", 15)), 1500); }
    catch (x) { toast(x.message, true); }
  });
  el.querySelector(".thought-toggle")?.addEventListener("click", e => e.currentTarget.parentElement.classList.toggle("open"));
}

function elMesazhi(m, iFundit = false, pyetja = "") {
  const el = document.createElement("div");
  if (m.role === "user") {
    el.className = "msg user";
    el.innerHTML = `<div class="bubble">${esc(m.content)}</div>${htmlVeprimet()}`;
  } else {
    const d = m.te_dhena;
    el.className = "msg bot" + (iFundit ? " last" : "");
    const trupi = d?.urgjence
      ? `<div class="alert danger" role="alert">${ic("alert", 20)}<div class="md">${md(m.content)}</div></div>`
      : `<div class="md">${md(m.content)}</div>`;
    el.innerHTML = htmlMendimi(d) + trupi + htmlKartat(d) + htmlVeprimet(true);
  }
  lidhVeprimet(el, m.content, m, pyetja);
  return el;
}

/* ---------------------------------------------------------------- dërgimi (live) */
async function dergo(tekst) {
  if (S.duke_pritur) return;
  if (!S.aktive) S.aktive = { id: null, titull: null, mesazhet: [] };
  const ishteBosh = !S.aktive.mesazhet.length;
  S.aktive.mesazhet.push({ role: "user", content: tekst });
  if (ishteBosh) vizatoKryesoren();
  else { document.querySelector(".msg.last")?.classList.remove("last"); $("#mesazhet").appendChild(elMesazhi({ role: "user", content: tekst })); }

  S.duke_pritur = true;
  $("#dergo").disabled = true;
  const bot = document.createElement("div");
  bot.className = "msg bot last";
  bot.innerHTML = `<div class="thought open live"><div class="thought-toggle"><span class="shimmer" id="hapi">${esc(S.mendo ? t("thinking") : t("searching"))}…</span></div>
    <div class="live-reason" id="arsyeja" hidden></div></div><div class="dots" id="pikat"><i></i><i></i><i></i></div>`;
  $("#mesazhet").appendChild(bot);
  poshte();

  let arsyeja = "", fundi = null;
  try {
    const r = await fetch("/api/biseda", { method: "POST", headers: { "Content-Type": "application/json" }, credentials: "same-origin",
      body: JSON.stringify({ mesazh: tekst, bisede_id: S.aktive.id, mendo: S.mendo, gjuha: S.gjuha }) });
    if (!r.ok) { let d = {}; try { d = await r.json(); } catch (e) { /* */ } throw new Error(d.gabim || `${t("error")} (${r.status})`); }
    const lexuesi = r.body.getReader(), dek = new TextDecoder();
    let mbetja = "";
    for (;;) {
      const { value, done } = await lexuesi.read();
      if (done) break;
      mbetja += dek.decode(value, { stream: true });
      let i;
      while ((i = mbetja.indexOf("\n")) >= 0) {
        const rresht = mbetja.slice(0, i).trim(); mbetja = mbetja.slice(i + 1);
        if (!rresht) continue;
        const ev = JSON.parse(rresht);
        if (ev.lloji === "bisede") {
          if (!S.aktive.id) {
            S.aktive.id = ev.id; S.aktive.titull = ev.titull;
            S.bisedat.unshift({ id: ev.id, titull: ev.titull, perditesuar: new Date().toISOString() });
            history.replaceState(null, "", `#/c/${ev.id}`);
            vizatoListen(); vizatoKoken();
          }
        } else if (ev.lloji === "hap") {
          const h = $("#hapi", bot); if (h) h.textContent = ev.tekst.replace(/\s*·\s*\d+\s*s$/, "");
        } else if (ev.lloji === "mendim") {
          arsyeja += ev.tekst;
          const a = $("#arsyeja", bot); if (a) { a.hidden = false; a.textContent = arsyeja.slice(-600); }
        } else if (ev.lloji === "fund") {
          fundi = ev;
        } else if (ev.lloji === "gabim") {
          throw new Error(ev.tekst);
        }
      }
    }
    if (!fundi) throw new Error(t("error"));
    const m = { role: "assistant", content: fundi.pergjigja.tekst, te_dhena: fundi.pergjigja };
    S.aktive.mesazhet.push(m);
    bot.replaceWith(elMesazhi(m, true, tekst));
    if (fundi.profili) S.sesioni.profili = fundi.profili;
    const b = S.bisedat.find(x => x.id === S.aktive.id);
    if (b) { b.perditesuar = new Date().toISOString(); S.bisedat = [b, ...S.bisedat.filter(x => x !== b)]; vizatoListen(); }
  } catch (x) {
    bot.innerHTML = `<div class="alert danger" role="alert">${ic("alert", 20)}<div><strong>${esc(t("error"))}</strong><br>${esc(x.message)}<br><span class="muted">${esc(t("serviceErr"))}</span></div></div>`;
  } finally {
    S.duke_pritur = false;
    const ta = $("#teksti"); if (ta) $("#dergo").disabled = !ta.value.trim();
    poshte();
  }
}

/* ---------------------------------------------------------------- bisedat */
function bisedeERe() {
  S.aktive = null; S.pamja = "biseda";
  history.replaceState(null, "", "/");
  vizatoPanelin(); vizatoKryesoren(); mbyllNeCelular();
}

async function hapBiseden(id) {
  if (S.duke_pritur) return;
  try {
    const d = await api("GET", `/api/bisedat/${id}`);
    const b = S.bisedat.find(x => x.id === id);
    S.aktive = { id, titull: b?.titull || "FarmaBot", mesazhet: d.mesazhet };
    S.pamja = "biseda";
    history.replaceState(null, "", `#/c/${id}`);
    vizatoPanelin(); vizatoKryesoren(); mbyllNeCelular();
  } catch (x) { toast(x.message, true); bisedeERe(); }
}

async function eksporto(id) {
  try {
    const d = id === S.aktive?.id ? S.aktive : { ...(await api("GET", `/api/bisedat/${id}`)), titull: S.bisedat.find(x => x.id === id)?.titull };
    const rr = [`# ${d.titull || "FarmaBot"}`, "", `_${new Date().toLocaleString()}_`, ""];
    for (const m of d.mesazhet) rr.push(`**${m.role === "user" ? (S.gjuha === "en" ? "You" : "Ti") : "FarmaBot"}:**`, "", m.content, "");
    rr.push(`_${t("disclaimer")}_`);
    const a = document.createElement("a");
    a.href = URL.createObjectURL(new Blob([rr.join("\n")], { type: "text/markdown" }));
    a.download = `farmabot-${(d.titull || "biseda").toLowerCase().replace(/[^\p{L}\p{N}]+/gu, "-").slice(0, 40)}.md`;
    a.click();
    setTimeout(() => URL.revokeObjectURL(a.href), 1000);
  } catch (x) { toast(x.message, true); }
}

/* ---------------------------------------------------------------- cilësimet */
function hapCilesimet(skeda = "pergjithshme") {
  const l = S.sesioni.llogaria;
  const nav = [["pergjithshme", "settings", t("general")], ["profili", "heart", t("healthProfile")], ["llogaria", "user", t("account")]];
  const m = modal({ titull: t("settings"), gjere: true, trup: `<div class="settings"><nav>${nav.map(([k, i, e]) =>
      `<button data-s="${k}" class="${k === skeda ? "on" : ""}">${ic(i, 16)}<span>${esc(e)}</span></button>`).join("")}</nav><section id="s-trupi"></section></div>`,
    pasHapjes: o => {
      o.querySelector(".modal-body").style.padding = "0";
      o.querySelectorAll("[data-s]").forEach(b => b.addEventListener("click", () => {
        o.querySelectorAll("[data-s]").forEach(x => x.classList.toggle("on", x === b)); skedaCilesimeve(b.dataset.s, o);
      }));
    } });
  skedaCilesimeve(skeda, m.el);
}

function skedaCilesimeve(skeda, o) {
  const el = o.querySelector("#s-trupi"), l = S.sesioni.llogaria;
  if (skeda === "pergjithshme") {
    el.innerHTML = `
      <div class="row"><div class="lbl">${t("theme")}</div><div class="seg" id="s-tema">
        ${[["system", "monitor", t("themeSystem")], ["light", "sun", t("themeLight")], ["dark", "moon", t("themeDark")]].map(([v, i, e]) =>
          `<button data-v="${v}" class="${S.tema === v ? "on" : ""}">${ic(i, 15)}${esc(e)}</button>`).join("")}</div></div>
      <div class="row"><div class="lbl">${t("language")}</div><div class="seg" id="s-gjuha">
        <button data-v="sq" class="${S.gjuha === "sq" ? "on" : ""}">Shqip</button><button data-v="en" class="${S.gjuha === "en" ? "on" : ""}">English</button></div></div>
      <div class="row"><div class="lbl">${t("thinkDefault")}<small>${t("thinkDefaultHelp")}</small></div>
        <button class="switch${S.mendo ? " on" : ""}" id="s-mendo" role="switch" aria-checked="${S.mendo}" aria-label="${t("thinkDefault")}"></button></div>
      <div class="row" style="display:block"><div class="lbl" style="margin-bottom:.6rem">${t("shortcuts")}</div>
        <div style="display:grid;grid-template-columns:1fr auto;gap:.5rem;font-size:.88rem;color:var(--text-2)">
        <span>${t("scNew")}</span><span><span class="kbd">Ctrl</span> <span class="kbd">Shift</span> <span class="kbd">O</span></span>
        <span>${t("scSidebar")}</span><span><span class="kbd">Ctrl</span> <span class="kbd">B</span></span>
        <span>${t("scSend")}</span><span><span class="kbd">Enter</span></span>
        <span>${t("scNewline")}</span><span><span class="kbd">Shift</span> <span class="kbd">Enter</span></span></div></div>`;
    el.querySelectorAll("#s-tema button").forEach(b => b.addEventListener("click", () => {
      vendosTemen(b.dataset.v); el.querySelectorAll("#s-tema button").forEach(x => x.classList.toggle("on", x === b)); vizatoKoken();
    }));
    el.querySelectorAll("#s-gjuha button").forEach(b => b.addEventListener("click", () => {
      o.remove(); vendosGjuhen(b.dataset.v); hapCilesimet("pergjithshme");
    }));
    el.querySelector("#s-mendo").addEventListener("click", e => {
      S.mendo = !S.mendo; ruaj("mendo", S.mendo ? "1" : "0");
      e.currentTarget.classList.toggle("on", S.mendo); e.currentTarget.setAttribute("aria-checked", S.mendo);
      $("#mendo")?.classList.toggle("on", S.mendo);
    });
  } else if (skeda === "profili") {
    const p = S.sesioni.profili || { mosha: null, gjendjet: [], shenime: "" };
    const zgj = new Set(p.gjendjet || []);
    el.innerHTML = `<p class="hint" style="margin:.2rem 0 1rem">${t("profileNote")}${l ? "" : " " + t("guestNote")}</p>
      <div class="field" style="max-width:160px"><label for="p-m">${t("age")}</label><input class="input" id="p-m" type="number" min="0" max="110" inputmode="numeric" placeholder="${t("agePh")}" value="${p.mosha ?? ""}"></div>
      <div class="field"><label>${t("conditions")}</label><input class="input" id="p-f" placeholder="${t("filter")}" style="height:36px;margin-bottom:.4rem">
        <div class="cond-grid" id="p-gj">${S.sesioni.gjendjet.map(g => `<label class="check" data-emer="${esc(g.emer.toLowerCase())}"><input type="checkbox" value="${esc(g.id)}" ${zgj.has(g.id) ? "checked" : ""}><span>${esc(g.emer)}</span></label>`).join("")}</div></div>
      <div class="field"><label for="p-s">${t("allergies")}</label><textarea class="input" id="p-s" placeholder="${t("allergiesPh")}" maxlength="500">${esc(p.shenime || "")}</textarea></div>
      <div class="error-text" id="p-err"></div>
      <div style="display:flex;justify-content:flex-end"><button class="btn primary" id="p-ruaj">${t("save")}</button></div>`;
    el.querySelector("#p-f").addEventListener("input", e => {
      const q = e.target.value.toLowerCase();
      el.querySelectorAll("#p-gj .check").forEach(c => (c.style.display = c.dataset.emer.includes(q) ? "" : "none"));
    });
    el.querySelector("#p-ruaj").addEventListener("click", async () => {
      try {
        const d = await api("PUT", "/api/profili", { mosha: el.querySelector("#p-m").value || null, shenime: el.querySelector("#p-s").value,
          gjendjet: [...el.querySelectorAll("#p-gj input:checked")].map(x => x.value) });
        S.sesioni.profili = { ...S.sesioni.profili, ...d.profili };
        toast(t("saved")); vizatoPanelin();
      } catch (x) { el.querySelector("#p-err").textContent = x.message; }
    });
  } else {
    if (!l) {
      el.innerHTML = `<div class="row"><div class="lbl">${t("guest")}<small>${t("guestNote")}</small></div><button class="btn primary" id="l-hyr">${t("signIn")}</button></div>`;
      el.querySelector("#l-hyr").addEventListener("click", () => { o.remove(); dil(); });
      return;
    }
    el.innerHTML = `
      <div class="row"><div class="lbl">${t("username")}<small>${esc(l.perdoruesi)}</small></div><span class="badge${l.roli === "admin" ? " admin" : ""}">${l.roli === "admin" ? t("administrator") : t("user")}</span></div>
      <div class="row" style="display:block"><div class="lbl" style="margin-bottom:.7rem">${t("email")}${l.email ? "" : `<small>${t("noEmail")}</small>`}</div>
        <div class="field"><input class="input" id="l-email" type="email" autocomplete="email" value="${esc(l.email || "")}" placeholder="emri@gmail.com" aria-label="${t("email")}"></div>
        <div class="field"><label for="l-ep">${t("currentPw")}</label><input class="input" id="l-ep" type="password" autocomplete="current-password"></div>
        <div class="error-text" id="l-eerr"></div><button class="btn" id="l-eruaj">${ic("mail", 16)}${t("saveEmail")}</button></div>
      <div class="row" style="display:block"><div class="lbl" style="margin-bottom:.7rem">${t("changePw")}</div>
        <div class="field"><label for="l-a">${t("currentPw")}</label><input class="input" id="l-a" type="password" autocomplete="current-password"></div>
        <div class="field"><label for="l-r">${t("newPw")}</label><input class="input" id="l-r" type="password" autocomplete="new-password"></div>
        <div class="error-text" id="l-err"></div><button class="btn" id="l-ndrysho">${ic("key", 16)}${t("changePw")}</button></div>
      <div class="row"><div class="lbl">${t("deleteAccount")}<small>${t("deleteAccountHelp")}</small></div><button class="btn danger" id="l-fshi">${t("del")}</button></div>`;
    syte(el);
    el.querySelector("#l-eruaj").addEventListener("click", async () => {
      const err = el.querySelector("#l-eerr"); err.textContent = "";
      try {
        const r = await api("PUT", "/api/email", { email: el.querySelector("#l-email").value, fjalekalimi: el.querySelector("#l-ep").value });
        l.email = r.email; el.querySelector("#l-ep").value = ""; toast(t("emailSaved"));
      } catch (x) { err.textContent = x.message; }
    });
    el.querySelector("#l-ndrysho").addEventListener("click", async () => {
      const err = el.querySelector("#l-err"); err.textContent = "";
      try { await api("POST", "/api/fjalekalimi", { aktual: el.querySelector("#l-a").value, i_ri: el.querySelector("#l-r").value });
        toast(t("pwChanged")); el.querySelector("#l-a").value = el.querySelector("#l-r").value = ""; }
      catch (x) { err.textContent = x.message; }
    });
    el.querySelector("#l-fshi").addEventListener("click", async () => {
      if (!await konfirmo(t("confirmDeleteAccount"))) return;
      try { await api("DELETE", "/api/llogaria"); o.remove(); dil(); } catch (x) { toast(x.message, true); }
    });
  }
}

/* ================================================================ admin */
function vizatoAdminin() {
  const skedat = [["permbledhje", t("overview")], ["perdoruesit", t("users")], ["barnat", t("medicines")], ["trajnimi", t("training")], ["backup", t("backup")]];
  $("#main").innerHTML = `<header class="topbar" id="koka"></header><div class="admin"><div class="admin-inner">
    <div class="tabs" role="tablist">${skedat.map(([k, e]) => `<button role="tab" data-t="${k}" class="${S.adminTab === k ? "on" : ""}">${esc(e)}</button>`).join("")}</div>
    <div id="a-trupi"><div class="dots"><i></i><i></i><i></i></div></div></div></div>`;
  vizatoKoken();
  document.querySelectorAll("[data-t]").forEach(b => b.addEventListener("click", () => { S.adminTab = b.dataset.t; location.hash = `#/admin/${b.dataset.t}`; vizatoAdminin(); }));
  ({ permbledhje: aPermbledhje, perdoruesit: aPerdoruesit, barnat: aBarnat, trajnimi: aTrajnimi, backup: aBackup })[S.adminTab]()
    .catch(x => { $("#a-trupi").innerHTML = `<div class="alert danger">${ic("alert", 20)}<div>${esc(x.message)}</div></div>`; });
}

function tabele(kolonat, rreshtat) {
  return `<div class="table-wrap"><table><thead><tr>${kolonat.map(k => `<th>${esc(k)}</th>`).join("")}</tr></thead>
    <tbody>${rreshtat.join("") || `<tr><td colspan="${kolonat.length}" class="muted">${t("noData")}</td></tr>`}</tbody></table></div>`;
}

async function aPermbledhje() {
  const d = await api("GET", "/api/admin/permbledhje");
  const n = d.numrat;
  const shiritat = lista => {
    const max = Math.max(1, ...lista.map(x => x.here));
    return lista.length ? lista.map(x => `<div class="bar"><span>${esc(x.emer)}</span><span class="muted">${x.here}</span><i style="--w:${(x.here / max * 100).toFixed(0)}%"></i></div>`).join("")
      : `<p class="muted">${t("noData")}</p>`;
  };
  $("#a-trupi").innerHTML = `
    <div class="stats">${[["accounts", n.llogari], ["persons", n.persona], ["questions", n.pyetje], ["drugs", n.barna], ["symptoms", n.simptoma]]
      .map(([k, v]) => `<div class="stat"><small>${t(k)}</small><b>${v}</b></div>`).join("")}</div>
    <div class="grid2"><div class="panel"><h3>${t("topSymptoms")}</h3>${shiritat(d.simptomat)}</div>
      <div class="panel"><h3>${t("topDrugs")}</h3>${shiritat(d.barnat)}</div></div>
    <h3 style="font-size:.95rem;margin:0 0 .7rem">${t("recentQ")}</h3>
    ${tabele(["", t("name"), t("question")], d.pyetjet.map(p => `<tr><td class="muted" style="white-space:nowrap">${esc(p.ora.replace("T", " "))}</td><td>${esc(p.personi)}</td><td>${esc(p.tekst)}</td></tr>`))}
    <p class="hint" style="margin-top:1rem">${t("connection")}: Neo4j · ${esc(d.lidhja)}</p>`;
}

async function aPerdoruesit() {
  const d = await api("GET", "/api/admin/perdoruesit");
  $("#a-trupi").innerHTML = `<div class="toolbar"><button class="btn primary sm" id="u-re">${ic("plus", 16)}${t("newAccount")}</button></div>
    ${tabele([t("username"), t("email"), t("role"), t("age"), t("messages"), t("created"), t("lastLogin"), ""], d.llogarite.map(u => `<tr>
      <td><strong>${esc(u.perdoruesi)}</strong>${u.perdoruesi === d.une ? ' <span class="muted">(ti)</span>' : ""}</td>
      <td class="muted">${esc(u.email || "–")}</td>
      <td><span class="badge${u.roli === "admin" ? " admin" : ""}">${u.roli === "admin" ? t("administrator") : t("user")}</span></td>
      <td>${u.mosha ?? "–"}</td><td>${u.mesazhe}</td>
      <td class="muted">${esc(u.krijuar)}</td><td class="muted">${esc(u.hyrja_fundit || "–")}</td>
      <td style="white-space:nowrap">${u.perdoruesi !== d.une ? `<button class="icon-btn sm danger" data-fshi="${esc(u.perdoruesi)}" title="${t("deleteUser")}" aria-label="${t("deleteUser")}">${ic("trash", 16)}</button>` : ""}<button class="icon-btn sm" data-u="${esc(u.perdoruesi)}" aria-label="${t("actions")}">${ic("more", 16)}</button></td></tr>`))}`;
  $("#u-re").addEventListener("click", () => {
    modal({ titull: t("newAccount"), trup: `<div class="field"><label>${t("username")}</label><input class="input" id="n-u"></div>
        <div class="field"><label>${t("email")}</label><input class="input" id="n-e" type="email"></div>
        <div class="field"><label>${t("newPw")}</label><input class="input" id="n-p" type="password" autocomplete="new-password"></div>
        <div class="field"><label>${t("role")}</label><select class="input" id="n-r"><option value="perdorues">${t("user")}</option><option value="admin">${t("administrator")}</option></select></div>
        <div class="error-text" id="n-err"></div>`,
      fund: `<button class="btn" data-mbyll>${t("cancel")}</button><button class="btn primary" id="n-ok">${t("create")}</button>`,
      pasHapjes: (o, mbyll) => o.querySelector("#n-ok").addEventListener("click", async () => {
        try { await api("POST", "/api/admin/perdoruesit", { perdoruesi: o.querySelector("#n-u").value, email: o.querySelector("#n-e").value,
            fjalekalimi: o.querySelector("#n-p").value, roli: o.querySelector("#n-r").value }); mbyll(); aPerdoruesit(); }
        catch (x) { o.querySelector("#n-err").textContent = x.message; }
      }) });
  });
  document.querySelectorAll("[data-u]").forEach(b => b.addEventListener("click", e => {
    e.stopPropagation();
    const u = d.llogarite.find(x => x.perdoruesi === b.dataset.u);
    const art = [{ tekst: t("viewChats"), ikona: "file", veprim: () => shikoBisedat(u.perdoruesi) },
      { tekst: u.roli === "admin" ? t("makeUser") : t("makeAdmin"), ikona: "shield", veprim: async () => {
        try { await api("PATCH", `/api/admin/perdoruesit/${encodeURIComponent(u.perdoruesi)}`, { roli: u.roli === "admin" ? "perdorues" : "admin" }); aPerdoruesit(); }
        catch (x) { toast(x.message, true); } } },
      { tekst: t("setPw"), ikona: "key", veprim: () => modal({ titull: `${t("setPw")}: ${u.perdoruesi}`,
          trup: `<div class="field"><label>${t("newPw")}</label><input class="input" id="r-p" type="password" autocomplete="new-password"></div><div class="error-text" id="r-err"></div>`,
          fund: `<button class="btn" data-mbyll>${t("cancel")}</button><button class="btn primary" id="r-ok">${t("save")}</button>`,
          pasHapjes: (o, mbyll) => o.querySelector("#r-ok").addEventListener("click", async () => {
            try { await api("PATCH", `/api/admin/perdoruesit/${encodeURIComponent(u.perdoruesi)}`, { fjalekalimi: o.querySelector("#r-p").value }); mbyll(); toast(t("pwChanged")); }
            catch (x) { o.querySelector("#r-err").textContent = x.message; }
          }) }) }];
    if (u.perdoruesi !== d.une) art.push("-", { tekst: t("deleteUser"), ikona: "trash", rrezik: true, veprim: () => fshiPerdoruesin(u) });
    hapMenune(b, art);
  }));
  document.querySelectorAll("[data-fshi]").forEach(b => b.addEventListener("click", e => {
    e.stopPropagation();
    fshiPerdoruesin(d.llogarite.find(x => x.perdoruesi === b.dataset.fshi));
  }));
}

async function fshiPerdoruesin(u) {
  if (!await konfirmo(t("deleteUserQ")(u.perdoruesi), { butoni: t("deleteUser"), pershkrimi: t("deleteUserHelp")(u.mesazhe) })) return;
  try {
    await api("DELETE", `/api/admin/perdoruesit/${encodeURIComponent(u.perdoruesi)}`);
    toast(t("userDeleted")(u.perdoruesi));
    aPerdoruesit();
  } catch (x) { toast(x.message, true); }
}

async function shikoBisedat(u) {
  const d = await api("GET", `/api/admin/perdoruesit/${encodeURIComponent(u)}/bisedat`);
  const trup = d.bisedat.length ? d.bisedat.map(b => `<details class="card" style="margin-bottom:.6rem"><summary>${ic("chev", 14)}${esc(b.titull)} <span class="muted" style="font-weight:400">· ${esc((b.perditesuar || "").slice(0, 16).replace("T", " "))}</span>${b.fshire ? ` <span class="badge deleted">${t("deletedByUser")}${b.fshire_me ? ` · ${esc(b.fshire_me.slice(0, 16).replace("T", " "))}` : ""}</span>` : ""}</summary>
      <div class="chat-log">${b.mesazhet.map(m => m.role === "user" ? `<div class="msg user"><div class="bubble">${esc(m.content)}</div></div>` : `<div class="msg bot"><div class="md">${md(m.content)}</div></div>`).join("")}</div></details>`).join("")
    : `<p class="muted">${t("noChatsUser")}</p>`;
  modal({ titull: `${t("viewChats")}: ${u}`, trup, gjere: true });
}

async function aBarnat() {
  const d = await api("GET", "/api/admin/barnat");
  const vizato_ = q => {
    const lista = d.barnat.filter(b => !q || `${b.emer} ${b.id} ${b.simptomat.join(" ")}`.toLowerCase().includes(q));
    $("#b-tab").innerHTML = tabele([t("name"), t("dose"), t("max"), t("forSymptoms"), ""], lista.map(b => `<tr>
      <td><strong>${esc(b.emer)}</strong><div class="muted" style="font-size:.78rem">${esc(b.id)}</div></td>
      <td>${esc(b.doza)}</td><td>${esc(b.doza_maks)}</td><td class="muted">${esc(b.simptomat.join(", "))}</td>
      <td><button class="btn sm" data-b="${esc(b.id)}">${t("edit")}</button></td></tr>`));
    document.querySelectorAll("[data-b]").forEach(x => x.addEventListener("click", () => ndryshoBarnen(d.barnat.find(b => b.id === x.dataset.b))));
  };
  $("#a-trupi").innerHTML = `<p class="hint" style="margin:0 0 1rem">${t("pharmacistNote")}</p>
    <div class="toolbar"><input class="input" id="b-q" placeholder="${t("searchDrugs")}"><button class="btn primary sm" id="b-re">${ic("plus", 16)}${t("newDrug")}</button></div><div id="b-tab"></div>`;
  vizato_("");
  $("#b-q").addEventListener("input", e => vizato_(e.target.value.toLowerCase()));
  $("#b-re").addEventListener("click", () => barneERe(d));
}

function ndryshoBarnen(b) {
  const fushat = [["emer", t("name")], ["doza", t("dose")], ["doza_maks", t("max")], ["kohezgjatja", t("duration")], ["si_merret", t("how")]];
  const kuf = b.kufizime.length ? `<ul style="margin:.3rem 0 0;padding-left:1.2rem;font-size:.87rem">${b.kufizime.map(k =>
    `<li><strong>${k.lloji === "KUJDES_ME" ? t("caution") : t("contraindication")}:</strong> ${esc(k.gjendja)}${k.arsye ? ` — <span class="muted">${esc(k.arsye)}</span>` : ""}</li>`).join("")}</ul>` : `<p class="muted">–</p>`;
  modal({ titull: b.emer, gjere: true, trup: fushat.map(([k, e]) => `<div class="field"><label>${esc(e)}</label>
      ${k === "emer" ? `<input class="input" data-f="${k}" value="${esc(b[k])}">` : `<textarea class="input" data-f="${k}" style="min-height:60px">${esc(b[k])}</textarea>`}</div>`).join("")
      + `<div class="field"><label>${t("restrictions")}</label>${kuf}</div><div class="error-text" id="e-err"></div>`,
    fund: `<button class="btn" data-mbyll>${t("cancel")}</button><button class="btn primary" id="e-ok">${t("save")}</button>`,
    pasHapjes: (o, mbyll) => o.querySelector("#e-ok").addEventListener("click", async () => {
      const ndr = {};
      o.querySelectorAll("[data-f]").forEach(x => { if (x.value.trim() !== (b[x.dataset.f] || "")) ndr[x.dataset.f] = x.value.trim(); });
      if (!Object.keys(ndr).length) { mbyll(); return; }
      try { await api("PATCH", `/api/admin/barnat/${encodeURIComponent(b.id)}`, ndr); mbyll(); toast(t("saved")); aBarnat(); }
      catch (x) { o.querySelector("#e-err").textContent = x.message; }
    }) });
}

function barneERe(d) {
  const zgjedhes = (id, lista) => `<input class="input" placeholder="${t("filter")}" data-filter="${id}" style="height:34px;margin-bottom:.4rem">
    <div class="cond-grid" id="${id}" style="max-height:160px">${lista.map(x => `<label class="check" data-emer="${esc(x.emer.toLowerCase())}"><input type="checkbox" value="${esc(x.id)}"><span>${esc(x.emer)}</span></label>`).join("")}</div>`;
  const f = [["id", t("drugId")], ["emer", t("name")], ["lende_aktive", t("activeIng")], ["forma", t("form")], ["tregtare", t("tradeNames")],
    ["doza", t("dose")], ["doza_maks", t("max")], ["kohezgjatja", t("duration")], ["si_merret", t("how")]];
  modal({ titull: t("newDrug"), gjere: true,
    trup: `<p class="hint" style="margin-top:0">${t("pharmacistNote")}</p><div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:0 1rem">
      ${f.map(([k, e]) => `<div class="field"><label>${esc(e)}</label><input class="input" data-f="${k}" ${k === "forma" ? 'value="Tableta"' : ""}></div>`).join("")}</div>
      <div class="field"><label>${t("forSymptoms")}</label>${zgjedhes("z-s", d.simptomat)}</div>
      <div class="field"><label>${t("contraFor")}</label>${zgjedhes("z-k", d.gjendjet)}</div>
      <div class="field"><label>${t("cautionFor")}</label>${zgjedhes("z-c", d.gjendjet)}</div><div class="error-text" id="d-err"></div>`,
    fund: `<button class="btn" data-mbyll>${t("cancel")}</button><button class="btn primary" id="d-ok">${t("create")}</button>`,
    pasHapjes: (o, mbyll) => {
      o.querySelectorAll("[data-filter]").forEach(inp => inp.addEventListener("input", () => {
        const q = inp.value.toLowerCase();
        o.querySelectorAll(`#${inp.dataset.filter} .check`).forEach(c => (c.style.display = c.dataset.emer.includes(q) ? "" : "none"));
      }));
      const zgj = id => [...o.querySelectorAll(`#${id} input:checked`)].map(x => x.value);
      o.querySelector("#d-ok").addEventListener("click", async () => {
        const trupi = Object.fromEntries([...o.querySelectorAll("[data-f]")].map(x => [x.dataset.f, x.value]));
        Object.assign(trupi, { per: zgj("z-s"), kunder: zgj("z-k"), kujdes: zgj("z-c") });
        try { await api("POST", "/api/admin/barnat", trupi); mbyll(); toast(t("saved")); aBarnat(); }
        catch (x) { o.querySelector("#d-err").textContent = x.message; }
      });
    } });
}

let _sondazhi = null;
async function aTrajnimi() {
  clearTimeout(_sondazhi);
  const d = await api("GET", "/api/admin/trajnimi");
  if (S.adminTab !== "trajnimi" || !$("#a-trupi")) return;
  const f = d.i_fundit, puna = d.puna;
  const pct = x => `${Math.round(x * 100)}%`;
  const opsionet = `<option value="">${t("chooseSymptom")}</option>` + d.simptomat.map(s => `<option value="${esc(s.id)}">${esc(s.emer)}</option>`).join("");
  const kategorite = f ? Object.values(f.kategorite).map(k => `<tr><td>${esc(k.emri)}</td><td>${k.sakte}/${k.gjithsej}${k.pyeti ? ` <span class="muted">(+${k.pyeti})</span>` : ""}</td>
      <td style="min-width:140px"><div class="bar" style="margin:0"><span>${pct(k.saktesia)}</span><span class="muted">${pct(k.kufiri)}</span><i style="--w:${pct(k.saktesia)}"></i></div></td>
      <td><span class="badge${k.kaloi ? " admin" : ""}" style="${k.kaloi ? "" : "background:var(--danger-soft);color:var(--danger)"}">${k.kaloi ? t("passed") : t("failed")}</span></td></tr>`) : [];
  const gabimet = (f?.gabimet || []).slice(0, 30).map(g => `<tr><td class="muted">${esc(g.kategoria)}</td><td>${esc(g.mesazh)}</td>
      <td>${esc(Array.isArray(g.pritet) ? g.pritet.join(", ") : g.pritet)}</td><td>${esc(Array.isArray(g.gjetur) ? g.gjetur.join(", ") || "–" : g.gjetur)}</td></tr>`);
  $("#a-trupi").innerHTML = `
    <div class="stats">
      <div class="stat"><small>${t("overall")}</small><b>${f ? pct(f.saktesia) : "–"}</b><span class="hint">${f ? esc(f.data) + " · " + (f.kaloi ? t("passed") : t("failed")) : ""}</span></div>
      <div class="stat"><small>${t("urgency") || "Urgjencat"}</small><b>${f?.kategorite?.urgjence ? pct(f.kategorite.urgjence.saktesia) : "–"}</b></div>
      <div class="stat"><small>${t("likes")}</small><b>${d.numrat.pelqime}</b></div>
      <div class="stat"><small>${t("complaints")}</small><b>${d.numrat.te_hapura}</b></div>
    </div>
    <div class="panel" style="margin-bottom:1.4rem"><div style="display:flex;gap:1rem;align-items:center;flex-wrap:wrap;justify-content:space-between">
      <div><h3 style="margin:0 0 .2rem">${t("lastEval")}</h3><p class="hint" style="margin:0">${t("evalHelp")}</p></div>
      <button class="btn primary" id="t-nis" ${puna.aktive ? "disabled" : ""}>${ic("play", 15)}${puna.aktive ? t("evalRunning") : t("evalRun")}</button></div>
      ${puna.aktive ? `<div class="bar" style="margin-top:1rem"><span>${t("progress")}: ${puna.i}/${puna.n || "…"} · ${esc(puna.kategoria)}</span><span></span>
        <i style="--w:${puna.n ? Math.round(puna.i / puna.n * 100) : 2}%"></i></div>` : ""}
      ${puna.gabim ? `<div class="error-text">${esc(puna.gabim)}</div>` : ""}
      ${f ? `<div style="margin-top:1rem">${tabele([t("category"), t("correct"), `${t("accuracy") || "Saktësia"} / ${t("threshold")}`, ""], kategorite)}</div>` : `<p class="muted">${t("noEval")}</p>`}
      ${d.historiku.length > 1 ? `<h3 style="margin:1.2rem 0 .6rem">${t("historyEval")}</h3>${d.historiku.map(h =>
        `<div class="bar"><span>${esc(h.data)}</span><span class="muted">${pct(h.saktesia)} · ${h.gjithsej}</span><i style="--w:${pct(h.saktesia)}"></i></div>`).join("")}` : ""}
    </div>
    <div class="panel" style="margin-bottom:1.4rem"><h3>${t("feedback")}</h3>
      ${d.reagimet.length ? d.reagimet.map(r => `<div class="card" data-r="${esc(r.id)}" style="margin-bottom:.7rem">
          <div class="hint">${esc(r.ora.replace("T", " "))} · ${esc(r.perdoruesi || t("guest"))} · ${esc(t("r_" + r.arsye) || r.arsye || "")}</div>
          <div style="margin:.4rem 0"><strong>${t("question")}:</strong> ${esc(r.pyetja)}</div>
          ${r.koment ? `<div class="note warn" style="margin:.3rem 0">${esc(r.koment)}</div>` : ""}
          <details class="more-info"><summary>${ic("chev", 14)}${t("answer")}</summary><div class="md" style="font-size:.88rem;margin-top:.4rem">${md(r.pergjigjja)}</div></details>
          <div class="toolbar" style="margin:.8rem 0 0"><select class="input" style="max-width:300px;height:36px">${opsionet}</select>
            <button class="btn primary sm" data-meso>${t("teach")}</button><button class="btn sm" data-zgjidh>${t("resolve")}</button></div></div>`).join("")
        : `<p class="muted">${t("noFeedback")}</p>`}
    </div>
    <div class="grid2">
      <div class="panel"><h3>${t("manualTeach")}</h3>
        <div class="field"><label for="m-f">${t("phrase")}</label><input class="input" id="m-f" placeholder="${t("phrasePh")}" maxlength="200"></div>
        <div class="field"><label for="m-s">${t("symptom")}</label><select class="input" id="m-s">${opsionet}</select></div>
        <div class="error-text" id="m-err"></div><button class="btn primary" id="m-ok">${t("teach")}</button></div>
      <div class="panel"><h3>${t("recentLessons")}</h3>${d.mesimet.length ? `<ul style="margin:0;padding-left:1.1rem;font-size:.87rem">${d.mesimet.map(x =>
        `<li><strong>${esc(x.fraza)}</strong> → ${esc(x.simptoma)} <span class="muted">· ${esc(x.ora)} · ${esc(x.kush)}</span></li>`).join("")}</ul>` : `<p class="muted">–</p>`}</div>
    </div>
    ${gabimet.length ? `<h3 style="font-size:.95rem;margin:1.4rem 0 .3rem">${t("evalErrors")}</h3><p class="hint" style="margin:0 0 .7rem">${t("evalErrorsHint")}</p>
      ${tabele(["", t("question"), t("expected"), t("got")], gabimet)}` : ""}`;

  $("#t-nis").addEventListener("click", async () => {
    try { await api("POST", "/api/admin/trajnimi/vlereso"); aTrajnimi(); } catch (x) { toast(x.message, true); }
  });
  const meso = async (fraza, simptoma, reagim_id, gabimEl) => {
    if (!simptoma) { gabimEl ? (gabimEl.textContent = t("chooseSymptom")) : toast(t("chooseSymptom"), true); return; }
    try { const r = await api("POST", "/api/admin/trajnimi/meso", { fraza, simptoma, reagim_id }); toast(t("taught")(r.fraza)); aTrajnimi(); }
    catch (x) { gabimEl ? (gabimEl.textContent = x.message) : toast(x.message, true); }
  };
  document.querySelectorAll("[data-r]").forEach(c => {
    const r = d.reagimet.find(x => x.id === c.dataset.r);
    c.querySelector("[data-meso]").addEventListener("click", () => meso(r.pyetja, c.querySelector("select").value, r.id));
    c.querySelector("[data-zgjidh]").addEventListener("click", async () => {
      try { await api("POST", `/api/admin/trajnimi/reagim/${r.id}/zgjidh`, {}); aTrajnimi(); } catch (x) { toast(x.message, true); }
    });
  });
  $("#m-ok").addEventListener("click", () => meso($("#m-f").value, $("#m-s").value, null, $("#m-err")));
  if (puna.aktive) _sondazhi = setTimeout(() => { if (S.adminTab === "trajnimi" && S.pamja === "admin") aTrajnimi(); }, 1500);
}

async function aBackup() {
  const d = await api("GET", "/api/admin/backup");
  $("#a-trupi").innerHTML = `<div class="panel" style="max-width:640px"><h3>${t("backup")}</h3><p class="hint" style="margin-top:0">${t("backupHelp")}<br><code>${esc(d.dosja)}</code></p>
    <button class="btn primary" id="bk">${ic("database", 16)}${t("backupNow")}</button>
    ${d.te_fundit.length ? `<h3 style="margin-top:1.4rem">${t("recentBackups")}</h3><ul style="margin:0;padding-left:1.2rem;font-size:.88rem">${d.te_fundit.map(x => `<li>${esc(x)}</li>`).join("")}</ul>` : ""}
    <p class="hint" style="margin-top:1.2rem">${t("connection")}: Neo4j · ${esc(d.lidhja)} · Neo4j Browser: <a href="http://localhost:7474" target="_blank" rel="noopener">localhost:7474</a></p></div>`;
  $("#bk").addEventListener("click", async e => {
    const b = e.currentTarget; b.disabled = true;
    try { const r = await api("POST", "/api/admin/backup"); toast(t("backupDone")(r.dosja)); aBackup(); }
    catch (x) { toast(x.message, true); b.disabled = false; }
  });
}

/* ================================================================ nisja */
async function nisAplikacionin() {
  try { S.bisedat = (await api("GET", "/api/bisedat")).bisedat; } catch (e) { S.bisedat = []; }
  S.aktive = null;
  const h = location.hash;
  if (h.startsWith("#/admin") && S.sesioni.llogaria?.roli === "admin") {
    S.pamja = "admin"; S.adminTab = h.split("/")[2] || "permbledhje";
  } else S.pamja = "biseda";
  vizato();
  const m = h.match(/^#\/c\/([\w-]+)$/);
  if (m && S.pamja === "biseda") hapBiseden(m[1]);
}

document.addEventListener("keydown", e => {
  if (!S.sesioni?.llogaria && !S.sesioni?.vizitor) return;
  const k = e.key.toLowerCase();
  if ((e.ctrlKey || e.metaKey) && e.shiftKey && k === "o") { e.preventDefault(); bisedeERe(); }
  else if ((e.ctrlKey || e.metaKey) && (k === "b" || (e.shiftKey && k === "s"))) { e.preventDefault(); nderroPanelin(); }
});

(async () => {
  document.documentElement.lang = S.gjuha;
  aplikoTemen();
  const rv = location.hash.match(/^#\/rivendos\/([\w-]+)$/);
  if (rv) { S.sesioni = { llogaria: null, vizitor: false }; vizatoHyrjen("rivendos", { token: rv[1] }); return; }
  try { S.sesioni = await api("GET", "/api/sesioni"); }
  catch (x) { $("#root").innerHTML = `<div class="auth-center" style="min-height:100vh"><div class="alert danger">${ic("alert", 20)}<div>${esc(x.message)}<br>${esc(t("serviceErr"))}</div></div></div>`; return; }
  if (S.sesioni.llogaria || S.sesioni.vizitor) await nisAplikacionin(); else vizato();
})();
