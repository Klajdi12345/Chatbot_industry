"""Tekstet e ndërfaqes në shqip dhe anglisht.   t("celesi") → teksti në gjuhën e zgjedhur."""
import time

import streamlit as st

TEKSTE = {
    # ---- shiriti sipër
    "paneli": ("Hap / mbyll panelin anësor", "Open / close the side panel"),
    "gjuha": ("Gjuha", "Language"),
    "tema": ("Tema", "Theme"),
    "e_bardhe": ("☀️ E bardhë", "☀️ Light"),
    "e_zeze": ("🌙 E zezë", "🌙 Dark"),

    # ---- hyrja
    "hero_nen": ("Asistenti yt i farmacisë.", "Your pharmacy assistant."),
    "veti1_t": ("Nga simptoma te ilaçi", "From symptom to medicine"),
    "veti1_d": ("Shkruaj si ndihesh, p.sh. “më dhemb dhëmbi”.", "Describe how you feel, e.g. “I have a toothache”."),
    "veti2_t": ("I sigurt për profilin tënd", "Safe for your profile"),
    "veti2_d": ("Heq ilaçet që nuk të përshtaten: shtatzëni, ulçerë, ilaçe që merr.",
                "Removes medicines that don't suit you: pregnancy, ulcer, medicines you take."),
    "veti3_t": ("Di kur duhet mjeku", "Knows when you need a doctor"),
    "veti3_d": ("Shenjat e rrezikut të çojnë te 127 / 112, jo te ilaçet.",
                "Danger signs send you to emergency services, not to medicines."),
    "paralajmerim": ("Informacion i përgjithshëm për ilaçe pa recetë. Nuk zëvendëson mjekun ose farmacistin.",
                     "General information about over-the-counter medicines. Not a substitute for a doctor or pharmacist."),
    "mire_se_erdhe": ("Mirë se erdhe 👋", "Welcome 👋"),
    "hyr_shpjegim": ("Hyr në llogari që profili dhe bisedat të ruhen, ose vazhdo si vizitor.",
                     "Sign in to save your profile and chats, or continue as a guest."),
    "hyr": ("🔐 Hyr", "🔐 Sign in"),
    "regjistrohu": ("📝 Regjistrohu", "📝 Sign up"),
    "perdoruesi": ("Emri i përdoruesit", "Username"),
    "fjalekalimi": ("Fjalëkalimi", "Password"),
    "hyr_btn": ("Hyr", "Sign in"),
    "gabim_hyrje": ("Emri ose fjalëkalimi nuk është i saktë.", "Wrong username or password."),
    "perdoruesi_help": ("3–30 karaktere: shkronja shqipe ose angleze (edhe ç, ë), shifra dhe _ . -",
                        "3–30 characters: Albanian or English letters (also ç, ë), digits and _ . -"),
    "emri_yt": ("Emri yt ose një pseudonim", "Your name or a nickname"),
    "emri_help": ("Opsional. Shkronja shqipe ose angleze, hapësira, ' . -",
                  "Optional. Albanian or English letters, spaces, ' . -"),
    "mosha": ("Mosha", "Age"),
    "fjalekalimi_min": ("Fjalëkalimi (min. 8 karaktere)", "Password (min. 8 characters)"),
    "perserit": ("Përsërit fjalëkalimin", "Repeat the password"),
    "pelqim": ("Pranoj që profili dhe bisedat e mia të ruhen në databazë. Mund t'i fshij kur të dua te 👤 Llogaria ime.",
               "I agree that my profile and chats are stored in the database. I can delete them any time in 👤 My account."),
    "shkronjat": ("Mund të përdorësh shkronjat shqipe **ç, ë** dhe ato angleze. "
                  "Emri i përdoruesit nuk dallon shkronjat e mëdha nga të voglat.",
                  "You can use Albanian letters **ç, ë** and English ones. Usernames are not case-sensitive."),
    "krijo": ("Krijo llogarinë", "Create account"),
    "nuk_perputhen": ("Fjalëkalimet nuk përputhen.", "The passwords do not match."),
    "duhet_pelqimi": ("Duhet pëlqimi për të ruajtur të dhënat.", "Consent is required to store your data."),
    "vizitor_btn": ("👤 Vazhdo si vizitor (asgjë nuk ruhet)", "👤 Continue as guest (nothing is saved)"),
    "gabim_neo4j": ("Nuk lidhem dot me Neo4j", "Cannot connect to Neo4j"),

    # ---- navigimi dhe paneli
    "biseda": ("Biseda", "Chat"),
    "llogaria_ime": ("Llogaria ime", "My account"),
    "administrimi": ("Administrimi", "Administration"),
    "permbledhje": ("Përmbledhje", "Overview"),
    "perdoruesit": ("Përdoruesit", "Users"),
    "ilacet": ("Ilaçet", "Medicines"),
    "backup": ("Backup", "Backup"),
    "vizitor": ("Vizitor", "Guest"),
    "admin": ("🛡️ Admin", "🛡️ Admin"),
    "perdorues": ("👤 Përdorues", "👤 User"),
    "pa_llogari": ("pa llogari", "no account"),
    "dil": ("🚪 Dil", "🚪 Sign out"),
    "hyr_regj": ("🔐 Hyr / Regjistrohu", "🔐 Sign in / Sign up"),

    # ---- biseda
    "biseda_re": ("＋ Bisedë e re", "＋ New chat"),
    "biseda_re_help": ("Fillon nga e para.", "Starts from scratch."),
    "profili": ("Profili", "Profile"),
    "pa_llogari_shenim": ("Je pa llogari: asgjë nuk ruhet. Hyr ose regjistrohu për ta ruajtur profilin.",
                          "You are a guest: nothing is saved. Sign in or sign up to save your profile."),
    "mosha_ph": ("p.sh. 30", "e.g. 30"),
    "gjendjet": ("Gjendje dhe ilaçe që merr", "Conditions and medicines you take"),
    "alergji": ("Alergji ose ilaçe të tjera", "Allergies or other medicines"),
    "alergji_ph": ("p.sh. alergji nga penicilina", "e.g. penicillin allergy"),
    "ruaj_profilin": ("💾 Ruaj profilin", "💾 Save profile"),
    "profili_u_ruajt": ("Profili u ruajt.", "Profile saved."),
    "cilesimet": ("Cilësimet", "Settings"),
    "mendo": ("🧠 Mendo më thellë", "🧠 Think more deeply"),
    "mendo_help": ("Bota e rilexon mesazhin me një model që mendon, e kontrollon në bazë dhe të tregon hapat. "
                   "Zgjat nga disa sekonda deri në 1–2 minuta. Urgjencat përgjigjen gjithmonë menjëherë.",
                   "The bot re-reads your message with a reasoning model, checks it against the database and shows "
                   "its steps. Takes a few seconds up to 1–2 minutes. Emergencies are always answered immediately."),
    "shkarko": ("⬇️ Shkarko bisedën", "⬇️ Download chat"),
    "pershendetje": (("Mirëmëngjes", "Mirëdita", "Mirëmbrëma"), ("Good morning", "Good afternoon", "Good evening")),
    "si_ndihesh": ("Si ndihesh sot?", "How are you feeling today?"),
    "shenim_mjeku": ("Informacion i përgjithshëm për ilaçe pa recetë, jo zëvendësim i mjekut ose farmacistit. "
                     "Në urgjencë telefono **127** ose **112**.",
                     "General information about over-the-counter medicines, not a substitute for a doctor or "
                     "pharmacist. In an emergency call **112** (Albania: **127**)."),
    "fusha": ("Si ndihesh? P.sh. “më dhemb koka prej dy ditësh”", "How do you feel? E.g. “I've had a headache for two days”"),
    "shembuj": ((("🦷", "Më dhemb dhëmbi"), ("🤒", "Kam temperaturë dhe grip"),
                 ("🤧", "Teshtij shumë dhe më lotojnë sytë"), ("🔥", "Më djeg stomaku pas ngrënies")),
                (("🦷", "I have a toothache"), ("🤒", "I have a fever and the flu"),
                 ("🤧", "I sneeze a lot and my eyes water"), ("🔥", "My stomach burns after eating"))),
    "po_mendoj": ("🧠 Po mendoj...", "🧠 Thinking..."),
    "po_kerkoj": ("Po kërkoj në bazën e njohurive...", "Searching the knowledge base..."),
    "gabim": ("Ndodhi një gabim", "An error occurred"),
    "gabim_sherbime": ("Kontrollo që Ollama dhe Neo4j janë ndezur.", "Check that Ollama and Neo4j are running."),
    "ti": ("Ti", "You"),

    # ---- llogaria ime
    "hyr_per_faqen": ("Hyr në llogari për ta parë këtë faqe.", "Sign in to see this page."),
    "roli": ("Roli", "Role"),
    "perdorues_thjeshte": ("Përdorues", "User"),
    "mesazhe_ruajtura": ("Mesazhe të ruajtura", "Saved messages"),
    "profili_ruajtur": ("Profili i ruajtur", "Saved profile"),
    "emri": ("Emri", "Name"),
    "gjendje": ("Gjendje", "Conditions"),
    "alergji_shkurt": ("Alergji / ilaçe të tjera", "Allergies / other medicines"),
    "ndrysho_profilin": ("Profilin e ndryshon te paneli anësor i faqes 💬 Biseda, me butonin 💾 Ruaj profilin.",
                         "Edit your profile in the side panel of 💬 Chat, with the 💾 Save profile button."),
    "historia": ("Historia e bisedave", "Chat history"),
    "pa_histori": ("Nuk ke ende biseda të ruajtura.", "You have no saved chats yet."),
    "ndrysho_fj": ("🔑 Ndrysho fjalëkalimin", "🔑 Change password"),
    "fj_aktual": ("Fjalëkalimi aktual", "Current password"),
    "fj_ri": ("Fjalëkalimi i ri (min. 8 karaktere)", "New password (min. 8 characters)"),
    "fj_perserit": ("Përsërit fjalëkalimin e ri", "Repeat the new password"),
    "ndrysho": ("Ndrysho", "Change"),
    "fj_gabim": ("Fjalëkalimi aktual nuk është i saktë.", "The current password is wrong."),
    "fj_nuk_perputhen": ("Fjalëkalimet e reja nuk përputhen.", "The new passwords do not match."),
    "fj_ndryshoi": ("Fjalëkalimi u ndryshua.", "Password changed."),
    "fshi_titull": ("🗑️ Fshi llogarinë dhe të dhënat", "🗑️ Delete account and data"),
    "fshi_shenim": ("Fshihen llogaria, profili dhe të gjitha bisedat e tua. Kjo nuk kthehet pas.",
                    "Your account, profile and all chats are deleted. This cannot be undone."),
    "fshi_konfirmo": ("E kuptoj, dua t'i fshij të gjitha të dhënat e mia", "I understand, delete all my data"),
    "fshi_btn": ("Fshi përgjithmonë", "Delete forever"),
}


def gjuha() -> str:
    return "en" if st.session_state.get("gjuha") == "en" else "sq"


def t(celesi: str):
    sq, en = TEKSTE[celesi]
    return en if gjuha() == "en" else sq


def pershendetja() -> str:
    ora = time.localtime().tm_hour
    return t("pershendetje")[0 if 4 <= ora < 12 else 1 if ora < 18 else 2]
