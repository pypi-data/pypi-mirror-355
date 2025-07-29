import os
import json
import hashlib
import getpass

if "site-packages/Orange/widgets" in os.path.dirname(os.path.abspath(__file__)).replace("\\", "/"):
    from Orange.widgets.orangecontrib.AAIT.utils import MetManagement
else:
    from orangecontrib.AAIT.utils import MetManagement

# Fonction pour générer une clé simple à partir du nom d'utilisateur
def get_user_key():
    try:
        try:
            username = os.getlogin()
        except OSError:
            username = getpass.getuser()

        if not username:
            raise ValueError("Nom d'utilisateur introuvable")

        # On dérive une clé simple (1 octet) depuis le hash du nom d'utilisateur
        digest = hashlib.sha256(username.encode("utf-8")).digest()
        key = digest[0]  # 1 octet pour XOR
        return key

    except Exception as e:
        raise RuntimeError(f"Erreur de génération de clé : {e}")

# Fonction simple de chiffrement/déchiffrement par XOR (non sécurisé mais obscurcissant)
def xor_crypt(data: str, key: int) -> str:
    return ''.join(chr(ord(c) ^ (key & 0xFF)) for c in data)

# Fonction pour enregistrer les données dans un fichier JSON avec le mot de passe chiffré
def enregistrer_config(agent, my_domain, password, interval_second):
    try:
        dossier=MetManagement.get_secret_content_dir()
        # Crée le dossier s'il n'existe pas
        if not os.path.exists(dossier):
            os.makedirs(dossier)

        # Récupère l'adresse MAC et chiffre le mot de passe
        key = get_user_key()
        mdp_chiffre = xor_crypt(password, key)

        # Nom du fichier (remplace @ par _at_ pour éviter les problèmes)
        nom_fichier = os.path.join(dossier, f"{agent}{my_domain.replace('@', '_at_')}.json")

        # Contenu à écrire dans le fichier
        contenu = {
            "agent": agent,
            "domain": my_domain,
            "interval_second": interval_second,
            "password_encrypted": mdp_chiffre
        }

        # Écriture du fichier
        with open(nom_fichier, "w", encoding="utf-8") as f:
            json.dump(contenu, f, indent=4)

        print(f"✅ Fichier enregistré : {nom_fichier}")
        return 0

    except Exception as e:
        print(f"❌ Erreur lors de l'enregistrement : {e}")
        return 1

# Fonction pour lire le fichier de configuration et déchiffrer le mot de passe
def lire_config(chemin_fichier):
    # renvoie une liste =["agent","domain",mdp,"interval_second"]
    try:
        chemin_fichier=MetManagement.get_secret_content_dir()+chemin_fichier
        # Lecture du fichier JSON
        with open(chemin_fichier, "r", encoding="utf-8") as f:
            contenu = json.load(f)

        # Récupère l'adresse MAC
        key = get_user_key()

        # Déchiffre le mot de passe
        mdp_dechiffre = xor_crypt(contenu["password_encrypted"], key)


        return [
            contenu["agent"],
            contenu["domain"],
            mdp_dechiffre,
            int(contenu["interval_second"]),
        ]


    except Exception as e:
        print(f"❌ Erreur lors de la lecture : {e}")
        return None
def enregistrer_config_cli():
    print("\n📝 Écriture d’un fichier de configuration :")
    agent = input("🤖 Nom de l’agent : ").strip()
    domaine = input("📨 @domain.com? : ").strip()
    mdp = input("📨mot de passe? : ").strip()
    interval = int(input("⏱️ Intervalle en secondes : ").strip())
    if 0!= enregistrer_config(agent,domaine,mdp,interval):
        print("erreur!")


def lire_config_cli():
    chemin_fichier = input("📄 non fichier json (pas le chemin!) JSON : ").strip()
    config = lire_config(chemin_fichier)

    if config==None:
        print("erreur")
    print(config)



if __name__ == "__main__":
    print("1) ecrire fichier")
    print("2) dechiffer fichier")
    choix = input("👉 que faire? [1/2] : ").strip()

    if choix == "1":
        enregistrer_config_cli()
    elif choix == "2":
        lire_config_cli()
    else:
        print("❌ Choix invalide. Réessayez.\n")

