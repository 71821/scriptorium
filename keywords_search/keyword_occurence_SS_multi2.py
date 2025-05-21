# --------------------------------------------------------------------
# 🎯 OBJECTIF DU SCRIPT :
# - Analyse la fréquence d’apparition de mots-clés (ou synonymes) dans
#   la littérature scientifique via l'API Semantic Scholar.
# - Génère un fichier Excel par mot-clé (sécurité).
# - Gère les erreurs 429 (trop de requêtes) avec retry automatique.
# - À la fin, crée un tableau global : mots-clés en lignes, années en colonnes.
# --------------------------------------------------------------------

import requests
import pandas as pd
import time
from datetime import datetime
from urllib.parse import quote_plus

# 📝 Explication affichée à l'écran
print("\n📘 Que fait ce script ?")
print("- Il interroge Semantic Scholar pour chaque mot-clé et chaque année.")
print("- Il compte le nombre total de publications par mot-clé et par année.")
print("- Les résultats NE SONT PAS CUMULÉS : chaque valeur est annuelle.")
print("- Il crée un fichier Excel par mot-clé pour éviter les pertes en cas d'erreur.")
print("- À la fin, un tableau croisé global est généré.\n")

# 📥 Paramètres utilisateur
keywords_input = input("🔡 Entrez vos mots-clés (séparés par des virgules) : ")
keywords = [k.strip() for k in keywords_input.split(",")]

start_year = int(input("📅 Année de début : "))
end_year = int(input("📅 Année de fin : "))

# 🧮 Pour le tableau croisé final
global_data = {}

# 🔁 Boucle principale
for keyword in keywords:
    print(f"\n🔍 Mot-clé : '{keyword}'")
    yearly_data = []
    global_data[keyword] = {}

    for year in range(start_year, end_year + 1):
        retry_count = 0
        max_retries = 5

        while retry_count < max_retries:
            params = {
                "query": keyword,
                "year": year,
                "limit": 1,
                "fields": "title"
            }

            response = requests.get("https://api.semanticscholar.org/graph/v1/paper/search", params=params)

            if response.status_code == 200:
                total = response.json().get("total", 0)
                print(f"  ✅ {year} : {total} publications")
                yearly_data.append({"Mot-clé": keyword, "Année": year, "Occurrences": total})
                global_data[keyword][year] = total
                time.sleep(1)
                break  # sortie du while
            elif response.status_code == 429:
                retry_count += 1
                wait_time = 5 * retry_count
                print(f"  ⚠️  Erreur 429 pour '{keyword}' en {year} (Tentative {retry_count}) - Pause {wait_time} sec...")
                time.sleep(wait_time)
            else:
                print(f"  ❌ Erreur {response.status_code} pour '{keyword}' en {year}")
                yearly_data.append({"Mot-clé": keyword, "Année": year, "Occurrences": None})
                global_data[keyword][year] = None
                time.sleep(1)
                break  # erreur autre que 429

    # 💾 Sauvegarde fichier Excel individuel
    df = pd.DataFrame(yearly_data)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_keyword = keyword.replace(" ", "_").replace("/", "_")
    filename = f"semantic_keyword_{safe_keyword}_{start_year}_{end_year}_{timestamp}.xlsx"
    df.to_excel(filename, index=False)
    print(f"  💾 Résultats sauvegardés dans : {filename}")

# 📊 Création tableau croisé final (keywords en lignes, années en colonnes)
final_df = pd.DataFrame(global_data).T
final_df.index.name = "Mot-clé"
final_df = final_df[sorted(final_df.columns)]  # trie les années

# 💾 Sauvegarde du tableau croisé global
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
final_filename = f"semantic_tableau_global_{start_year}_{end_year}_{timestamp}.xlsx"
final_df.to_excel(final_filename)
print(f"\n📊 Tableau global sauvegardé dans : {final_filename}")
