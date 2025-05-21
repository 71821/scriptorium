import requests
import pandas as pd
from urllib.parse import quote_plus

def get_total_results_for_year(keyword, year):
    encoded_keyword = quote_plus(keyword)
    url = (
        f"https://api.crossref.org/works?"
        f"query={encoded_keyword}&"
        f"filter=from-pub-date:{year}-01-01,until-pub-date:{year}-12-31"
        f"&rows=0"  # Pas besoin des résultats, juste total-results
    )
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        return data['message']['total-results']
    else:
        print(f"Erreur pour '{keyword}' en {year} : code {response.status_code}")
        return None

# Saisie mots-clés (séparés par des virgules)
keywords_input = input("Entrez les mots-clés / synonymes (séparés par des virgules) : ")
keywords = [k.strip() for k in keywords_input.split(",")]

start_year = int(input("Année de début : "))
end_year = int(input("Année de fin : "))

print("\nℹ️  EXPLICATIONS IMPORTANTES :")
print("- Chaque valeur correspond au nombre total de publications contenant le mot-clé pour l'année indiquée.")
print("- Les résultats ne sont PAS cumulés mais annuels.")
print("- Plusieurs mots-clés sont traités en parallèle et les résultats affichés dans un tableau.\n")

# Initialiser un dictionnaire avec années comme clés et dict de mots-clés/occurrences comme valeurs
results = {year: {} for year in range(start_year, end_year + 1)}

# Pour chaque mot-clé, récupérer le total par année
for keyword in keywords:
    print(f"\nRecherche pour mot-clé : '{keyword}'")
    for year in range(start_year, end_year + 1):
        count = get_total_results_for_year(keyword, year)
        results[year][keyword] = count
        if count is not None:
            print(f"  {year} : {count} publications")
        else:
            print(f"  {year} : Erreur ou données manquantes")

# Transformer le dictionnaire en DataFrame
# Les années en lignes, les mots-clés en colonnes
df = pd.DataFrame.from_dict(results, orient='index')
df.index.name = 'Année'
df.reset_index(inplace=True)

# Enregistrer en Excel
filename = f"crossref_multi_keywords_{start_year}_{end_year}.xlsx"
df.to_excel(filename, index=False)

print(f"\n✅ Données multi-mots-clés sauvegardées dans : {filename}")
