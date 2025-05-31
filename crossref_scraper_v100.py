##########################################################################
#
# Script : Extraction de publications via l'API Crossref
# ------------------------------------------------------
#
# Ce script permet d'extraire toutes les publications contenant un mot-clé donné,
# présent dans le titre ou les mots-clés via l'API publique de Crossref.
#
# Fonctionnalités :
#    - Extraction complète sans limite (par lots de 500).
#    - Reprise automatique en cas d'arrêt, avec détection des fichiers sauvegardés.
#    - Enregistrement des résultats par tranche (chunk) au format Excel.
#    - Gestion des erreurs réseau avec 5 minutes de tentatives progressives.
#    - Fusion finale des données extraites.
#    - Affichage progressif, suivi en pourcentage et message clair pour l'utilisateur.
#
##########################################################################

import requests
import time
import pandas as pd
import os
import re
from urllib.parse import quote

# === PARAMÈTRES GLOBAUX ===
CHUNK_SIZE = 500
MAX_TOTAL_RETRIES = 60  # nombre total de tentatives (5 minutes)
RETRY_INTERVAL = 5      # en secondes
EMAIL = "votre.email@example.com"  # à modifier
OUTPUT_DIR = "crossref_results"

# === FONCTION : récupérer le dernier chunk existant ===
def detect_last_chunk(keyword_slug):
    existing = [
        f for f in os.listdir(OUTPUT_DIR)
        if re.match(rf"chunk_(\d+)_({keyword_slug})\.xlsx", f)
    ]
    if not existing:
        return 0
    indices = [int(re.findall(r"chunk_(\d+)_", name)[0]) for name in existing]
    return max(indices)

# === INITIALISATION ===
os.makedirs(OUTPUT_DIR, exist_ok=True)


print("\n🔎 Ce script extrait toutes les publications de Crossref liées à un mot-clé.")
print("📘 Il recherche dans les titres et les mots-clés des publications.")
print("💾 Les résultats sont sauvegardés par tranches de 500 dans des fichiers Excel.")
print("🔁 En cas d'arrêt, vous pourrez relancer et reprendre l'extraction.\n")


keyword = input("🔍 Entrez le mot-clé à rechercher (dans le titre ou les mots-clés) : ").strip()
if not keyword:
    print("❌ Mot-clé vide. Script annulé.")
    exit()

safe_keyword = quote(keyword)
keyword_slug = keyword.replace(" ", "_")
cursor = "*"
all_dataframes = []

# === DÉTECTION DE SAUVEGARDES EXISTANTES ===
last_chunk = detect_last_chunk(keyword_slug)
resume = False

if last_chunk > 0:
    print(f"\n📁 {last_chunk} chunks précédents détectés pour « {keyword} ».")
    rep = input("↩️ Voulez-vous reprendre à partir du dernier chunk sauvegardé ? (o/n) : ").lower()
    if rep == 'o':
        resume = True
        cursor_df = pd.read_excel(os.path.join(OUTPUT_DIR, f"chunk_{last_chunk}_{keyword_slug}.xlsx"))
        # Charger tous les chunks précédents
        for i in range(1, last_chunk + 1):
            df_part = pd.read_excel(os.path.join(OUTPUT_DIR, f"chunk_{i}_{keyword_slug}.xlsx"))
            all_dataframes.append(df_part)
    else:
        print("🧹 Suppression des anciens fichiers...")
        for f in os.listdir(OUTPUT_DIR):
            if re.match(rf"chunk_\d+_{keyword_slug}\.xlsx", f) or f.startswith(f"crossref_all_{keyword_slug}"):
                os.remove(os.path.join(OUTPUT_DIR, f))
        last_chunk = 0

chunk_count = last_chunk
print("\n🚀 Lancement de l'extraction depuis Crossref...")
print("⏳ Les résultats s'affichent progressivement. Veuillez patienter...\n")

while True:
    url = (
        f"https://api.crossref.org/works?query.bibliographic={safe_keyword}"
        f"&rows={CHUNK_SIZE}&cursor={cursor}&mailto={EMAIL}"
    )

    retry_count = 0
    success = False

    while retry_count < MAX_TOTAL_RETRIES:
        try:
            response = requests.get(url, timeout=30)
            if response.status_code != 200:
                raise requests.exceptions.HTTPError(f"Code {response.status_code}")
            data = response.json()
            success = True
            break
        except Exception as e:
            retry_count += 1
            print(f"⚠️ Erreur (tentative {retry_count}/60) : {e}")
            time.sleep(RETRY_INTERVAL)

    if not success:
        print("❌ Échec définitif après plusieurs tentatives.")
        break

    items = data['message']['items']
    if not items:
        print("✅ Tous les résultats ont été extraits.")
        break

    if chunk_count == 0:
        total_results = data['message']['total-results']
        print(f"📊 Total de publications trouvées : {total_results}\n")

    rows = []
    for item in items:
        title = item.get('title', [''])[0]
        authors = ", ".join(
            [f"{a.get('given', '')} {a.get('family', '')}" for a in item.get('author', [])]
        )
        date_parts = item.get('issued', {}).get('date-parts', [[None]])
        year = date_parts[0][0] if date_parts else None
        doi = item.get('DOI', '')
        url = item.get('URL', '')
        abstract = item.get('abstract', '')
        keywords = ", ".join(item.get('subject', []))

        rows.append({
            "Titre": title,
            "Auteurs": authors,
            "Année": year,
            "DOI": doi,
            "URL": url,
            "Résumé": abstract,
            "Mots-clés": keywords
        })

    df = pd.DataFrame(rows)
    chunk_count += 1
    filename = os.path.join(OUTPUT_DIR, f"chunk_{chunk_count}_{keyword_slug}.xlsx")
    df.to_excel(filename, index=False)
    all_dataframes.append(df)

    print(f"📦 Chunk {chunk_count} → {filename} ({len(rows)} publications)")

    cursor = data['message']['next-cursor']
    time.sleep(1)

# === SAUVEGARDE FINALE ===
if all_dataframes:
    final_df = pd.concat(all_dataframes, ignore_index=True)
    final_name = os.path.join(OUTPUT_DIR, f"crossref_all_{keyword_slug}.xlsx")
    final_df.to_excel(final_name, index=False)
    print(f"\n💾 Fusion complète sauvegardée : {final_name}")
else:
    print("📭 Aucun résultat n’a été traité.")
