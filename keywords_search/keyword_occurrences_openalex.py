import requests
import pandas as pd
import time
import datetime
from urllib.parse import quote

# --------------
# FONCTION UTILE
# --------------
def query_openalex(keyword, start_year, end_year, pause=1.5, max_retries=5):
    """
    Interroge l'API OpenAlex pour compter le nombre de publications par mot-clé et par année.
    """
    base_url = "https://api.openalex.org/works"
    results = []

    print(f"\n🔍 Mot-clé : '{keyword}'")
    print("ℹ️  Chaque chiffre correspond au nombre de publications contenant le mot-clé, publiées l’année correspondante.")

    for year in range(start_year, end_year + 1):
        success = False
        attempts = 0
        while not success and attempts < max_retries:
            params = {
                "search": keyword,
                "filter": f"from_publication_date:{year}-01-01,to_publication_date:{year}-12-31",
                "per-page": 1
            }
            try:
                response = requests.get(base_url, params=params, timeout=15)
                response.raise_for_status()
                data = response.json()
                count = data.get("meta", {}).get("count", 0)
                print(f"✅ {year} : {count} publications")
                results.append({"Mot-clé": keyword, "Année": year, "Occurrences": count})
                success = True
            except requests.exceptions.RequestException as e:
                attempts += 1
                wait = pause * (2 ** attempts)
                print(f"⚠️  Erreur pour '{keyword}' en {year} (Tentative {attempts}/{max_retries}) - attente {wait:.1f}s")
                time.sleep(wait)
        if not success:
            print(f"❌ Échec pour {keyword} en {year} après {max_retries} tentatives.")
            results.append({"Mot-clé": keyword, "Année": year, "Occurrences": None})
    return results

# -----------------
# PROGRAMME PRINCIPAL
# -----------------
if __name__ == "__main__":
    print("""
===========================================================
📊 Analyse des publications par mot-clé via l'API OpenAlex
===========================================================

Ce script permet de rechercher plusieurs mots-clés sur la période
souhaitée et de sauvegarder les résultats par mot-clé dans des
fichiers Excel, ainsi qu’un tableau comparatif final.
    """)

    start_year = int(input("📅 Année de début : "))
    end_year = int(input("📅 Année de fin   : "))

    print("\n💡 Entrez vos mots-clés séparés par une virgule (ex: informal economy, shadow economy, économie informelle)")
    raw_keywords = input("🔠 Mots-clés : ")
    keywords = [k.strip() for k in raw_keywords.split(",") if k.strip()]

    all_data = []

    for keyword in keywords:
        keyword_data = query_openalex(keyword, start_year, end_year)
        df = pd.DataFrame(keyword_data)
        all_data.extend(keyword_data)

        now = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_kw = quote(keyword.replace(" ", "_").lower())
        fname = f"openalex_keyword_{safe_kw}_{start_year}_{end_year}_{now}.xlsx"
        df.to_excel(fname, index=False)
        print(f"💾 Résultats sauvegardés dans : {fname}\n")

    # Création du tableau croisé
    df_all = pd.DataFrame(all_data)
    df_pivot = df_all.pivot(index="Mot-clé", columns="Année", values="Occurrences")

    now = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    fname_final = f"openalex_tableau_comparatif_{start_year}_{end_year}_{now}.xlsx"
    df_pivot.to_excel(fname_final)
    print(f"📊 Tableau comparatif sauvegardé dans : {fname_final}")
