# -------------------------------------------------------------
# Explication importante pour mémoire :
#
# - Chaque requête interroge Crossref pour un mot-clé donné, filtré par année.
# - La variable 'total-results' indique le nombre total de publications
#   contenant le mot-clé pour l'année précise.
# - Les résultats ne sont PAS cumulés d'année en année, mais correspondent
#   à des comptes annuels indépendants.
# - Cette méthode permet d'analyser l'évolution temporelle de la présence
#   d'un terme dans la littérature scientifique.
#
# - Limitation : la requête est faite année par année (plus longue si la période est large).
# -------------------------------------------------------------

import requests
import pandas as pd
from urllib.parse import quote_plus
from datetime import datetime

print("📚 Analyse de l'évolution d'un mot-clé dans la littérature scientifique via Crossref")
print("\nℹ️  Ce script effectue une requête par année pour le mot-clé donné.")
print("    Les résultats ne sont pas cumulés, mais correspondent au total annuel.")
print("    Utile pour observer l'évolution temporelle du mot dans les publications scientifiques.\n")

# 1. Saisie utilisateur : mot-clé + période
keyword = input("🔍 Mot-clé à rechercher : ")
start_year = int(input("📅 Année de début : "))
end_year = int(input("📅 Année de fin : "))

# 2. Encodage du mot-clé pour URL (gère espaces et caractères spéciaux)
encoded_keyword = quote_plus(keyword)

# 3. Dictionnaire pour stocker le nombre de publications par année
year_counts = {}

print(f"\n📡 Envoi des requêtes à Crossref pour le mot-clé : '{keyword}'\n")

# 4. Boucle année par année
for year in range(start_year, end_year + 1):
    url = (
        f"https://api.crossref.org/works?"
        f"query={encoded_keyword}&"
        f"filter=from-pub-date:{year}-01-01,until-pub-date:{year}-12-31&rows=0"
    )
    
    response = requests.get(url)

    if response.status_code == 200:
        data = response.json()
        count = data['message']['total-results']
        year_counts[year] = count
        print(f"✅ {year} | {keyword} : {count} publications")
    else:
        print(f"⚠️  Erreur pour l'année {year} : code {response.status_code}")
        year_counts[year] = None

# 5. Transformation en DataFrame
df = pd.DataFrame([
    {"Année": year, "Mot-clé": keyword, "Occurrences": count}
    for year, count in year_counts.items()
])

# 6. Génération du nom de fichier avec horodatage
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
safe_keyword = keyword.replace(" ", "_").replace(",", "_")
filename = f"crossref_{safe_keyword}_{start_year}_{end_year}_{timestamp}.xlsx"

# 7. Sauvegarde dans Excel
df.to_excel(filename, index=False)

print(f"\n💾 Données sauvegardées dans : {filename}")
