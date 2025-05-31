# ========================================
# 📌 Description du script :
#
# Ce script : 
# - Recherche les publications liées à un mot-clé depuis l'API Crossref.
# - Extrait les métadonnées : titre, auteur, date, DOI, résumé
# - Les résultats sont sauvegardés par tranches de 500 publications.
# - Met à jour automatiquement un fichier global fusionné après chaque tranche.
# - Reprend automatiquement là où il s’est arrêté en cas d’interruption.
# - Gère les erreurs et les connexions lentes (jusqu'à 60 tentatives de 5s)
# - Fournit une progression en pourcentage dans la console.
# ========================================


import requests
import time
import os
import glob
import pandas as pd

# === FONCTION PRINCIPALE ===
def fetch_crossref_data(mot_cle):
    nom_dossier = f"resultats_{mot_cle.replace(' ', '_')}"
    os.makedirs(nom_dossier, exist_ok=True)
    fichier_cursor = os.path.join(nom_dossier, "cursor.txt")
    fichier_combine = f"{nom_dossier}.xlsx"
    email_contact = "votre.email@example.com"

    if os.path.exists(fichier_cursor):
        with open(fichier_cursor, "r") as f:
            cursor = f.read().strip()
        print("🔁 Reprise à partir du dernier curseur enregistré.")
    else:
        cursor = "*"
        print("🚀 Nouvelle recherche commencée.")

    try:
        r_init = requests.get(
            "https://api.crossref.org/works",
            params={
                "query.bibliographic": mot_cle,
                "rows": 0,
                "mailto": email_contact
            },
            timeout=30
        )
        r_init.raise_for_status()
        total = r_init.json()["message"]["total-results"]
        print(f"\U0001f4ca Nombre total estimé de publications trouvées : {total}")
    except Exception as e:
        print(f"\u26a0\ufe0f Impossible d’obtenir le total initial : {e}")
        total = None

    def enregistrer_chunk(data, numero):
        df = pd.DataFrame(data)
        fichier = os.path.join(nom_dossier, f"chunk_{numero}.xlsx")
        df.to_excel(fichier, index=False)
        print(f"📂 Chunk {numero} sauvegardé ({len(df)} lignes)")
        return fichier

    def maj_fichier_combine():
        fichiers = sorted(glob.glob(os.path.join(nom_dossier, "chunk_*.xlsx")))
        all_dfs = []
        for f in fichiers:
            try:
                df = pd.read_excel(f)
                all_dfs.append(df)
            except Exception as e:
                print(f"❌ Erreur lecture {f} : {e}")
        if all_dfs:
            df_final = pd.concat(all_dfs, ignore_index=True)
            df_final.to_excel(fichier_combine, index=False)
            print(f"📁 Fichier combiné mis à jour : {fichier_combine} ({len(df_final)} lignes)")

    def trouver_prochain_numero():
        existants = glob.glob(os.path.join(nom_dossier, "chunk_*.xlsx"))
        if not existants:
            return 1
        numeros = [int(os.path.basename(f).split("_")[1].split(".")[0]) for f in existants]
        return max(numeros) + 1

    chunk_num = trouver_prochain_numero()
    count_total = (chunk_num - 1) * 500

    while True:
        try:
            for tentative in range(60):
                try:
                    r = requests.get(
                        "https://api.crossref.org/works",
                        params={
                            "query.bibliographic": mot_cle,
                            "rows": 500,
                            "cursor": cursor,
                            "mailto": email_contact,
                            "select": "title,author,issued,DOI,URL,abstract,subject"
                        },
                        timeout=30
                    )
                    r.raise_for_status()
                    break
                except Exception as e:
                    print(f"⚠\ufe0f Erreur (tentative {tentative+1}/60) : {e}")
                    time.sleep(5)
            else:
                print("❌ Abandon après 60 tentatives.")
                break

            data = r.json()["message"]
            items = data["items"]
            if not items:
                print("✅ Extraction terminée.")
                break

            lignes = []
            for item in items:
                lignes.append({
                    "titre": item.get("title", [""])[0],
                    "auteurs": "; ".join([f"{a.get('given', '')} {a.get('family', '')}" for a in item.get("author", [])]) if item.get("author") else "",
                    "date": "-".join(map(str, item.get("issued", {}).get("date-parts", [[None]])[0])),
                    "DOI": item.get("DOI", ""),
                    "URL": item.get("URL", ""),
                    "abstract": item.get("abstract", ""),
                    "mots_cles": "; ".join(item.get("subject", [])) if item.get("subject") else ""
                })

            fichier_chunk = enregistrer_chunk(lignes, chunk_num)
            count_total += len(lignes)
            maj_fichier_combine()

            if total:
                pourcentage = count_total / total * 100
                print(f"📈 Progression : {count_total}/{total} ({pourcentage:.2f}%)\n")
            else:
                print(f"📈 Progression : {count_total} lignes extraites\n")

            chunk_num += 1
            cursor = data["next-cursor"]
            with open(fichier_cursor, "w") as f:
                f.write(cursor)

            time.sleep(1 + 5 * (chunk_num % 3))

        except KeyboardInterrupt:
            print("⏹️ Interruption par l’utilisateur.")
            break

# === POINT D’ENTRÉE DU SCRIPT ===
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
        fetch_crossref_data(keyword)
