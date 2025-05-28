import requests
from datetime import datetime
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

# Afficher un message explicatif
def afficher_message_explicatif():
    print("Ce script permet de récupérer tous les DOI d'une revue scientifique.")
    print("Il prend en entrée jusqu'à deux ISSN (imprimé et en ligne) d'une même revue.")
    print("Les DOI récupérés sont triés par date de création et sauvegardés dans un fichier texte.")
    print("-" * 80)

# Fonction pour formater l'ISSN
def format_issn(issn):
    return issn.replace("-", "")

# Fonction pour obtenir les articles avec pagination
def get_dois(url, cursor="*"):
    try:
        # Faire une requête HTTP pour obtenir les articles
        response = session.get(url, params={"rows": 1000, "cursor": cursor})
        response.raise_for_status()  # Vérifie si la requête a réussi

        # Vérifier si la réponse est au format JSON
        try:
            data = response.json()
        except ValueError:
            print("Erreur : La réponse de l'API n'est pas au format JSON.")
            data = None

        if data:
            # Extraire les DOI et les dates de création des articles
            dois_dates = [(item['DOI'], item['created']['date-time']) for item in data['message']['items']]
            journal_title = data['message']['items'][0]['container-title'][0] if data['message']['items'] else ""
            publisher = data['message']['items'][0]['publisher'] if data['message']['items'] else "Éditeur inconnu"
            issn_list = data['message']['items'][0]['ISSN'] if data['message']['items'] else []
            next_cursor = data['message'].get('next-cursor', None)
            return dois_dates, journal_title, publisher, issn_list, next_cursor
        else:
            print("Erreur : Aucune donnée trouvée.")
            return [], "", "Éditeur inconnu", [], None
    except requests.exceptions.RequestException as e:
        print(f"Erreur de requête HTTP : {e}")
        return [], "", "Éditeur inconnu", [], None

# Afficher le message explicatif
afficher_message_explicatif()

# Demander les ISSN de la revue à l'utilisateur
issn1 = input("Entrez le premier ISSN de la revue (par exemple, 0022-0388) : ")
issn2 = input("Entrez le deuxième ISSN de la revue (par exemple, 1743-9140) : ")

# Formater les ISSN
formatted_issn1 = format_issn(issn1)
formatted_issn2 = format_issn(issn2)

# URL de base de l'API CrossRef pour les ISSN
base_url1 = f"https://api.crossref.org/journals/{formatted_issn1}/works"
base_url2 = f"https://api.crossref.org/journals/{formatted_issn2}/works"

# Configurer le mécanisme de nouvelle tentative
session = requests.Session()
retry = Retry(
    total=5,
    backoff_factor=1,
    status_forcelist=[429, 500, 502, 503, 504],
)
adapter = HTTPAdapter(max_retries=retry)
session.mount('http://', adapter)
session.mount('https://', adapter)

# Initialiser les variables pour stocker les résultats
all_dois_dates = []
journal_title = ""
publisher = "Éditeur inconnu"
issn_list = []

# Récupérer les DOI en utilisant la pagination pour les deux ISSN
for base_url in [base_url1, base_url2]:
    cursor = "*"
    while cursor:
        dois_dates, title, pub, issns, cursor = get_dois(base_url, cursor)
        if dois_dates:
            all_dois_dates.extend(dois_dates)
            journal_title = title if title else journal_title
            publisher = pub if pub else publisher
            issn_list = list(set(issn_list + issns))
        else:
            break

# Trier les DOI par date de création
all_dois_dates.sort(key=lambda x: datetime.strptime(x[1], '%Y-%m-%dT%H:%M:%SZ'))
all_dois = [doi for doi, _ in all_dois_dates]

# Obtenir la date et l'heure actuelles pour le nom de fichier
current_time = datetime.now().strftime("%Y%m%d_%H%M%S")

# Afficher les détails de la revue et les DOI
print(f"Nom de la revue : {journal_title if journal_title else 'Titre inconnu'}")
print(f"Éditeur : {publisher}")
print("ISSN :")
for issn in issn_list:
    print(issn)
print(f"Nombre total de DOI récupérés : {len(all_dois)}")
print("DOI des articles :")
for doi in all_dois:
    print(doi)

# Sauvegarder les DOI dans un fichier texte
filename = f"{formatted_issn1}_{formatted_issn2}_{current_time}.txt"
with open(filename, "w") as file:
    file.write(f"Nom de la revue : {journal_title if journal_title else 'Titre inconnu'}\n")
    file.write(f"Éditeur : {publisher}\n")
    file.write("ISSN :\n")
    for issn in issn_list:
        file.write(f"{issn}\n")
    file.write(f"Nombre total de DOI récupérés : {len(all_dois)}\n")
    file.write("DOI des articles :\n")
    for doi in all_dois:
        file.write(doi + "\n")

print(f"Les DOI ont été sauvegardés dans le fichier '{filename}'.")
