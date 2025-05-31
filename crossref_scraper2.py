
# ========================================
# 📌 Description du script :
#
# Ce script : 
# - Recherche les publications liées à un mot-clé depuis l'API Crossref.
# - Extrait les métadonnées : titre, auteur, date, DOI, résumé
# - Les résultats sont sauvegardés par tranches de 500 publications.
# - Met à jour automatiquement un fichier global fusionné après chaque tranche.
# - Demande s'il faut reprendre là où il s’est arrêté ou non en cas d’interruption.
# - Gère les erreurs et les connexions lentes (jusqu'à 60 tentatives de 5s)
# - Fournit une progression en pourcentage dans la console.
# ========================================


import requests
import time
import os
import json
import pandas as pd
from urllib.parse import quote

def fetch_crossref_data(keyword, resume=False):
    encoded_keyword = quote(keyword)
    base_url = "https://api.crossref.org/works"
    rows_per_request = 500
    email = "votre.email@example.com"
    headers = {"User-Agent": f"Python Script (mailto:{email})"}

    # Dossiers de sauvegarde
    output_folder = f"resultats_{keyword.replace(' ', '_')}"
    os.makedirs(output_folder, exist_ok=True)
    combined_file = f"{output_folder}.xlsx"
    cursor_file = os.path.join(output_folder, "cursor.txt")

    # Reprendre à partir du dernier curseur ?
    if resume and os.path.exists(cursor_file):
        with open(cursor_file, "r") as f:
            cursor = f.read().strip()
        print("🔁 Reprise intelligente à partir du dernier curseur sauvegardé...")
    else:
        cursor = "*"
        print("🚀 Nouvelle extraction depuis le début...")

    # Chercher le nombre total estimé de résultats
    try:
        count_response = requests.get(
            f"{base_url}?query.bibliographic={encoded_keyword}&rows=0&mailto={email}",
            headers=headers, timeout=30
        )
        count_response.raise_for_status()
        total_results = count_response.json()["message"]["total-results"]
        print(f"\n📊 Nombre total estimé de publications trouvées : {total_results}\n")
    except Exception as e:
        print(f"❌ Erreur lors de la récupération du nombre total de résultats : {e}")
        total_results = None

    all_chunks = []
    chunk_number = 1
    total_saved = 0

    if resume:
        # Trouver le dernier chunk existant
        existing_chunks = [f for f in os.listdir(output_folder) if f.startswith("chunk_") and f.endswith(".xlsx")]
        if existing_chunks:
            chunk_numbers = [int(f.split("_")[1].split(".")[0]) for f in existing_chunks]
            chunk_number = max(chunk_numbers) + 1
            total_saved = (chunk_number - 1) * rows_per_request

    while True:
        params = {
            "query.bibliographic": keyword,
            "rows": rows_per_request,
            "cursor": cursor,
            "mailto": email,
        }

        success = False
        for attempt in range(60):
            try:
                response = requests.get(base_url, params=params, headers=headers, timeout=30)
                response.raise_for_status()
                data = response.json()
                success = True
                break
            except Exception as e:
                print(f"⚠️ Erreur (tentative {attempt+1}/60) : {e}")
                time.sleep(5)

        if not success:
            print("❌ Échec après 60 tentatives. Fin de l'extraction.")
            break

        items = data["message"]["items"]
        if not items:
            print("✅ Aucune donnée supplémentaire. Extraction terminée.")
            break

        chunk_data = []
        for item in items:
            title = item.get("title", [""])[0]
            authors = ", ".join([f"{a.get('given', '')} {a.get('family', '')}".strip() for a in item.get("author", [])]) if "author" in item else ""
            date_parts = item.get("issued", {}).get("date-parts", [[None]])
            year = date_parts[0][0]
            doi = item.get("DOI", "")
            url = item.get("URL", "")
            abstract = item.get("abstract", "")
            chunk_data.append({
                "Titre": title,
                "Auteurs": authors,
                "Année": year,
                "DOI": doi,
                "URL": url,
                "Résumé": abstract
            })

        df_chunk = pd.DataFrame(chunk_data)
        chunk_path = os.path.join(output_folder, f"chunk_{chunk_number}.xlsx")
        df_chunk.to_excel(chunk_path, index=False)
        print(f"\n💾 Chunk {chunk_number} sauvegardé ({len(df_chunk)} lignes)")

        # Mise à jour fichier combiné
        if os.path.exists(combined_file):
            df_existing = pd.read_excel(combined_file)
            df_combined = pd.concat([df_existing, df_chunk], ignore_index=True)
        else:
            df_combined = df_chunk
        df_combined.to_excel(combined_file, index=False)
        total_saved = len(df_combined)
        print(f"📁 Fichier combiné mis à jour : {combined_file} ({total_saved} lignes)")

        chunk_number += 1
        cursor = data["message"]["next-cursor"]
        with open(cursor_file, "w") as f:
            f.write(cursor)

        if total_results:
            percent = (total_saved / total_results) * 100
            print(f"📈 Progression : {total_saved}/{total_results} ({percent:.2f}%)")
        else:
            print(f"📈 Progression : {total_saved} lignes extraites...")

        # Pause aléatoire entre 1 et 7 secondes
        time.sleep(1 + (6 * time.time() % 1))


if __name__ == "__main__":
    print("""
-----------------------------------------------------
📘 Script Crossref – Extraction massive de publications
-----------------------------------------------------
Ce script :
✔️ Recherche toutes les publications associées à un mot-clé
✔️ Extrait les métadonnées : titre, auteur, date, DOI, résumé
✔️ Sauvegarde automatiquement par tranches de 500 résultats
✔️ Met à jour automatiquement un fichier combiné global
✔️ Gère les erreurs et les connexions lentes (jusqu’à 60 essais)

⚠️ Important :
Le mot-clé sera recherché dans le **titre** et le champ **bibliographique**.
-----------------------------------------------------
""")
    keyword = input("🔎 Entrez le mot-clé à rechercher : ").strip()
    if not keyword:
        print("❌ Vous devez entrer un mot-clé valide.")
    else:
        reprendre = input("🔁 Reprendre à partir de la dernière interruption ? (o/n) : ").strip().lower()
        fetch_crossref_data(keyword, resume=(reprendre == 'o'))
