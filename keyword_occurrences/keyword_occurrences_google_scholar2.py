# coding: utf-8

import time
import datetime
import xlwt
import unicodedata
import re as regex
import random
from bs4 import BeautifulSoup
from urllib.request import Request, build_opener
from urllib.parse import urlencode
import urllib.error

# Liste de User-Agents différents pour simuler plusieurs navigateurs
USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/122 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 Safari/605.1.15',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/113 Safari/537.36',
    'Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15 Mobile/15E148',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:111.0) Gecko/20100101 Firefox/111.0'
]

def sanitize_filename(text):
    """Nettoie un texte pour en faire un nom de fichier sûr."""
    text = unicodedata.normalize('NFKD', text).encode('ASCII', 'ignore').decode()
    text = regex.sub(r'\W+', '_', text)
    return text.strip('_')

def get_num_results(search_term, year, max_retries=3, wait_seconds=5):
    """
    Interroge Google Scholar pour obtenir le nombre de résultats d’un mot-clé pour une année spécifique.
    Gère les erreurs HTTP 429 (Too Many Requests) en réessayant jusqu’à `max_retries` fois.
    """
    query_params = {'q': search_term, 'as_ylo': year, 'as_yhi': year}
    url = "https://scholar.google.com/scholar?as_vis=1&hl=en&as_sdt=1,5&" + urlencode(query_params)

    for attempt in range(1, max_retries + 1):
        try:
            opener = build_opener()
            user_agent = random.choice(USER_AGENTS)
            request = Request(url=url, headers={'User-Agent': user_agent})

            handler = opener.open(request)
            html = handler.read()
            soup = BeautifulSoup(html, 'html.parser')
            div_results = soup.find("div", {"id": "gs_ab_md"})

            if div_results is not None:
                import re
                res = re.findall(r'(\d+).?(\d+)?\.?(\d+)?\s', div_results.text)
                if not res:
                    return 0, True
                else:
                    number = ''.join(res[0])
                    return int(number), True
            else:
                return 0, False
        except urllib.error.HTTPError as e:
            if e.code == 429:
                print(f"   ⚠️  Erreur 429 (trop de requêtes). Tentative {attempt}/{max_retries}. Attente {wait_seconds}s...")
                time.sleep(wait_seconds)
            else:
                print(f"   ❌ Erreur HTTP {e.code} : {e.reason}")
                break
        except Exception as e:
            print(f"   ❌ Erreur inattendue : {e}")
            break

    return None, False  # toutes les tentatives échouées

def get_range(search_term, start_date, end_date, output_filename):
    """Réalise les requêtes pour toutes les années et sauvegarde les résultats dans un fichier Excel .xls."""
    workbook = xlwt.Workbook()
    sheet = workbook.add_sheet("Résultats")
    sheet.write(0, 0, "Année")
    sheet.write(0, 1, "Nombre de publications")

    print("\n📈 Début de l’analyse par année...")
    print("ℹ️  Chaque chiffre correspond au nombre de publications contenant le mot-clé, publiées cette année-là.\n")

    for i, year in enumerate(range(start_date, end_date + 1), start=1):
        print(f"🔄 Requête pour l’année {year}...")

        num_results, success = get_num_results(search_term, year)

        if success:
            print(f"   ✅ {year} : {num_results} résultats")
        else:
            print(f"   ⚠️  Requête échouée ou bloquée pour {year}. Résultat : None")

        sheet.write(i, 0, year)
        sheet.write(i, 1, num_results if num_results is not None else "")

        pause = round(random.uniform(1.0, 7.0), 2)
        print(f"   ⏸️ Pause de {pause}s avant la prochaine requête...\n")
        time.sleep(pause)

    workbook.save(output_filename)
    print(f"\n💾 Données enregistrées dans le fichier : {output_filename}")
    print("📌 Analyse terminée.")

if __name__ == "__main__":
    print("""
--------------------------------------------------
🧠 Script Google Scholar – Analyse temporelle
--------------------------------------------------

Ce script :
✔️ Demande un mot-clé et une période (année de début et de fin)
✔️ Interroge Google Scholar pour estimer le nombre de publications par année
✔️ Sauvegarde les résultats dans un fichier Excel (.xls)
✔️ Gère les erreurs temporaires (429 - trop de requêtes)
✔️ Ajoute une pause aléatoire + rotation des User-Agent
--------------------------------------------------
""")

    search_term_raw = input("🔎 Terme à rechercher : ").strip()
    search_term = f'"{search_term_raw}"'

    try:
        start_date = int(input("📅 Année de début : "))
        end_date = int(input("📅 Année de fin   : "))
    except ValueError:
        print("❌ Les années doivent être des nombres entiers.")
        exit(1)

    if start_date > end_date:
        print("❌ L’année de début doit être inférieure ou égale à l’année de fin.")
        exit(1)

    now = datetime.datetime.now()
    time_str = now.strftime("%Y%m%d_%H%M%S")
    safe_term = sanitize_filename(search_term_raw)
    output_file = f"gscholar_{safe_term}_{start_date}_{end_date}_{time_str}.xls"

    get_range(search_term, start_date, end_date, output_file)
