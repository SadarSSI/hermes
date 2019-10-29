import datetime

from hermes_ui.adminlte.models import User
from hermes_ui.models.detecteur import Detecteur
from hermes_ui.db import db
from copy import deepcopy
from collections import OrderedDict


class Automate(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    designation = db.Column(db.String(255), nullable=False, unique=True)

    production = db.Column(db.Boolean(), nullable=False, default=False)
    notifiable = db.Column(db.Boolean(), nullable=False, default=True)

    priorite = db.Column(db.Integer(), nullable=False, default=0)

    createur_id = db.Column(db.ForeignKey('user.id'), nullable=True)
    createur = db.relationship(User, primaryjoin="User.id==Automate.createur_id")

    date_creation = db.Column(db.DateTime(timezone=True), nullable=False, default=datetime.datetime.utcnow())
    date_modification = db.Column(db.DateTime(timezone=True), nullable=False, default=datetime.datetime.utcnow())

    responsable_derniere_modification_id = db.Column(db.ForeignKey('user.id'), nullable=True)
    responsable_derniere_modification = db.relationship(User,
                                                        primaryjoin="User.id==Automate.responsable_derniere_modification_id")

    detecteur_id = db.Column(db.Integer(), db.ForeignKey(Detecteur.id), nullable=False)
    detecteur = db.relationship(Detecteur, foreign_keys="Automate.detecteur_id", lazy='joined', backref='automates', cascade="save-update")

    actions = db.relationship('ActionNoeud', primaryjoin='ActionNoeud.automate_id==Automate.id', lazy='joined', enable_typechecks=False)

    action_racine_id = db.Column(db.Integer(), db.ForeignKey('action_noeud.id'), nullable=True)
    action_racine = db.relation('ActionNoeud', foreign_keys='Automate.action_racine_id', lazy='joined', enable_typechecks=False, cascade="save-update, merge, delete")


class ActionNoeud(db.Model):
    DESCRIPTION = None
    PARAMETRES = OrderedDict({
        'designation': {
            'format': 'TEXT',
            'required': True,
            'help': 'Une courte explication de ce que votre action va réaliser'
        },
        'friendly_name': {
            'format': 'TEXT',
            'required': False,
            'help': 'Un nom simple (de variable) sans espace pour réutiliser le résultat de votre action si il y a lieu'
        }
    })

    id = db.Column(db.Integer(), primary_key=True, autoincrement=True)

    automate_id = db.Column(db.Integer(), db.ForeignKey('automate.id'), nullable=False)
    # automate = db.relation(Automate, back_populates="actions", foreign_keys="ActionNoeud.automate_id", lazy='noload')

    designation = db.Column(db.String(255), nullable=False)

    createur_id = db.Column(db.ForeignKey('user.id'), nullable=True)
    createur = db.relationship(User, primaryjoin="User.id==ActionNoeud.createur_id")

    date_creation = db.Column(db.DateTime(timezone=True), nullable=False, default=datetime.datetime.utcnow())
    date_modification = db.Column(db.DateTime(timezone=True), nullable=False, default=datetime.datetime.utcnow())

    responsable_derniere_modification_id = db.Column(db.ForeignKey('user.id'), nullable=True)
    responsable_derniere_modification = db.relationship(User,
                                                        primaryjoin="User.id==ActionNoeud.responsable_derniere_modification_id")

    action_reussite_id = db.Column(db.Integer(), db.ForeignKey('action_noeud.id'), nullable=True)
    action_reussite = db.relationship('ActionNoeud', foreign_keys='ActionNoeud.action_reussite_id', lazy='joined', uselist=False, enable_typechecks=False, cascade="save-update, merge, delete")

    action_echec_id = db.Column(db.Integer(), db.ForeignKey('action_noeud.id'), nullable=True)
    action_echec = db.relation('ActionNoeud', foreign_keys='ActionNoeud.action_echec_id', lazy='joined', uselist=False, enable_typechecks=False, cascade="save-update, merge, delete")

    mapped_class_child = db.Column(db.String(128), nullable=True)

    friendly_name = db.Column(db.String(), nullable=True)

    __mapper_args__ = {'polymorphic_on': mapped_class_child}

    def transcription(self):
        raise NotImplemented

    @staticmethod
    def descriptifs(ma_classe=None, ancetres_parametres=None):
        """

        :param type ma_classe:
        :param dict ancetres_parametres:
        :return:
        """
        ma_liste_descriptif = list()

        if ma_classe is not None and isinstance(ma_classe, type) is False:
            return ma_liste_descriptif
        if ma_classe is None and ancetres_parametres is None:
            ancetres_parametres = deepcopy(getattr(ActionNoeud, 'PARAMETRES'))

        for my_class in ma_classe.__subclasses__() if ma_classe is not None else ActionNoeud.__subclasses__():

            parametres = deepcopy(getattr(my_class, 'PARAMETRES'))  # type: dict
            parametres.update(ancetres_parametres)

            if len(my_class.__subclasses__()) == 0:

                ma_liste_descriptif.append(
                    {
                        'type': str(my_class),
                        'description': getattr(my_class, 'DESCRIPTION'),
                        'formulaire': parametres
                    }
                )
            else:
                ma_liste_descriptif += ActionNoeud.descriptifs(my_class, ancetres_parametres=parametres)
        return ma_liste_descriptif


class RequeteSqlActionNoeud(ActionNoeud):
    DESCRIPTION = 'Effectuer une requête de type SQL sur un serveur SGDB tel que ' \
                  'Oracle, MySQL, PosgreSQL, Microsoft SQL Serveur et MariaDB'
    PARAMETRES = OrderedDict({
        'hote_type_protocol': {
            'format': 'SELECT',
            'required': True,
            'help': 'Type de serveur SGDB distant',
            'choix': ['mysql', 'mariadb', 'posgres', 'mssql', 'oracle']
        },
        'hote_ipv4': {
            'format': 'TEXT',
            'required': True,
            'help': 'Adresse IPv4 xxx.xxx.xxx.xxx de votre serveur SGDB',
        },
        'hote_port': {
            'format': 'NUMBER',
            'required': True,
            'help': 'Port TCP à utiliser pour se connecter à votre serveur, '
                    'eg. 3306 pour MySQL, MariaDB; 5432 pour PosgreSQL; 1521 pour Oracle; etc..',
        },
        'hote_database': {
            'format': 'TEXT',
            'required': True,
            'help': 'Nom de votre base de données sur laquelle sera executée la requête SQL',
        },
        'requete_sql': {
            'format': 'TEXTAREA',
            'required': True,
            'help': 'Requête SQL à lancer sur votre serveur, l\'usage des variables {{ ma_variable }} '
                    'est autorisée dans la clause WHERE. Elles seront insérées de manière sécurisée. '
                    'eg. "SELECT * FROM Product WHERE name = {{ nom_produit }} LIMIT 5"',
        },
        'nom_utilisateur': {
            'format': 'TEXT',
            'required': False,
            'help': 'Saisir le nom d\'utilisateur pour la connexion si nécessaire',
        },
        'mot_de_passe': {
            'format': 'TEXT',
            'required': False,
            'help': 'Saisir le mot de passe associé à l\'utilisateur pour la connexion si nécessaire',
        },
    })

    __tablename__ = 'requete_sql_action_noeud'

    id = db.Column(db.Integer, db.ForeignKey('action_noeud.id'), primary_key=True)

    hote_type_protocol = db.Column(db.Enum('mysql', 'posgres', 'mariadb', 'mssql', 'oracle'), nullable=False)
    hote_ipv4 = db.Column(db.String(), nullable=False)
    hote_port = db.Column(db.String(), nullable=False)
    hote_database = db.Column(db.String(), nullable=False)

    requete_sql = db.Column(db.Text(), nullable=False)

    nom_utilisateur = db.Column(db.String(), nullable=True)
    mot_de_passe = db.Column(db.String(), nullable=True)

    __mapper_args__ = {
        'polymorphic_identity': str(ActionNoeud).replace('ActionNoeud', 'RequeteSqlActionNoeud'),
    }

    def transcription(self):
        """
        :rtype: gie_interoperabilite.automate.RequeteSqlActionNoeud
        """
        from hermes.automate import RequeteSqlActionNoeud as Action
        return Action(
            self.designation,
            self.hote_type_protocol,
            self.hote_ipv4,
            self.hote_port,
            self.hote_database,
            self.requete_sql,
            self.nom_utilisateur,
            self.mot_de_passe,
            self.friendly_name
        )


class RequeteSoapActionNoeud(ActionNoeud):
    DESCRIPTION = 'Effectuer une requête de type SOAP Webservice'
    PARAMETRES = OrderedDict({
        'url_service': {
            'format': 'TEXT',
            'required': True,
            'help': 'URL du service WDSL cible sur lequel le webservice SOAP est actif'
        },
        'methode_cible': {
            'format': 'TEXT',
            'required': True,
            'help': 'Choix de la méthode (fonction) à utiliser, la documentation du webservice doit vous le fournir',
        },
        'form_data': {
            'format': 'JSON',
            'required': False,
            'help': 'La structure de données à fournir au webservice, il est possible que celle-ci soit vide',
        },
        'authentification_basique_utilisateur': {
            'format': 'TEXT',
            'required': False,
            'help': 'Nom utilisateur à utiliser pour une éventuelle authentification',
        },
        'authentification_basique_mot_de_passe': {
            'format': 'TEXT',
            'required': False,
            'help': 'Mot de passe associé à utiliser pour une éventuelle authentification',
        },
        'proxy_http': {
            'format': 'TEXT',
            'required': False,
            'help': 'Adresse de votre proxy pour les requêtes HTTP non sécurisée',
        },
        'proxy_https': {
            'format': 'TEXT',
            'required': False,
            'help': 'Adresse de votre proxy pour les requêtes HTTPS sécurisée',
        },
    })

    __tablename__ = 'requete_soap_action_noeud'

    id = db.Column(db.Integer, db.ForeignKey('action_noeud.id'), primary_key=True)

    url_service = db.Column(db.String(), nullable=False)
    methode_cible = db.Column(db.String(), nullable=False)
    form_data = db.Column(db.Text(), nullable=False)

    authentification_basique_utilisateur = db.Column(db.String(), nullable=True)
    authentification_basique_mot_de_passe = db.Column(db.String(), nullable=True)

    proxy_http = db.Column(db.String(), nullable=True)
    proxy_https = db.Column(db.String(), nullable=True)

    __mapper_args__ = {
        'polymorphic_identity': str(ActionNoeud).replace('ActionNoeud', 'RequeteSoapActionNoeud'),
    }

    def transcription(self):
        """
        :rtype: gie_interoperabilite.automate.RequeteSoapActionNoeud
        """
        from hermes.automate import RequeteSoapActionNoeud as Action
        from json import loads
        return Action(
            self.designation,
            self.url_service,
            self.methode_cible,
            loads(self.form_data) if self.form_data is not None and len(self.form_data) >= 1 else {},
            (
                self.authentification_basique_utilisateur,
                self.authentification_basique_mot_de_passe
            ) if self.authentification_basique_utilisateur is not None else None,
            {
                'http': self.proxy_http,
                'https': self.proxy_https
            } if self.proxy_http is not None else None,
            self.friendly_name
        )


class RequeteHttpActionNoeud(ActionNoeud):
    DESCRIPTION = 'Effectuer une requête de type HTTP sur un serveur distant'
    PARAMETRES = OrderedDict({
        'url_dest': {
            'format': 'TEXT',
            'required': True,
            'help': 'Adresse URL du serveur HTTP distant sur laquelle la requête sera lancée'
        },
        'methode_http': {
            'format': 'SELECT',
            'required': True,
            'help': 'La méthode (ou verbe) HTTP à utiliser avec la requête, cette information peut être disponible dans votre documentation du service distant',
            'choix': ['GET', 'POST', 'PUT', 'DELETE', 'PATCH']
        },
        'form_data': {
            'format': 'JSON',
            'required': False,
            'help': 'Les données à transmettre dans votre requête HTTP',
        },
        'authentification_basique_utilisateur': {
            'format': 'TEXT',
            'required': False,
            'help': 'Si une authentification est nécessaire par le billet d\'une authentification basique, précisez le nom utilisateur',
        },
        'authentification_basique_mot_de_passe': {
            'format': 'TEXT',
            'required': False,
            'help': 'Si une authentification est nécessaire par le billet d\'une authentification basique, précisez le mot de passe',
        },
        'proxy_http': {
            'format': 'TEXT',
            'required': False,
            'help': 'Si votre requête doit utiliser un proxy pour les requêtes non sécurisées, précisez l\'adresse de votre serveur mandataire HTTP',
        },
        'proxy_https': {
            'format': 'TEXT',
            'required': False,
            'help': 'Si votre requête doit utiliser un proxy pour les requêtes sécurisées, précisez l\'adresse de votre serveur mandataire HTTP',
        },
        'resp_code_http': {
            'format': 'NUMBER',
            'required': False,
            'help': 'Si vous attendez un code de retour HTTP spécifique pour vérifier que la requête à réussi, précisez-le',
        },
        'verify_peer': {
            'format': 'CHECKBOX',
            'required': False,
            'help': 'Cochez cette case pour activer la vérification TLS distante, dans le doute laissez cette case cochée',
        }
    })

    __tablename__ = 'requete_http_action_noeud'

    id = db.Column(db.Integer, db.ForeignKey('action_noeud.id'), primary_key=True)

    url_dest = db.Column(db.String(), nullable=False)
    methode_http = db.Column(db.Enum('GET', 'POST', 'DELETE', 'PATCH', 'DELETE'), nullable=False)
    form_data = db.Column(db.Text(), nullable=False)

    authentification_basique_utilisateur = db.Column(db.String(), nullable=True)
    authentification_basique_mot_de_passe = db.Column(db.String(), nullable=True)

    proxy_http = db.Column(db.String(), nullable=True)
    proxy_https = db.Column(db.String(), nullable=True)

    resp_code_http = db.Column(db.Integer(), nullable=True)
    verify_peer = db.Column(db.Boolean, nullable=False, default=True)

    __mapper_args__ = {
        'polymorphic_identity': str(ActionNoeud).replace('ActionNoeud', 'RequeteHttpActionNoeud'),
    }

    def transcription(self):
        """
        :rtype: gie_interoperabilite.automate.RequeteHttpActionNoeud
        """
        from hermes.automate import RequeteHttpActionNoeud as ACTION
        from json import loads
        return ACTION(
            self.designation,
            self.url_dest,
            self.methode_http,
            loads(self.form_data) if self.form_data is not None and len(self.form_data) >= 1 else {},
            (
                self.authentification_basique_utilisateur,
                self.authentification_basique_mot_de_passe
            ) if self.authentification_basique_utilisateur is not None else None,
            {
                'http': self.proxy_http,
                'https': self.proxy_https
            } if self.proxy_http is not None else None,
            self.resp_code_http,
            self.verify_peer,
            self.friendly_name
        )


class EnvoyerMessageSmtpActionNoeud(ActionNoeud):
    DESCRIPTION = 'Ecrire un message électronique vers n-tiers via un serveur SMTP'
    PARAMETRES = OrderedDict({
        'destinataire': {
            'format': 'TEXT',
            'required': True,
            'help': "L'adresse email du destinataire, en cas de multiple destinataire, "
                    "veuillez les séparer par une virgule."
        },
        'sujet': {
            'format': 'TEXT',
            'required': True,
            'help': 'Le sujet de votre email transféré'
        },
        'corps': {
            'format': 'TEXTAREA',
            'required': True,
            'help': 'Le corps de votre message électronique, format HTML supporté'
        },
        'hote_smtp': {
            'format': 'TEXT',
            'required': True,
            'help': 'Votre serveur SMTP par lequel votre message transitera'
        },
        'port_smtp': {
            'format': 'NUMBER',
            'required': True,
            'help': 'Le port de votre serveur SMTP à utiliser, '
                    'soit 587 (le plus courant) ou le port 25 à titre d\'exemple'
        },
        'nom_utilisateur': {
            'format': 'TEXT',
            'required': False,
            'help': 'Le nom d\'utilisateur à utiliser avec le serveur SMTP si il y a lieu',
        },
        'mot_de_passe': {
            'format': 'TEXT',
            'required': False,
            'help': 'Le mot de passe à utiliser avec le serveur SMTP si il y a lieu',
        },
        'enable_tls': {
            'format': 'CHECKBOX',
            'required': False,
            'help': 'Cochez cette case pour utiliser la connexion via un port sécurisé, '
                    'dans le doute laissez cette case cochée',
        },
        'pj_source': {
            'format': 'CHECKBOX',
            'required': False,
            'help': 'Cochez cette case pour transférer le message source en pièce jointe si la source le permet',
        },
    })

    __tablename__ = 'envoyer_message_smtp_action_noeud'

    id = db.Column(db.Integer, db.ForeignKey('action_noeud.id'), primary_key=True)

    destinataire = db.Column(db.String(), nullable=False)
    sujet = db.Column(db.String(), nullable=False)
    corps = db.Column(db.Text(), nullable=False)
    hote_smtp = db.Column(db.String(), nullable=False)
    port_smtp = db.Column(db.Integer(), nullable=False)
    nom_utilisateur = db.Column(db.String(), nullable=True)
    mot_de_passe = db.Column(db.String(), nullable=True)
    enable_tls = db.Column(db.Boolean(), nullable=False, default=True)
    pj_source = db.Column(db.Boolean(), nullable=False, default=True)

    __mapper_args__ = {
        'polymorphic_identity': str(ActionNoeud).replace('ActionNoeud', 'EnvoyerMessageSmtpActionNoeud'),
    }

    def transcription(self):
        """
        :rtype: gie_interoperabilite.automate.EnvoyerMessageSmtpActionNoeud
        """
        from hermes.automate import EnvoyerMessageSmtpActionNoeud as ACTION
        return ACTION(
            self.designation,
            self.destinataire,
            self.sujet,
            self.corps,
            self.hote_smtp,
            self.port_smtp,
            self.nom_utilisateur,
            self.mot_de_passe,
            self.enable_tls,
            self.pj_source
        )


class TransfertSmtpActionNoeud(ActionNoeud):
    DESCRIPTION = 'Transferer un message électronique vers n-tiers via un serveur SMTP'
    PARAMETRES = OrderedDict({
        'destinataire': {
            'format': 'TEXT',
            'required': True,
            'help': "L'adresse email du destinaire, en cas de multiple destinataire, "
                    "veuillez les séparer par une virgule"
        },
        'sujet': {
            'format': 'TEXT',
            'required': True,
            'help': 'Le sujet de votre email transféré'
        },
        'hote_smtp': {
            'format': 'TEXT',
            'required': True,
            'help': 'Votre serveur SMTP par lequel votre message transitera'
        },
        'port_smtp': {
            'format': 'NUMBER',
            'required': True,
            'help': 'Le port de votre serveur SMTP à utiliser, le plus fréquent 587 ou 25'
        },
        'nom_utilisateur': {
            'format': 'TEXT',
            'required': False,
            'help': 'Le nom d\'utilisateur à utiliser avec le serveur SMTP si il y a lieu',
        },
        'mot_de_passe': {
            'format': 'TEXT',
            'required': False,
            'help': 'Le mot de passe à utiliser avec le serveur SMTP si il y a lieu',
        },
        'enable_tls': {
            'format': 'CHECKBOX',
            'required': False,
            'help': 'Cochez cette case pour utiliser la connexion SMTP via un port sécurisé, '
                    'dans le doute laissez cette case cochée',
        },
    })

    __tablename__ = 'transfert_smtp_action_noeud'

    id = db.Column(db.Integer, db.ForeignKey('action_noeud.id'), primary_key=True)

    destinataire = db.Column(db.String(), nullable=False)
    sujet = db.Column(db.String(), nullable=False)
    hote_smtp = db.Column(db.String(), nullable=False)
    port_smtp = db.Column(db.Integer(), nullable=False)
    nom_utilisateur = db.Column(db.String(), nullable=True)
    mot_de_passe = db.Column(db.String(), nullable=True)
    enable_tls = db.Column(db.Boolean(), nullable=False, default=True)

    __mapper_args__ = {
        'polymorphic_identity': str(ActionNoeud).replace('ActionNoeud', 'TransfertSmtpActionNoeud'),
    }

    def transcription(self):
        """
        :rtype: gie_interoperabilite.automate.EnvoyerMessageSmtpActionNoeud
        """
        from hermes.automate import TransfertSmtpActionNoeud as ACTION
        return ACTION(
            self.designation,
            self.destinataire,
            self.sujet,
            self.hote_smtp,
            self.port_smtp,
            self.nom_utilisateur,
            self.mot_de_passe,
            self.enable_tls
        )


class ConstructionInteretActionNoeud(ActionNoeud):
    DESCRIPTION = "Construire une variable intermédiaire"
    PARAMETRES = OrderedDict({
        'interet': {
            'format': 'JSON',
            'required': True,
            'help': 'Contruire votre objet variable intermédiaire'
        },
    })

    __tablename__ = 'construction_interet_action_noeud'

    id = db.Column(db.Integer, db.ForeignKey('action_noeud.id'), primary_key=True)

    interet = db.Column(db.Text(), nullable=False)

    __mapper_args__ = {
        'polymorphic_identity': str(ActionNoeud).replace('ActionNoeud', 'ConstructionInteretActionNoeud'),
    }

    def transcription(self):
        """
        :rtype: gie_interoperabilite.automate.ConstructionInteretActionNoeud
        """
        from hermes.automate import ConstructionInteretActionNoeud as ACTION
        from json import loads
        return ACTION(
            self.designation,
            loads(self.interet),
            self.friendly_name
        )


class ConstructionChaineCaractereSurListeActionNoeud(ActionNoeud):
    DESCRIPTION = "Fabriquer une chaîne de caractère à partir d'une liste identifiable"
    PARAMETRES = OrderedDict({
        'variable_pattern': {
            'format': 'TEXT',
            'required': True,
            'help': 'Votre variable contenant au moins une liste identifiable tel que {{ ma_variable.0.adresse }}'
        },
        'separateur': {
            'format': 'TEXT',
            'required': True,
            'help': 'Le séparateur à mettre pendant la phase de collage'
        },
    })

    __tablename__ = 'construction_chaine_caractere_sur_liste_action_noeud'

    id = db.Column(db.Integer, db.ForeignKey('action_noeud.id'), primary_key=True)

    variable_pattern = db.Column(db.String(), nullable=False)
    separateur = db.Column(db.String(), nullable=False)

    __mapper_args__ = {
        'polymorphic_identity': str(ActionNoeud).replace('ActionNoeud', 'ConstructionChaineCaractereSurListeActionNoeud'),
    }

    def transcription(self):
        """
        :rtype: gie_interoperabilite.automate.ConstructionChaineCaractereSurListeActionNoeud
        """
        from hermes.automate import ConstructionChaineCaractereSurListeActionNoeud as ACTION
        return ACTION(
            self.designation,
            self.variable_pattern,
            self.separateur,
            self.friendly_name
        )


class InvitationEvenementActionNoeud(ActionNoeud):
    DESCRIPTION = "Emettre ou mettre à jour une invitation à un évenement par message electronique"
    PARAMETRES = OrderedDict({
        'organisateur': {
            'format': 'TEXT',
            'required': True,
            'help': 'Précisez-nous qui est à l\'origine de cette invitation, nom ou adresse de messagerie'
        },
        'participants': {
            'format': 'TEXT',
            'required': True,
            'help': "Une liste d'adresse de messagerie séparées par une virgule, "
                    "peut être précédemment construit par une autre action"
        },
        'sujet': {
            'format': 'TEXT',
            'required': True,
            'help': "En bref, le sujet au coeur de votre invitation"
        },
        'description': {
            'format': 'TEXTAREA',
            'required': True,
            'help': 'Décrivez-nous en détails votre invitation, les enjeux, les prérequis, etc.. (!HTML non supporté!)'
        },
        'lieu': {
            'format': 'TEXT',
            'required': True,
            'help': 'Le lieu où l\'invitation aura lieu'
        },
        'date_heure_depart': {
            'format': 'TEXT',
            'required': True,
            'help': "La date et heure de début de l'évenement, "
                    "doit être facilement lisible pour un robot, format français ou anglais. "
                    "eg. '15/01/2019 15:22 GMT+02'"
        },
        'date_heure_fin': {
            'format': 'TEXT',
            'required': True,
            'help': "La date et heure de fin de l'évenement, "
                    "doit être facilement lisible pour un robot, format français ou anglais. "
                    "eg. '20/01/2019 15:22 GMT+02'"
        },
        'est_maintenu': {
            'format': 'CHECKBOX',
            'required': False,
            'help': "Cochez-le si l'évenement doit être maintenu"
        },

        'hote_smtp': {
            'format': 'TEXT',
            'required': True,
            'help': 'Votre serveur SMTP par lequel votre message transitera'
        },
        'port_smtp': {
            'format': 'NUMBER',
            'required': True,
            'help': 'Le port de votre serveur SMTP à utiliser, le plus fréquent 587 ou 25'
        },
        'nom_utilisateur': {
            'format': 'TEXT',
            'required': False,
            'help': 'Le nom d\'utilisateur à utiliser avec le serveur SMTP si il y a lieu',
        },
        'mot_de_passe': {
            'format': 'TEXT',
            'required': False,
            'help': 'Le mot de passe à utiliser avec le serveur SMTP si il y a lieu',
        },
        'enable_tls': {
            'format': 'CHECKBOX',
            'required': False,
            'help': 'Cochez cette case pour utiliser la connexion SMTP via un port sécurisé, '
                    'dans le doute laissez cette case cochée',
        },
    })

    __tablename__ = 'invitation_evenement_action_noeud'

    id = db.Column(db.Integer, db.ForeignKey('action_noeud.id'), primary_key=True)

    organisateur = db.Column(db.String(), nullable=False)
    participants = db.Column(db.String(), nullable=False)
    sujet = db.Column(db.String(), nullable=False)
    description = db.Column(db.Text(), nullable=False)
    lieu = db.Column(db.String(), nullable=False)
    date_heure_depart = db.Column(db.Text(), nullable=False)
    date_heure_fin = db.Column(db.Text(), nullable=False)
    est_maintenu = db.Column(db.Boolean(), nullable=False, default=True)

    hote_smtp = db.Column(db.String(), nullable=False)
    port_smtp = db.Column(db.String(), nullable=False)
    nom_utilisateur = db.Column(db.String(), nullable=False)
    mot_de_passe = db.Column(db.String(), nullable=False)
    enable_tls = db.Column(db.Boolean(), nullable=False, default=True)

    __mapper_args__ = {
        'polymorphic_identity': str(ActionNoeud).replace('ActionNoeud', 'InvitationEvenementActionNoeud'),
    }

    def transcription(self):
        """
        :rtype: gie_interoperabilite.automate.InvitationEvenementActionNoeud
        """
        from hermes.automate import InvitationEvenementActionNoeud as Action
        return Action(
            self.designation,
            self.organisateur,
            self.participants,
            self.sujet,
            self.description,
            self.lieu,
            self.date_heure_depart,
            self.date_heure_fin,
            self.est_maintenu,
            self.hote_smtp,
            self.port_smtp,
            self.nom_utilisateur,
            self.mot_de_passe,
            self.enable_tls,
            self.friendly_name
        )


class VerifierSiVariableVraiActionNoeud(ActionNoeud):
    DESCRIPTION = "Vérifie si une variable est Vrai"
    PARAMETRES = OrderedDict({
        'variable_cible': {
            'format': 'TEXT',
            'required': True,
            'help': 'Nom de votre variable à tester à Vrai, vous pouvez utiliser le format {{ ma_varible }}'
        },
    })

    __tablename__ = 'verifier_si_variable_vrai_action_noeud'

    id = db.Column(db.Integer, db.ForeignKey('action_noeud.id'), primary_key=True)

    variable_cible = db.Column(db.String(), nullable=False)

    __mapper_args__ = {
        'polymorphic_identity': str(ActionNoeud).replace('ActionNoeud', 'VerifierSiVariableVraiActionNoeud'),
    }

    def transcription(self):
        """
        :rtype: gie_interoperabilite.automate.VerifierSiVariableVraiActionNoeud
        """
        from hermes.automate import VerifierSiVariableVraiActionNoeud as Action
        return Action(
            self.designation,
            self.variable_cible,
            self.friendly_name
        )


class ComparaisonVariableActionNoeud(ActionNoeud):
    DESCRIPTION = "Effectue une comparaison entre deux variables de votre choix, nombres, dates, etc.."
    PARAMETRES = OrderedDict({
        'membre_gauche_variable': {
            'format': 'TEXT',
            'required': True,
            'help': 'Membre de gauche de notre comparaison, vous pouvez utiliser le format {{ ma_varible }}'
        },
        'operande': {
            'format': 'SELECT',
            'required': True,
            'help': "Type d'opérateur à utiliser dans le cadre de notre comparaison",
            'choix': ['==', '>', '<', '>=', '<=', '!=']
        },
        'membre_droite_variable': {
            'format': 'TEXT',
            'required': True,
            'help': 'Membre de gauche de notre comparaison, vous pouvez utiliser le format {{ ma_varible }}'
        },
    })

    __tablename__ = 'comparaison_variable_action_noeud'

    id = db.Column(db.Integer, db.ForeignKey('action_noeud.id'), primary_key=True)

    membre_gauche_variable = db.Column(db.String(), nullable=False)
    operande = db.Column(db.Enum('==', '>', '<', '>=', '<=', '!='), nullable=False)
    membre_droite_variable = db.Column(db.String(), nullable=False)

    __mapper_args__ = {
        'polymorphic_identity': str(ActionNoeud).replace('ActionNoeud', 'ComparaisonVariableActionNoeud'),
    }

    def transcription(self):
        """
        :rtype: gie_interoperabilite.automate.ComparaisonVariableActionNoeud
        """
        from hermes.automate import ComparaisonVariableActionNoeud as Action
        return Action(
            self.designation,
            self.membre_gauche_variable,
            self.operande,
            self.membre_droite_variable,
            self.friendly_name
        )


class DeplacerMailSourceActionNoeud(ActionNoeud):
    DESCRIPTION = "Déplacer un message électronique sur un autre dossier"
    PARAMETRES = OrderedDict({
        'dossier_destination': {
            'format': 'TEXT',
            'required': True,
            'help': 'La destination dans lequel votre source sera déplacée'
        }
    })

    __tablename__ = 'deplacer_mail_source_action_noeud'

    id = db.Column(db.Integer, db.ForeignKey('action_noeud.id'), primary_key=True)

    dossier_destination = db.Column(db.String(), nullable=False)

    __mapper_args__ = {
        'polymorphic_identity': str(ActionNoeud).replace('ActionNoeud', 'DeplacerMailSourceActionNoeud'),
    }

    def transcription(self):
        """
        :rtype: gie_interoperabilite.automate.DeplacerMailSourceActionNoeud
        """
        from hermes.automate import DeplacerMailSourceActionNoeud as Action
        return Action(
            self.designation,
            self.dossier_destination
        )


class CopierMailSourceActionNoeud(ActionNoeud):
    DESCRIPTION = "Copier un message électronique dans un autre dossier"
    PARAMETRES = OrderedDict({
        'dossier_destination': {
            'format': 'TEXT',
            'required': True,
            'help': 'La destination dans lequel votre source sera copiée',
        },
    })

    __tablename__ = 'copier_mail_source_action_noeud'

    id = db.Column(db.Integer, db.ForeignKey('action_noeud.id'), primary_key=True)

    dossier_destination = db.Column(db.String(), nullable=False)

    __mapper_args__ = {
        'polymorphic_identity': str(ActionNoeud).replace('ActionNoeud', 'CopierMailSourceActionNoeud'),
    }

    def transcription(self):
        """
        :rtype: gie_interoperabilite.automate.CopierMailSourceActionNoeud
        """
        from hermes.automate import CopierMailSourceActionNoeud as Action
        return Action(
            self.designation,
            self.dossier_destination
        )


class SupprimerMailSourceActionNoeud(ActionNoeud):
    DESCRIPTION = "Supprime un message électronique"
    PARAMETRES = OrderedDict()

    __tablename__ = 'supprimer_mail_source_action_noeud'

    id = db.Column(db.Integer, db.ForeignKey('action_noeud.id'), primary_key=True)

    __mapper_args__ = {
        'polymorphic_identity': str(ActionNoeud).replace('ActionNoeud', 'SupprimerMailSourceActionNoeud'),
    }

    def transcription(self):
        """
        :rtype: gie_interoperabilite.automate.SupprimerMailSourceActionNoeud
        """
        from hermes.automate import SupprimerMailSourceActionNoeud as Action
        return Action(
            self.designation
        )


class TransformationListeVersDictionnaireActionNoeud(ActionNoeud):
    DESCRIPTION = "Création d'une variable intermédiaire " \
                  "sachant une liste [{'cle_a': 'val_a', 'cle_b': 'val_b'}] vers {'val_a': 'val_b'}"

    PARAMETRES = OrderedDict({
        'resultat_concerne': {
            'format': 'TEXT',
            'required': True,
            'help': 'Le nom de la variable concernée par la transformation'
        },
        'champ_cle': {
            'format': 'TEXT',
            'required': True,
            'help': 'Le nom du champ clé'
        },
        'champ_valeur': {
            'format': 'TEXT',
            'required': True,
            'help': 'Le nom du champ valeur'
        },
    })

    __tablename__ = 'transformation_liste_vers_dictionnaire_action_noeud'

    id = db.Column(db.Integer, db.ForeignKey('action_noeud.id'), primary_key=True)

    resultat_concerne = db.Column(db.String(), nullable=False)
    champ_cle = db.Column(db.String(), nullable=False)
    champ_valeur = db.Column(db.String(), nullable=False)

    __mapper_args__ = {
        'polymorphic_identity': str(ActionNoeud).replace('ActionNoeud', 'TransformationListeVersDictionnaireActionNoeud'),
    }

    def transcription(self):
        """
        :rtype: gie_interoperabilite.automate.TransformationListeVersDictionnaireActionNoeud
        """
        from hermes.automate import TransformationListeVersDictionnaireActionNoeud as Action
        return Action(
            self.designation,
            self.resultat_concerne,
            self.champ_cle,
            self.champ_valeur,
            self.friendly_name
        )