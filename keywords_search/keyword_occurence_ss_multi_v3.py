import requests
import pandas as pd
import time
import random
import datetime
from tqdm import tqdm

# 📌 Fonction de requête API Semantic Scholar
def get_publication_count(keyword, year, max_retries=5):
    url = "https://api.semanticscholar.org/graph/v1/paper/search"
    params = {
        "query": keyword,
        "year": year,
        "limit": 1,  # On ne veut que le nombre total
        "fields": "title"
    }

    for attempt in range(max_retries):
        try:
            response = requests.get(url, params=params)
            if response.status_code == 200:
                return response.json().get("total", 0)
            elif response.status_code == 429:
                wait = 5 + attempt * 2
                print(f"⚠️  Trop de requêtes (429). Pause de {wait} secondes...")
                time.sleep(wait)
            else:
                print(f"❌ Erreur {response.status_code} pour {keyword} ({year})")
                return None
        except Exception as e:
            print(f"⛔ Erreur : {e}")
            time.sleep(5)
    return None

# 🔁 Analyse de tous les mots-clés
def analyze_keywords(keywords, start_year, end_year):
    global_results = []

    print("\n📊 Lancement de l’analyse pour chaque mot-clé...\n")

    for keyword in keywords:
        print(f"🔍 Mot-clé : '{keyword}'")
        keyword_results = []

        for year in tqdm(range(start_year, end_year + 1)):
            count = get_publication_count(keyword, year)
            keyword_results.append({
                "Mot-clé": keyword,
                "Année": year,
                "Occurrences": count
            })
            time.sleep(random.uniform(1.0, 2.5))

        # 💾 Sauvegarde individuelle
        df_indiv = pd.DataFrame(keyword_results)
        filename = f"semantic_keyword_{keyword.replace(' ', '_')}_{start_year}_{end_year}_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        df_indiv.to_excel(filename, index=False)
        print(f"✅ Résultats sauvegardés dans : {filename}\n")

        global_results.extend(keyword_results)

    return pd.DataFrame(global_results)

# 🔁 Création du tableau croisé
def create_pivot_table(df, output_filename="semantic_summary.xlsx"):
    pivot = df.pivot_table(index="Mot-clé", columns="Année", values="Occurrences", fill_value=0)
    pivot.to_excel(output_filename)
    print(f"\n📈 Tableau comparatif sauvegardé dans : {output_filename}")

# 🚀 Programme principal
if __name__ == "__main__":
    print("\n🧠 Analyse multi-mots-clés avec l’API Semantic Scholar")
    print("🎯 Objectif : Voir l'évolution annuelle du nombre de publications contenant chaque mot-clé.")
    print("ℹ️  Les chiffres correspondent aux **nouvelles publications** de chaque année.\n")

    # Demander les paramètres
    start_year = int(input("📅 Année de début : "))
    end_year = int(input("📅 Année de fin   : "))

    # Liste de mots-clés manuelle
    raw_keywords = input("📝 Entrez les mots-clés séparés par des virgules :\n👉 ")
    keywords = [kw.strip() for kw in raw_keywords.split(",") if kw.strip()]

    # Lancer l’analyse
    df_all = analyze_keywords(keywords, start_year, end_year)

    # Créer le tableau comparatif
    create_pivot_table(df_all)
