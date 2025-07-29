import imaplib
import smtplib
import email
from email.header import decode_header
import time
import os
from email import policy
from email.message import EmailMessage
if "site-packages/Orange/widgets" in os.path.dirname(os.path.abspath(__file__)).replace("\\", "/"):
    from Orange.widgets.orangecontrib.AAIT.utils import MetManagement
    from Orange.widgets.orangecontrib.IO4IT.utils import offuscation_basique
else:
    from orangecontrib.AAIT.utils import MetManagement
    from orangecontrib.IO4IT.utils import offuscation_basique


def clean_addresses(field,myemail):
    """Retourne une liste d'adresses nettoyées sans ton adresse"""
    if not field:
        return []
    addresses = email.utils.getaddresses([field])
    return [addr for name, addr in addresses if addr.lower() != myemail.lower()]

def mail_in_folder(agent_name, type="in"):
    if agent_name is None or agent_name == "":
        print("agent_name doit etre renseigné")
        return None
    chemin_dossier= MetManagement.get_path_mailFolder()
    if type == "in":
        if not os.path.exists(chemin_dossier):
            os.makedirs(chemin_dossier)
        real_time = MetManagement.get_second_from_1970()
        folder_in = chemin_dossier + "/" + str(agent_name) + "/in/" + str(real_time)
        folder_out = chemin_dossier + "/" + str(agent_name) + "/out/" + str(real_time)
        if not os.path.exists(folder_in) and not os.path.exists(folder_out):
            os.makedirs(folder_in)
            os.makedirs(folder_out)
        else:
            time.sleep(1.5)
            mail_in_folder(agent_name, "in")
        return folder_in
    if  type == "out":
        return chemin_dossier + str(agent_name) + "/in/", chemin_dossier + "/" + str(agent_name) + "/out/"


def check_new_emails(offusc_conf_agent):
    try:
        agent,my_domain,password,interl_seconds=offuscation_basique.lire_config(offusc_conf_agent)
        myemail=agent + my_domain
        imap = imaplib.IMAP4_SSL("imap.gmail.com")
        imap.login(myemail, password)
        imap.select("inbox")

        status, messages = imap.search(None, 'UNSEEN')
        mail_ids = messages[0].split()

        if not mail_ids:
            print("Aucun nouveau mail.")
        else:
            for mail_id in mail_ids:
                time.sleep(1.5)
                output_lines = []
                _, msg_data = imap.fetch(mail_id, "(RFC822)")
                for response_part in msg_data:
                    if isinstance(response_part, tuple):
                        from email.parser import BytesParser

                        # Utilise :
                        msg = BytesParser(policy=policy.default).parsebytes(response_part[1])

                        # Sujet
                        subject, encoding = decode_header(msg["Subject"])[0]
                        if isinstance(subject, bytes):
                            subject = subject.decode(encoding if encoding else "utf-8")

                        # Expéditeur
                        from_ = msg.get("From")

                        # Destinataires
                        to_emails = clean_addresses(msg.get("To", ""),myemail)
                        cc_emails = clean_addresses(msg.get("Cc", ""),myemail)

                        # Corps
                        body = ""
                        if msg.is_multipart():
                            for part in msg.walk():
                                content_type = part.get_content_type()
                                content_disposition = str(part.get("Content-Disposition"))

                                if content_type == "text/plain" and "attachment" not in content_disposition:
                                    payload = part.get_payload(decode=True)
                                    charset = part.get_content_charset()
                                    body = payload.decode(charset if charset else "utf-8", errors="replace")
                                    break
                        else:
                            body = msg.get_payload(decode=True).decode(errors="replace")

                        # Format de sortie
                        output_lines.append(f"#$who : {myemail}")
                        output_lines.append(f"#$eme : {from_}")
                        output_lines.append(f"#$des : {', '.join(to_emails)}")
                        output_lines.append(f"#$cop : {', '.join(cc_emails)}")
                        output_lines.append("#$pri : Normale")
                        output_lines.append(f"#$tit : {subject}")
                        output_lines.append(f"#$txt : {body.strip()}")
                        output_lines.append("")
                        print("----------------------------------------")
                        print(f"mail recu de {from_}")
                        print("----------------------------------------")

                        if output_lines != []:
                            folder = mail_in_folder(agent, "in")
                            if folder is None:
                                print("erreur dans le folder de mail")
                                return

                            with open(folder + "/" + "mail.txt", "w", encoding="utf-8") as f:
                                f.write("\n".join(output_lines))
                                f.close()

                            with open(folder + "/" + "mail.ok", "w") as f:
                                f.close()

                            for part in msg.iter_attachments():
                                filename = part.get_filename()
                                if filename:
                                    folder_pj = folder + "/" + "pj"
                                    if not os.path.exists(folder_pj):
                                        os.makedirs(folder_pj)
                                    filepath = os.path.join(folder_pj, filename)
                                    with open(filepath, "wb") as f:
                                        f.write(part.get_payload(decode=True))
                                    f.close()

        imap.logout()
    except Exception as e:
        print(f"Erreur lors de la vérification des mails : {e}")


def lire_message(chemin_fichier):
    donnees = {}
    cle_courante = None
    texte_multi_ligne = []

    with open(chemin_fichier, 'r', encoding='utf-8') as fichier:
        for ligne in fichier:
            if ligne.startswith('#$'):
                if cle_courante == 'txt' and texte_multi_ligne:
                    donnees['txt'] = '\n'.join(texte_multi_ligne).strip()
                    texte_multi_ligne = []

                cle_val = ligne[2:].split(':', 1)
                cle_courante = cle_val[0].strip()

                if cle_courante == 'txt':
                    texte_multi_ligne.append(cle_val[1].strip())
                else:
                    donnees[cle_courante] = cle_val[1].strip()
            else:
                if cle_courante == 'txt':
                    texte_multi_ligne.append(ligne.rstrip())

    # En fin de fichier, enregistrer le texte si encore en cours
    if cle_courante == 'txt' and texte_multi_ligne:
        donnees['txt'] = '\n'.join(texte_multi_ligne).strip()

    return donnees




def send_mail(expediteur, offusc_conf_agent, destinataire, sujet, contenu,piece_jointe_path=None, serveur="smtp.gmail.com", port=587):
    msg = EmailMessage()
    msg['From'] = expediteur
    msg['To'] = destinataire
    msg['Subject'] = sujet
    msg.set_content(contenu)
    # Ajout d'une pièce jointe si fournie
    if piece_jointe_path:
        with open(piece_jointe_path, 'rb') as f:
            data = f.read()
            nom_fichier = piece_jointe_path.split('/')[-1]
            msg.add_attachment(data, maintype='application', subtype='octet-stream', filename=nom_fichier)
    try:
        _, _, mot_de_passe, _ = offuscation_basique.lire_config(offusc_conf_agent)
        with smtplib.SMTP(serveur, port) as smtp:
            smtp.starttls()
            smtp.login(expediteur, mot_de_passe)
            smtp.send_message(msg)
        return 0
    except Exception as e:
        print("❌ Une erreur s'est produite :", e)


def check_send_new_emails(offusc_conf_agent):
    agent, domain, _, _  = offuscation_basique.lire_config(offusc_conf_agent)
    chemin_dossier_in, chemin_dossier_out = mail_in_folder(agent, "out")
    if os.path.exists(chemin_dossier_out) and os.path.isdir(chemin_dossier_out):
        contenus = os.listdir(chemin_dossier_out)
        if contenus:
            for contenu in contenus:
                if os.path.exists(chemin_dossier_out + "/" + contenu + "/mail.ok"):
                    chemin = chemin_dossier_out + "/" + contenu + "/mail.txt"
                    infos = lire_message(chemin)
                    # Affichage des informations extraites
                    cles_requises = ["eme", "des", "cop", "pri", "tit", "txt"]
                    if all(cle in infos for cle in cles_requises):
                        send_mail(
                            agent+domain,
                            offusc_conf_agent,
                            infos["eme"],
                            infos["tit"],
                            infos["txt"],
                            piece_jointe_path=None  #à rajouter quand PJ ok chemin_dossier_out + "/" + contenu + "/pj"
                        )
                        MetManagement.reset_folder(chemin_dossier_in + contenu , recreate=False)
                        MetManagement.reset_folder(chemin_dossier_out + contenu, recreate=False)
                    else:
                        print("il manque des clefs dans le contenu du mail")
        else:
            print("Le dossier est vide.")
    else:
        print("Le dossier n'existe pas ou le chemin n'est pas un dossier.")


if __name__ == "__main__":
    offusc_conf_agent="agent.ia_at_institut-ia.com.json"
    while True:
        check_new_emails(offusc_conf_agent)
        time.sleep(1)
        check_send_new_emails(offusc_conf_agent)
        time.sleep(1)
    # print(f"Surveillance des mails toutes les {INTERVAL_SECONDS} secondes. Ctrl+C pour arrêter.")
    # send_mail(
    #     expediteur=EMAIL,
    #     mot_de_passe=PASSWORD,
    #     destinataire="jc@institut-ia.com",
    #     sujet="Test depuis Python",
    #     contenu="Bonjour,\nVoici un test d'envoi de mail avec Python 2.",
    #     piece_jointe_path=r""#C:\Users\max83\Desktop\Orange_4All_AAIT\Orange_4All_AAIT\Orange\Lib\site-packages\Orange\widgets\orangecontrib\HLIT_dev\widgets\icons\input_interface.png"  # ou "chemin/vers/fichier.pdf"
    # )
