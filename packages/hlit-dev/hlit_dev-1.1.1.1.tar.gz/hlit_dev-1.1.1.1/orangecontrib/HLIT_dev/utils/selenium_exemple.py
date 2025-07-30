import os
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# === CONFIG ===
CHROMEDRIVER_PATH = "C:/Users/max83/Documents/chromedriver-win64/chromedriver-win64/chromedriver.exe"
USER_DATA_DIR = os.path.expanduser("~\\AppData\\Local\\Google\\Chrome\\User Data")
PROFILE_NAME = "Profile 5"  # ← Ton vrai profil (vu dans chrome://version)
DOWNLOAD_FOLDER = "polycam_downloads"
URL = "https://poly.cam/library?feed=albums&layout=list&tags=all&sort=created"

# === Chrome options ===
options = Options()
options.add_argument(f"user-data-dir={USER_DATA_DIR}")
options.add_argument(f"profile-directory={PROFILE_NAME}")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")
options.add_argument("--disable-gpu")
options.add_argument("--headless=new")  # Optionnel si tu veux le faire sans interface

# === Lancer Chrome avec le bon profil ===
service = Service(CHROMEDRIVER_PATH)
driver = webdriver.Chrome(service=service, options=options)

# === Aller sur la page Polycam ===
driver.get(URL)
time.sleep(5)  # Laisse le temps de charger
name_buttons = driver.find_elements(By.XPATH, '//button[@title="Edit name"]')
# --- Étape 1 : Récupérer les noms (spans) ---
name_elements = driver.find_elements(By.XPATH, '//button[@title="Edit name"]/span')
names = [e.text.strip() for e in name_elements if e.text.strip()]
print("📌 Noms récupérés :")
for n in names:
    print(" -", n)

# --- Étape 2 : Récupérer les liens des albums ---
album_links_elements = driver.find_elements(By.CSS_SELECTOR, 'a[href^="/album/"]')
album_links = [e.get_attribute("href") for e in album_links_elements]

# --- Vérification : nombre de noms = nombre de liens ---
if len(names) != len(album_links):
    print(f"⚠️ Attention : {len(names)} noms et {len(album_links)} liens. Possible décalage.")

# --- Étape 3 : Associer noms + liens ---
album_data = list(zip(names, album_links))

# --- Étape 4 : Navigation + retour ---
for i, (name, url) in enumerate(album_data):
    print(f"\n➡️ {i + 1}/{len(album_data)} : {name}")

    # Ouvrir l'album
    driver.get(url)
    time.sleep(4)

    print(f"📂 Album : {name}")

    try:
        # === Étape 1 : Trouver tous les boutons "Details"
        details_buttons = driver.find_elements(By.XPATH, '//button[@title="Details"]')

        for index, btn in enumerate(details_buttons):
            try:
                btn.click()
                time.sleep(2)

                # === Étape 2 : Lire la "Capture method"
                info_sections = driver.find_elements(By.CLASS_NAME, 'Info_section__8mgHM')
                capture_method = None

                for section in info_sections:
                    spans = section.find_elements(By.TAG_NAME, 'span')
                    if len(spans) == 2 and "Capture method:" in spans[0].text:
                        capture_method = spans[1].text.strip()
                        break

                print(f"🔍 Méthode de capture détectée : {capture_method}")

                # === Étape 3 : Vérifie la méthode
                if capture_method in ["Object mode", "Floorplan mode"]:
                    print(f"✅ Méthode acceptée : {capture_method} → tentative de téléchargement")

                    try:
                        # Cliquer sur le bouton "Download 3D model"
                        download_button = driver.find_element(By.XPATH, '//button[.//span[text()="Download 3D model"]]')
                        download_button.click()
                        print("⬇️  Bouton 'Download 3D model' cliqué !")
                        time.sleep(6)

                        # === Étape 4 : Clic conditionnel selon la méthode
                        if capture_method == "Object mode":
                            try:
                                image_btn = driver.find_element(By.XPATH, '//span[text()="Images"]/ancestor::button')
                                image_btn.click()
                                print("🖼️ Bouton 'Images' cliqué")
                                time.sleep(2)
                            except Exception as e_img:
                                print(f"❌ Bouton 'Images' introuvable : {e_img}")

                        elif capture_method == "Floorplan mode":
                            try:
                                report_btn = driver.find_element(By.XPATH,
                                                                 '//span[text()="Spatial Report"]/ancestor::button')
                                report_btn.click()
                                print("📐 Bouton 'Spatial Report' cliqué")
                                time.sleep(2)
                            except Exception as e_rp:
                                print(f"❌ Bouton 'Spatial Report' introuvable : {e_rp}")

                        # === Étape 5 : Cliquer sur Export
                        try:
                            export_btn = driver.find_element(By.XPATH, '//span[text()="Export"]/ancestor::button')
                            export_btn.click()
                            print("📤 Bouton 'Export' cliqué")
                            time.sleep(2)
                            # 🔁 Attendre que le bouton "Back" soit cliquable
                            try:
                                # Attendre que le bouton Back soit présent
                                wait = WebDriverWait(driver, 10)
                                back_btn = wait.until(
                                    EC.presence_of_element_located((By.XPATH, '//button[@title="Back"]')))

                                # Scroll jusqu'à lui pour le rendre visible
                                driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", back_btn)
                                time.sleep(0.5)

                                # Clic JS (plus puissant que Selenium click classique)
                                driver.execute_script("arguments[0].click();", back_btn)
                                print("🔙 Bouton 'Back' cliqué via JS")
                                time.sleep(1)

                            except Exception as e:
                                # Optionnel : capture la page pour debug
                                driver.save_screenshot("debug_back_fail.png")
                                print(f"❌ Impossible de cliquer sur 'Back' : {e}")


                        except Exception as e_export:
                            print(f"❌ Bouton 'Export' introuvable ou cliquable : {e_export}")

                    except Exception as e_dl:
                        print(f"❌ Erreur pendant le clic sur 'Download 3D model' : {e_dl}")

                else:
                    print("⏭️ Méthode ignorée. Aucun téléchargement effectué.")

                # Fermer le panneau Details (dans tous les cas sauf si on quitte l'album)
                try:
                    close_btn = driver.find_element(By.XPATH, '//button[@title="Close"]')
                    close_btn.click()
                    time.sleep(1)
                    print("↩️ Panneau de détails fermé.")
                except Exception as e_close:
                    print(f"⚠️ Impossible de fermer le panneau : {e_close}")

            except Exception as e:
                print(f"⛔ Erreur sur Details #{index + 1} : {e}")

    except Exception as e:
        print(f"⚠️ Erreur globale dans l'album {name} : {e}")

    # Retour à la bibliothèque
    driver.get(URL)
    time.sleep(4)
driver.quit()
print("\n✅ Terminé.")