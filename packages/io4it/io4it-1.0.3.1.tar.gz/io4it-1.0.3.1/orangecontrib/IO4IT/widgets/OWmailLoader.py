import os
import sys
from Orange.data import Domain, StringVariable, Table
import Orange.data
from AnyQt.QtWidgets import QApplication
from Orange.widgets import widget
from Orange.widgets.utils.signals import Input, Output
import re

if "site-packages/Orange/widgets" in os.path.dirname(os.path.abspath(__file__)).replace("\\", "/"):
    from Orange.widgets.orangecontrib.AAIT.utils.import_uic import uic
    from Orange.widgets.orangecontrib.AAIT.utils.initialize_from_ini import apply_modification_from_python_file
else:
    from orangecontrib.AAIT.utils.import_uic import uic
    from orangecontrib.AAIT.utils.initialize_from_ini import apply_modification_from_python_file




equivalence = {
    "who": "Mailbox",
    "eme": "Sender",
    "des": "Receiver",
    "cop": "Copy",
    "pri": "Priority",
    "tit": "Title",
    "txt": "content"
}


@apply_modification_from_python_file(filepath_original_widget=__file__)
class OWMailLoader(widget.OWWidget):
    name = "OWMailLoader"
    description = "Load a mail from AAIT format"
    icon = "icons/mail_loader.png"
    if "site-packages/Orange/widgets" in os.path.dirname(os.path.abspath(__file__)).replace("\\", "/"):
       icon = "icons_dev/mail_loader.png"
    gui = os.path.join(os.path.dirname(os.path.abspath(__file__)), "designer/owmailloader.ui")
    want_control_area = False
    priority = 9999

    class Inputs:
        data = Input("Data", Orange.data.Table)

    class Outputs:
        data = Output("Data", Orange.data.Table)
        data_out_nothing_to_do = Output("Data Out Nothing to Do", Orange.data.Table)

    @Inputs.data
    def set_data(self, in_data):
        self.valid_folders=[]
        input_dir_path=""
        self.error("")
        if in_data is None:
            return
        if not "input_dir" in in_data.domain:
            self.error("need input_dir in input data domain" )
            return
        if len(in_data)!=1:
            self.error("in data need to be exactly 1 line" )
            return
        input_dir_path=str(in_data[0]["input_dir"].value)
        input_dir_path.replace ("\\","/")

        self.valid_folders=self.get_valid_folders(input_dir_path)
        if len(self.valid_folders)==0:
            self.send_nothing_to_do()
            return
        print( self.valid_folders)
        self.run()


    def __init__(self):
        super().__init__()
        # Qt Management
        self.valid_folders=[]
        self.can_run = True
        self.setFixedWidth(700)
        self.setFixedHeight(500)
        uic.loadUi(self.gui, self)

        # # Data Management
        self.thread = None

        # Custom updates
        self.post_initialized()


    def get_valid_folders(self,input_dir_path):
        in_dir = input_dir_path

        # Étape 1 : Vérifier si le dossier existe
        if not os.path.isdir(in_dir):
            print(f"Dossier introuvable : {in_dir}")
            return []  # ou `return` selon ton besoin

        # Étape 2 : Parcourir les sous-dossiers
        valid_folders = []
        for name in os.listdir(in_dir):
            full_path = os.path.join(in_dir, name)
            if os.path.isdir(full_path):
                mail_ok_path = os.path.join(full_path, "mail.ok")
                if os.path.isfile(mail_ok_path):
                    valid_folders.append(full_path.replace("\\","/"))

        return valid_folders

    def send_nothing_to_do(self):
        # Définir une variable texte comme méta-attribut
        text_meta = StringVariable("nothing to do")

        # Créer un domaine sans variables principales, avec une méta
        domain = Domain([], metas=[text_meta])

        # Créer la table avec Table.from_list
        data_table = Table.from_list(domain, [["nothing"]])
        self.Outputs.data_out_nothing_to_do.send(data_table)

    def lire_fichier_txt_mail_and_parse(self,nom_du_fichier):
        try:
            # vba enregistre en ansi
            with open(nom_du_fichier, 'r', encoding='cp1252') as fichier:
                texte = fichier.read()
        except FileNotFoundError:
            print(f"Le fichier '{nom_du_fichier}' n'a pas été trouvé.")
            return None
        except Exception as e:
            print(f"Une erreur s'est produite : {e}")
            return None

        # Utilisation d'une expression régulière pour trouver toutes les lignes commençant par '#$'
        pattern = r'^\#\$(.+?) : (.*)$'

        # Recherche de tous les matches dans le texte, en utilisant un flag MULTILINE
        matches = re.findall(pattern, texte, re.MULTILINE)

        # Création d'un dictionnaire pour stocker les résultats
        resultats = {}

        for cle, valeur in matches:
            resultats[cle] = valeur

        return resultats


    # def run(self):
    #     rows = []
    #     for folder in self.valid_folders:
    #         mail_path = os.path.join(folder, "mail.txt")
    #         with open(mail_path, 'r', encoding='cp1252') as f:
    #             content = f.read()
    #         pj_folder = os.path.join(folder, "pj")
    #         rows.append([mail_path, content, pj_folder])
    #
    #     var_folder = StringVariable("Mail - path")
    #     var_content = StringVariable("Mail - content")
    #     var_attachments = StringVariable("Attachments path")
    #     domain = Domain([], metas=[var_folder, var_content, var_attachments])
    #     out_data = Table.from_list(domain=domain, rows=rows)
    #
    #     self.Outputs.data.send(out_data)


    def run(self):
        # Définir les variables de texte
        var_mail_path = StringVariable("Mail path")
        var_pj_path = StringVariable("Attachments")

        # Définir le domaine avec deux colonnes texte
        # domain = Domain([], metas=[var_mail_path, var_pj_path])

        # Construire les lignes de données
        rows = []
        for idx,folder in enumerate(self.valid_folders):
            # Chemin vers mail.txt
            mail_path = os.path.join(folder, "mail.txt").replace("\\", "/")
            pj_path = os.path.join(folder, "pj").replace("\\", "/")

            # Lecture du contenu du mail
            detail = self.lire_fichier_txt_mail_and_parse(mail_path)
            renamed = {equivalence.get(k, k): v for k, v in detail.items()}
            if detail is None:
                self.error("error reading " + mail_path)
                return

            # Ajout des éléments à la row
            row = [mail_path, pj_path] + list(renamed.values())
            rows.append(row)

        # On utilise detail du dernier mail analysé, qui devrait être le même pour tous mails
        new_metas = [var_mail_path, var_pj_path] + [Orange.data.StringVariable(key) for key in list(renamed.keys())]
        dom = Orange.data.Domain([], [], metas=new_metas)
        out_data = Table.from_list(domain=dom, rows=rows)

        self.Outputs.data.send(out_data)


    def post_initialized(self):
        pass

if __name__ == "__main__":
    app = QApplication(sys.argv)
    data = Orange.data.Table(r"C:\Users\lucas\Downloads\input.tab")
    my_widget = OWMailLoader()
    my_widget.show()
    my_widget.set_data(data)
    app.exec_()
