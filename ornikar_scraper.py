from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from dotenv import load_dotenv
import time
import json
import os
import requests
import tempfile

def send_telegram_message(message):
    TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
    TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
    print("[🔁] Tentative d'envoi Telegram...")
    if TELEGRAM_TOKEN and TELEGRAM_CHAT_ID:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        data = {
            "chat_id": TELEGRAM_CHAT_ID,
            "text": message
        }
        try:
            response = requests.post(url, data=data)
            print("[✅] Message envoyé. Réponse :", response.status_code, response.text)
            if response.status_code != 200:
                print("[⚠️] Erreur Telegram :", response.text)
        except Exception as e:
            print("[⚠️] Exception Telegram :", e)
    else:
        print("[⚠️] Paramètres TELEGRAM manquants dans .env")


# --- Chargement des identifiants ---
load_dotenv()
EMAIL = os.getenv("ORNIKAR_EMAIL")
PASSWORD = os.getenv("ORNIKAR_PASSWORD")
print(f"Connexion avec {EMAIL}")

# --- Configuration ---
CALENDAR_URL = "https://app.ornikar.com/conduite/enseignant/14365#/conduite/reservation/14365/lecons?meetingPointId=4716"
SLOTS_FILE = "slots_seen.json"

# --- Lancement navigateur ---
options = Options()
options.add_argument("--start-maximized")
options.add_argument(f"--user-data-dir={tempfile.mkdtemp()}")
options.add_argument("--headless")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")

driver = webdriver.Chrome(options=options)

wait = WebDriverWait(driver, 20)

# --- Fonction pour accepter les cookies et bloquer le popup si présent ---
def gerer_cookies_et_popups():
    try:
        # Attendre et switcher vers l'iframe des cookies si nécessaire
        try:
            iframe = driver.find_element(By.CSS_SELECTOR, "iframe[src*='axeptio']")
            driver.switch_to.frame(iframe)
        except:
            pass  # pas d'iframe => passe au test direct

        # Tenter de cliquer sur le bouton "Accepter" dans la popin Axeptio
        accept_btn = WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.XPATH, "//button[contains(., 'Accepter')]"))
        )
        accept_btn.click()
        time.sleep(1)

        # Revenir à la fenêtre principale si on était dans un iframe
        driver.switch_to.default_content()
    except:
        driver.switch_to.default_content()
        pass

# --- Accès page d'accueil puis page de connexion ---
driver.get("https://app.ornikar.com")
with open("page.html", "w", encoding="utf-8") as f:
    f.write(driver.page_source)

time.sleep(2)
gerer_cookies_et_popups()

driver.get("https://app.ornikar.com/connexion")
with open("page.html", "w", encoding="utf-8") as f:
    f.write(driver.page_source)

time.sleep(2)
gerer_cookies_et_popups()

# --- Remplir formulaire de connexion ---
try:
    email_input = wait.until(EC.presence_of_element_located((By.ID, "email")))
    email_input.send_keys(EMAIL)
    password_input = driver.find_element(By.ID, "password")
    password_input.send_keys(PASSWORD)
    time.sleep(1)

    # Appuyer sur Entrée dans le champ mot de passe (plus fiable que click JS)
    password_input.send_keys(Keys.RETURN)
    time.sleep(5)
except Exception as e:
    print("[❌] Erreur pendant la connexion :", e)
    driver.quit()
    exit()

# --- Accès au calendrier ---
print("[➡️] Accès à la page de réservation...")
driver.get(CALENDAR_URL)
time.sleep(10)

# --- Extraction des créneaux ---
print("[🔎] Recherche des créneaux...")
elements = driver.find_elements(By.CSS_SELECTOR, "div[class*=SlotCard]")
#Verification lecture SLotCard
print(f"[🧪] {len(elements)} éléments SlotCard détectés")
for el in elements:
    try:
        date = el.find_element(By.CSS_SELECTOR, "span[class*=SlotCard__Date]").text
        hour = el.find_element(By.CSS_SELECTOR, "span[class*=SlotCard__Time]").text
        print(f"  - Slot détecté : {date} à {hour}")
    except Exception as e:
        print(f"[⚠️] SlotCard illisible : {e}")


slots = []
for el in elements:
    try:
        date = el.find_element(By.CSS_SELECTOR, "span[class*=SlotCard__Date]").text
        hour = el.find_element(By.CSS_SELECTOR, "span[class*=SlotCard__Time]").text
        slots.append(f"{date} - {hour}")
    except:
        continue

# --- Comparaison avec les anciens créneaux ---
if os.path.exists(SLOTS_FILE):
    with open(SLOTS_FILE, "r") as f:
        old_slots = set(json.load(f))
else:
    old_slots = set()

new_slots = set(slots) - old_slots

# --- Affichage des nouveaux créneaux ---


# --- Vérification et envoi si prochaine dispo a changé ---
PROCHAINE_DISPO_LOG = "prochaine_dispo.log"
from twilio.rest import Client

# Charger la dernière date enregistrée
ancienne_dispo = ""
if os.path.exists(PROCHAINE_DISPO_LOG):
    with open(PROCHAINE_DISPO_LOG, "r") as f:
        ancienne_dispo = f.read().strip()

# --- Vérification et envoi si prochaine dispo a changé ---
PROCHAINE_DISPO_LOG = "prochaine_dispo.log"
from twilio.rest import Client



# --- Lecture ancienne date enregistrée ---
PROCHAINE_DISPO_LOG = "prochaine_dispo.log"
ancienne_dispo = ""
if os.path.exists(PROCHAINE_DISPO_LOG):
    with open(PROCHAINE_DISPO_LOG, "r") as f:
        ancienne_dispo = f.read().strip()

# --- Récupération de la nouvelle date ---
nouvelle_dispo = None  # <--- AJOUT PRÉVENTIF
try:
    element = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((
            By.CSS_SELECTOR,
            "body > div.css-175oi2r.r-16y2uox.r-1pi2tsx.r-1d2f490.r-1xcajam.r-ipm5af.r-13qz1uu > div > div.css-175oi2r.r-1awozwy.r-1qahzrx.r-1jj8364.r-lchren.r-1t01tom.r-bko0gm.r-142ercc.r-1jnzvcq.r-puj83k.r-11g3r6m.r-1hy97zq.r-13qz1uu > div > div.css-175oi2r.r-150rngu.r-eqz5dr.r-16y2uox.r-1wbh5a2.r-11yh6sk.r-1rnoaur.r-agouwx > div > div.css-175oi2r.r-1awozwy > div > div:nth-child(3) > div.css-146c3p1.r-cqee49.r-1i390ty.r-ubezar.r-13uqrnb.r-b88u0q.r-oxtfae.r-10yl4k.r-q4m81j > span"
        ))
    )
    nouvelle_dispo = element.text.strip()
    print(f"[📅] Prochaine disponibilité indiquée : {nouvelle_dispo}")

except Exception as e:
    print(f"[❌] Impossible de lire la date : {e}")

# --- Comparaison avec l'ancienne valeur ---
if nouvelle_dispo and nouvelle_dispo != ancienne_dispo:
    print("[📬] Nouvelle date détectée, envoi d'une alerte.")

    with open(PROCHAINE_DISPO_LOG, "w") as f:
        f.write(nouvelle_dispo)

    # 🔔 Envoi Telegram
    send_telegram_message(f"Nouvelle disponibilité Ornikar : {nouvelle_dispo}")
else:
    print("[✅] Pas de changement de date, aucune alerte envoyée.")



# --- Fermeture ---
driver.quit()
