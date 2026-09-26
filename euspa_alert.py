import sys
import time
import requests
from bs4 import BeautifulSoup

URL_CIBLE = "https://www.euspa-careerday.eu/coming-soon"

# Choisi un identifiant unique pour ton canal d'alerte (ex: euspa-alert-tonprenom)
NTFY_TOPIC = "euspa-careerday-rdv-alert"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

if __name__ == "__main__":
    # --- Ligne temporaire de test (à supprimer après vérification) ---
    notify_user("🧪 Test GitHub Actions", "Le script tourne correctement sur GitHub !", URL_CIBLE)
    # -----------------------------------------------------------------
    
    verify_page()

def notify_user(title: str, message: str, click_url: str):
    """Envoie un push instantané sur smartphone via ntfy.sh."""
    try:
        requests.post(
            f"https://ntfy.sh/{NTFY_TOPIC}",
            data=message.encode("utf-8"),
            headers={
                "Title": title,
                "Priority": "urgent",
                "Tags": "rotating_light,rocket",
                "Click": click_url
            },
            timeout=10
        )
        print(f"[+] Notification envoyée : {title}")
    except Exception as err:
        print(f"[-] Erreur d'envoi ntfy: {err}")

def verify_page():
    try:
        response = requests.get(URL_CIBLE, headers=HEADERS, timeout=15, allow_redirects=True)
    except requests.RequestException as e:
        print(f"[!] Erreur réseau lors de la requête : {e}")
        return

    # 1. Vérification de redirection ou suppression de la page
    final_url = response.url.rstrip("/")
    if final_url != URL_CIBLE.rstrip("/"):
        notify_user(
            "🚨 EUSPA : Redirection détectée !",
            f"La page a été redirigée vers : {final_url}. Les créneaux sont probablement ouverts !",
            final_url
        )
        return

    if response.status_code != 200:
        notify_user(
            "⚠️ EUSPA : Changement de statut HTTP",
            f"La page répond désormais avec le statut HTTP {response.status_code}.",
            URL_CIBLE
        )
        return

    soup = BeautifulSoup(response.text, "html.parser")

    # 2. Vérification du titre H1
    h1_tag = soup.find("h1")
    h1_text = h1_tag.get_text(strip=True).lower() if h1_tag else ""

    # 3. Vérification du corps de l'article principal
    article_tag = soup.find("article")
    article_text = article_tag.get_text(separator=" ", strip=True).lower() if article_tag else ""

    # Critères de blocage actuels (état fermé)
    is_still_coming_soon = "coming soon" in h1_text
    has_waiting_text = "will open at a later date" in article_text or "stay tuned" in article_text

    # Détection de changement
    if not is_still_coming_soon:
        notify_user(
            "🚨 EUSPA : Le titre 'Coming Soon' a disparu !",
            f"Nouveau titre détecté : '{h1_text}'. Rendez-vous sur le site immédiatement !",
            URL_CIBLE
        )
    elif not has_waiting_text:
        notify_user(
            "🚨 EUSPA : Le texte d'attente a changé !",
            "Le texte 'will open at a later date' n'est plus présent dans l'annonce.",
            URL_CIBLE
        )
    else:
        # Vérification si un nouveau bouton/lien a été ajouté dans le corps de l'article
        links = article_tag.find_all("a") if article_tag else []
        # Actuellement, il n'y a que le lien "Return to homepage"
        outbound_links = [
            a["href"] for a in links 
            if a.get("href") and "euspa-careerday.eu" not in a.get("href")
        ]
        if outbound_links:
            notify_user(
                "🚨 EUSPA : Nouveau lien de réservation détecté !",
                f"Lien trouvé : {outbound_links[0]}",
                outbound_links[0]
            )
        else:
            print(f"[{time.strftime('%H:%M:%S')}] RAS : Les réservations ne sont pas encore ouvertes.")

if __name__ == "__main__":
    verify_page()
