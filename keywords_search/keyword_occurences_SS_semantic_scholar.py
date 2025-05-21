# --------------------------------------------------------------------
# 🧠 SCRIPT D’ANALYSE BIBLIOGRAPHIQUE PAR MOT-CLÉ (API Semantic Scholar)
#
# 🎯 OBJECTIF :
# Ce script permet d’analyser la présence d’un mot-clé dans la littérature
# scientifique pour chaque année d’une période donnée.
#
# 📝 MÉTHODOLOGIE :
# - Pour chaque année, on interroge l'API Semantic Scholar avec un mot-clé.
# - On récupère le nombre TOTAL de publications contenant ce mot-clé publiées
#   spécifiquement cette année-là.
# - ⚠️ Ce nombre n’est PAS un cumul, mais bien un total annuel indépendant.
#   Il montre combien de *nouveaux articles* ont été publiés cette année avec le mot-clé.
#
# ✅ Le script gère les erreurs (ex: code 429 si trop de requêtes) avec des pauses.
# ✅ Les résultats sont sauvegardés dans un fichier Excel nommé automatiquement.
# --------------------------------------------------------------------

import requests
import pandas as pd
import time
from datetime import datetime
from urllib.parse import quote_plus

# -------------------------------------------------------
# 1. SAISIE DES PARAMÈTRES UTILISATEUR
# -------------------------------------------------------
print("\n🔍 Ce script analyse le nombre de publications scientifiques contenant un mot-clé donné, par année.")
print("📚 Source : API Semantic Scholar (graph.v1)")
print("ℹ️  Le nombre affiché correspond aux publications contenant le mot-clé et publiées cette année-là (non cumulatif).")

keyword = input("\n➡️  Entrez le mot-clé à rechercher (ex: informal economy) : ").strip()
start_year = int(input("➡️  Entrez l'année de début (ex : 2010) : "))
end_year = int(input("➡️  Entrez l'année de fin (ex : 2024) : "))

print(f"\n📊 Analyse en cours pour le mot-clé : **{keyword}**")
print(f"📆 Période : {start_year} à {end_year}\n")

# -------------------------------------------------------
# 2. INITIALISATION
# -------------------------------------------------------
base_url = "https://api.semanticscholar.org/graph/v1/paper/search"
results = []

# -------------------------------------------------------
# 3. BOUCLE ANNUELLE AVEC GESTION DES ERREURS 429
# -------------------------------------------------------
for year in range(start_year, end_year + 1):
    retry_count = 0
    max_retries = 5

    print(f"🔄 Année {year} - interrogation de l’API...")

    while retry_count < max_retries:
        params = {
            "query": keyword,
            "year": year,
            "limit": 1,  # On récupère juste un papier pour obtenir le total
            "fields": "title"
        }

        response = requests.get(base_url, params=params)

        if response.status_code == 200:
            total = response.json().get("total", 0)
            print(f"   ✅ {total} publications trouvées pour '{keyword}' en {year}.")
            print("   📌 Cela correspond aux nouvelles publications de cette année contenant ce mot-clé (non cumulatif).\n")
            results.append({"Année": year, "Occurrences": total})
            break
        elif response.status_code == 429:
            retry_count += 1
            wait_time = 5 * retry_count
            print(f"   ⚠️  Trop de requêtes (code 429). Pause {wait_time} secondes... (tentative {retry_count})")
            time.sleep(wait_time)
        else:
            print(f"   ❌ Erreur {response.status_code} pour l'année {year}. Résultat non disponible.\n")
            results.append({"Année": year, "Occurrences": None})
            break

    time.sleep(1)  # Pause pour éviter surcharge API

# -------------------------------------------------------
# 4. CONVERSION EN DATAFRAME
# -------------------------------------------------------
df = pd.DataFrame(results)

# -------------------------------------------------------
# 5. EXPORT EXCEL AVEC NOM UNIQUE
# -------------------------------------------------------
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
safe_keyword = quote_plus(keyword.replace(" ", "_"))
filename = f"semantic_{safe_keyword}_{start_year}_{end_year}_{timestamp}.xlsx"
df.to_excel(filename, index=False)

# -------------------------------------------------------
# 6. FIN ET EXPLICATION
# -------------------------------------------------------
print(f"\n✅ Analyse terminée !")
print(f"💾 Fichier sauvegardé : {filename}")
print("\n📈 Chaque ligne = une année. La colonne 'Occurrences' = nombre d’articles contenant le mot-clé publiés cette année-là.")
print("👉 Ce n’est PAS un cumul, mais un indicateur de tendance annuelle.")
print("Tu peux maintenant créer des graphiques pour observer l’évolution de l’intérêt scientifique sur ce terme.\n")
