from glob import glob
from io import StringIO
import yaml
import json

from flask import url_for, redirect, jsonify, request, Response
from flask_sqlalchemy import Pagination
from marshmallow.exceptions import MarshmallowError
from werkzeug.datastructures import FileStorage

from flask_babel import Babel

from hermes import Mail
from hermes_ui.moteur.transcription import ServiceTranspositionModels
from .flask_extended import Flask
from flask_migrate import Migrate
from flask_security import Security, login_required
from flask_security.utils import hash_password
from flask_admin import helpers as admin_helpers, AdminIndexView

from json import dumps
from os.path import realpath, dirname
from sys import modules
from os.path import join, basename

from sqlalchemy.exc import NoReferencedTableError, NoSuchTableError, OperationalError, IntegrityError, SQLAlchemyError

from hermes_ui.adminlte.admin import AdminLte, admins_store
from hermes_ui.adminlte.models import *
from hermes_ui.adminlte.views import FaLink

from hermes_ui.views import *

from hermes.session import SessionFiltre
from hermes.analysis import ExtractionInteret
from hermes.logger import logger, mem_handler
from hermes_ui.moteur.processus import InstanceInteroperabilite
from hermes_ui.incident import NotificationIncident

from hermes_ui.marshmallow.legacy import *
from hermes_ui.marshmallow.front import *
from flask_webpack import Webpack


app = Flask(__name__)
app.config.from_yaml(join(app.root_path, '../configuration.yml'))
app.logger = logger

__path__ = dirname(realpath(__file__))

security = Security(app, admins_store)

babel = Babel(app)

webpack = Webpack(app)

admin = AdminLte(
    app,
    skin='purple',
    name='GIE Interopérabilité',
    short_name="<b>GIE</b><sup>SV</sup>",
    long_name="<b>GIE</b><sup>SV</sup> <small>Interopérabilité</small>",
    index_view=AdminIndexView(name="Interopérabilité", menu_icon_value='fa-pencil', menu_icon_type='fa')
)

db.init_app(app)
migrate = Migrate(app, db)
ma = Marshmallow(app)
NotificationIncident.init_app(app)

admin.add_view(
    BoiteAuxLettresImapView(
        BoiteAuxLettresImap,
        db.session,
        name="Boite aux lettres (IMAP)",
        menu_icon_value="fa-envelope",
        category="Sources de données"
    )
)

admin.add_view(
    ConfigurationView(
        Configuration,
        db.session,
        name="Mes variables globales",
        menu_icon_value="fa-cogs"
    )
)

admin.add_view(
    AutomateView(
        Automate,
        db.session,
        name="Description des Automates",
        menu_icon_value="fa-android"
    )
)

admin.add_view(
    DectecteurView(
        Detecteur,
        db.session,
        name="Détecteur",
        menu_icon_value="fa-flag"
    )
)

admin.add_view(
    IdentificateurRechercheInteretView(
        IdentificateurRechercheInteret,
        db.session,
        name="Identifiant",
        menu_icon_value="fa-sort-numeric-desc",
        category="Critères de recherche"
    )
)

admin.add_view(
    LocalisationExpressionRechercheInteretView(
        LocalisationExpressionRechercheInteret,
        db.session,
        name="Recherche d'expression",
        menu_icon_value="fa-search-plus",
        category="Critères de recherche"
    )
)

admin.add_view(
    DateRechercheInteretView(
        DateRechercheInteret,
        db.session,
        name="Date",
        menu_icon_value="fa-calendar",
        category="Critères de recherche"
    )
)

admin.add_view(
    ExpressionCleRechercheInteretView(
        ExpressionCleRechercheInteret,
        db.session,
        name="Expression exacte",
        menu_icon_value="fa-commenting",
        category="Critères de recherche"
    )
)

admin.add_view(
    CleRechercheInteretView(
        CleRechercheInteret,
        db.session,
        name="Clé",
        menu_icon_value="fa-key",
        category="Critères de recherche"
    )
)

admin.add_view(
    ExpressionDansCleRechercheInteretView(
        ExpressionDansCleRechercheInteret,
        db.session,
        name="Expression exacte dans la clé",
        menu_icon_value="fa-cubes",
        category="Critères de recherche"
    )
)

admin.add_view(
    ExpressionReguliereRechercheInteretView(
        ExpressionReguliereRechercheInteret,
        db.session,
        name="Expression régulière",
        menu_icon_value="fa-magic",
        category="Critères de recherche"
    )
)

admin.add_view(
    InformationRechercheInteretView(
        InformationRechercheInteret,
        db.session,
        name="Information balisée",
        menu_icon_value="fa-hashtag",
        category="Critères de recherche"
    )
)

admin.add_view(
    OperationLogiqueRechercheInteretView(
        OperationLogiqueRechercheInteret,
        db.session,
        name="Opération sur critères",
        menu_icon_value="fa-list-ol",
        category="Critères de recherche"
    )
)

admin.add_view(
    RechercheInteretView(
        RechercheInteret,
        db.session,
        name="Vue globales règles",
        menu_icon_value="fa-list"
    )
)

admin.add_view(
    AdminIndexView(
        name="Manuel utilisateur",
        menu_icon_type='fa',
        menu_icon_value='fa-book',
        endpoint='/admin/manuel',
        url='/admin/manuel',
        template='/admin/manuel.html'
    )
)

admin.add_link(FaLink(name='GIE Sesam-Vitale', category='Liens', url='http://intranet',
                      icon_value='fa-globe', target="_blank"))
admin.add_link(FaLink(name='iTop', category='Liens', url='https://sl-itop/itop-prod',
                      icon_value='fa-ticket', target="_blank"))

admin.set_category_icon(name='Liens', icon_value='fa-star')


@security.context_processor
def security_context_processor():
    return dict(
        admin_base_template=admin.base_template,
        admin_view=admin.index_view,
        h=admin_helpers,
        get_url=url_for
    )


@app.route("/", methods=['GET'])
def index():
    return redirect('/admin')


@app.route("/admin/rest/statistique", methods=['GET'])
@login_required
def recuperation_statistique_generale():

    nb_automate = db.session.query(Automate).count()
    nb_execution = db.session.query(AutomateExecution).count()

    nb_execution_reussite = db.session.query(AutomateExecution).filter_by(validation_automate=True).count()
    nb_execution_echec = db.session.query(AutomateExecution).filter_by(validation_automate=False).count()

    return jsonify(
        {
            'automate': nb_automate,
            'executions': nb_execution,
            'reussites': nb_execution_reussite,
            'echecs': nb_execution_echec
        }
    ), 200


@app.route("/admin/rest/statistique/automate/<automate_id>", methods=['GET'])
@login_required
def recuperation_statistique_automate(automate_id):
    nb_execution = db.session.query(AutomateExecution).filter_by(automate_id=automate_id).count()

    nb_execution_reussite = db.session.query(AutomateExecution).filter_by(validation_automate=True, automate_id=automate_id).count()
    nb_execution_echec = db.session.query(AutomateExecution).filter_by(validation_automate=False, automate_id=automate_id).count()

    return jsonify(
        {
            'executions': nb_execution,
            'reussites': nb_execution_reussite,
            'echecs': nb_execution_echec
        }
    ), 200


@app.route("/admin/rest/automate-execution", methods=['GET'])
@login_required
def lecture_automates_executions():
    executions = db.session.query(AutomateExecution).order_by(AutomateExecution.date_finalisation.desc()).paginate(1, 25)  # type: Pagination
    return AutomateExecutionDataTableSchema().jsonify(AutomateExecutionDataTable(executions.items)), 200


@app.route("/admin/rest/automate-execution/<automate_execution_id>", methods=['GET'])
@login_required
def lecture_automate_execution(automate_execution_id):
    execution = db.session.query(AutomateExecution).get(automate_execution_id)
    return AutomateExecutionSchema().jsonify(execution), 200 if execution is not None else 404


@app.route("/admin/rest/automate-execution/automate/<automate_id>", methods=['GET'])
@login_required
def lecture_automate_executions(automate_id):

    executions = db.session.query(AutomateExecution).filter_by(
        automate_id=automate_id
    ).order_by(
        AutomateExecution.date_finalisation.desc()
    ).paginate(
        1,
        50
    )  # type: Pagination

    return AutomateExecutionDataTableSchema().jsonify(AutomateExecutionDataTable(executions.items)), 200


@app.route("/admin/rest/assistance-saisie", methods=['GET'])
@login_required
def assistance_saisie():

    configurations = db.session.query(Configuration).all()  # type: list[Configuration]

    for conf_globale in configurations:
        Session.charger_input(
            conf_globale.designation,
            conf_globale.valeur,
            conf_globale.format
        )

    propositions = list()

    for el in Session.UNIVERSELLE.variables_disponibles:
        propositions.append('{{'+str(el)+'}}')

    for filtre in SessionFiltre.FILTRES:
        propositions.append('|'+filtre.methode)

    return jsonify(
        propositions
    ), 200


@app.route("/admin/rest/assistance-saisie/automate/<automate_id>", methods=['GET'])
@login_required
def assistance_saisie_automate(automate_id):
    automate = db.session.query(Automate).get(automate_id)

    if automate is None:
        return jsonify({'message': 'Impossible de proposer la liste des variables disponibles pour un automate inexistant'})

    propositions = list()

    for el in automate.detecteur.regles:  # type: RechercheInteret
        if el.friendly_name is not None:
            propositions.append('{{' + el.friendly_name + '}}')

    for el in automate.actions:  # type: ActionNoeud
        if el.friendly_name is not None:
            propositions.append('{{' + el.friendly_name + '}}')

    return jsonify(
        propositions
    ), 200


@app.route("/admin/service", methods=['GET'])
@login_required
def etat_service():
    return jsonify({}), 204 if InstanceInteroperabilite.current_thread is None else 200


@app.route("/admin/service", methods=['POST'])
@login_required
def demarrer_service():
    demarrage = InstanceInteroperabilite.demarrer()
    return jsonify({}), 201 if demarrage is True else 409


@app.route("/admin/service", methods=['DELETE'])
@login_required
def arreter_service():
    arret = InstanceInteroperabilite.arreter()
    return jsonify({}), 204 if arret is True else 409


@app.route("/admin/rest/simulation/detecteur/fichier", methods=['POST'])
def simulation_detecteur_fichier():

    if 'file' not in request.files:
        return jsonify({'message': 'Aucun fichier envoyé'}), 400

    mon_fichier = request.files['file']  # type: FileStorage

    if (mon_fichier.content_type != 'application/octet-stream' and mon_fichier.content_type != 'message/rfc822') or (mon_fichier.filename.endswith('.eml') is False and mon_fichier.filename.endswith('.msg') is False):
        return jsonify({'message': 'Fichier message invalide, fichier binaire *.EML ou *.MSG requis !'}), 400

    if mon_fichier.filename.endswith('.eml') is True:
        mon_message = Mail.from_eml(mon_fichier.stream.read())
    else:
        mon_message = Mail.from_msg(mon_fichier.stream.read())

    detecteurs = db.session.query(Detecteur).all()

    ob_detecteurs = list()
    ma_reponse_html = str()

    ma_reponse_html += """
    <div class="panel box box-warning">
      <div class="box-header with-border">
        <h4 class="box-title">
          <a data-toggle="collapse" data-parent="#accordion" href="#collapse-x" aria-expanded="false" class="">
            Ce que le moteur perçoit
          </a>
        </h4>
      </div>
      <div id="collapse-x" class="panel-collapse collapse" aria-expanded="false" style="">
        <div class="box-body">
            <pre>
    <code class="json">
{perception_moteur}
    </code>
            </pre>
        </div>
      </div>
    </div>""".format(
        perception_moteur=dumps(mon_message.extraction_interet.interets, indent=4, ensure_ascii=False)
    )

    for detecteur, i in zip(detecteurs, range(0, len(detecteurs))):
        ob_detecteurs.append(
            ServiceTranspositionModels.generer_detecteur(detecteur)
        )
        ob_detecteurs[-1].lance_toi(mon_message)

        ma_reponse_html += """
<div class="panel box {box_color}">
  <div class="box-header with-border">
    <h4 class="box-title">
      <a data-toggle="collapse" data-parent="#accordion" href="#collapse{i_row}" aria-expanded="false" class="">
        {detecteur_res}
      </a>
    </h4>
  </div>
  <div id="collapse{i_row}" class="panel-collapse collapse" aria-expanded="false" style="">
    <div class="box-body">
        <pre>
<code>
{detecteur_explications}
</code>
        </pre>
    </div>
  </div>
</div>""".format(
            detecteur_res=str(ob_detecteurs[-1]),
            detecteur_explications=ob_detecteurs[-1].explain(),
            box_color="box-success" if ob_detecteurs[-1].est_accomplis else 'box-danger',
            i_row=str(i),
        )

    return Response(
        ma_reponse_html,
        status=200,
        content_type='text/html'
    )


@app.route("/admin/rest/simulation/detecteur", methods=['POST'])
@login_required
def simulation_detecteur():

    detecteur_id = request.form.get('detecteur_id', type=int, default=None)

    sujet = request.form.get('sujet', type=str, default=None)
    corps = request.form.get('corps', type=str, default=None)

    if sujet is None:
        return jsonify({'message': 'Formulaire incomplet, manque le sujet de la source'}), 400
    if corps is None:
        return jsonify({'message': 'Formulaire incomplet, manque le corps de la source'}), 400

    if detecteur_id is None:
        return jsonify({'message': 'Formulaire incomplet, manque l\'identifiant du detecteur cible à tester'}), 400

    detecteur = db.session.query(Detecteur).get(detecteur_id)  # type: Detecteur

    if detecteur is None:
        return jsonify({'message': 'Impossible de trouver le detecteur n°'+str(detecteur_id)}), 404

    from hermes_ui.moteur.transcription import ServiceTranspositionModels

    from hermes.detecteur import Detecteur as DetecteurNatif
    from hermes.source import Source as SourceNatif

    k = DetecteurNatif(
        detecteur.designation
    )

    for regle in detecteur.regles:
        k.je_veux(
            ServiceTranspositionModels.generer_recherche_interet(regle)
        )

    d = SourceNatif(
        sujet,
        corps
    )

    k.lance_toi(
        d
    )

    return jsonify(
        {
            'explications': k.explain(),
            'interets': d.extraction_interet.interets
        }
    ), 200 if k.est_accomplis is True else 409


@app.route("/admin/rest/simulation/extraction-interet", methods=['POST'])
@login_required
def simulation_extraction_interet():
    sujet = request.form.get('sujet', type=str, default=None)
    corps = request.form.get('corps', type=str, default=None)

    if sujet is None:
        return jsonify({'message': 'Formulaire incomplet, manque le sujet de la source'}), 409
    if corps is None:
        return jsonify({'message': 'Formulaire incomplet, manque le corps de la source'}), 409

    mon_extraction_interet = ExtractionInteret(
        sujet,
        corps
    )

    return jsonify(
        mon_extraction_interet.interets
    ), 201


@app.route("/admin/rest/logger", methods=['GET'])
@login_required
def lecture_journal():
    offset = request.args.get('offset', type=int, default=None)

    try:
        with StringIO('\n'.join([str(el.msg) for el in mem_handler.buffer])) as fp:

            # Récupération de l'offset maximale
            fp.seek(0, 2)
            max_offset = fp.tell()

            # Revenir au début du fichier
            fp.seek(0, 1)

            if offset is not None and max_offset > offset >= 0:
                fp.seek(offset)
            return jsonify(
                {
                    'logs': fp.readlines() if offset > 0 else [],
                    'offset': fp.tell() if offset > 0 else max_offset
                }
            ), 200
    except FileNotFoundError as e:
        pass
    except IOError as e:
        pass

    return jsonify({'logs': [], 'offset': 0}), 204


@app.route("/admin/rest/detecteur", methods=['GET'])
def lecture_detecteurs():
    detecteurs = db.session.query(Detecteur).all()

    return DetecteurSchema(many=True).jsonify(detecteurs), 200


@app.route("/admin/rest/automate", methods=['GET'])
def lecture_automates():
    automates = db.session.query(Automate).all()

    return AutomateSchema(many=True).jsonify(automates), 200


@app.route("/admin/rest/legacy/automate/<automate_id>", methods=['GET'])
def lecture_legacy_automate(automate_id):
    automate = db.session.query(Automate).get(automate_id)  # type: Automate
    if automate is None:
        return jsonify({'message': 'Aucun automate ne correspond à ID {}'.format(automate_id)}), 404
    return AutomateLegacySchema().jsonify(automate), 200


@app.route("/admin/rest/type/action_noeud", methods=['GET'])
def lecture_liste_action_noeud_type():

    return jsonify(
        ActionNoeud.descriptifs()
    ), 200


@app.route("/admin/rest/automate/<automate_id>", methods=['GET'])
def lecture_automate(automate_id):
    automate = db.session.query(Automate).get(automate_id)  # type: Automate
    if automate is None:
        return jsonify({'message': 'Aucun automate ne correspond à ID {}'.format(automate_id)}), 404
    return AutomateSchema().jsonify(automate), 200


@app.route("/admin/rest/automate/<automate_id>/action_noeud", methods=['GET'])
def lecture_actions_automate(automate_id):
    actions = db.session.query(ActionNoeud).filter_by(automate_id=automate_id).options().all()  # type: list[ActionNoeud]
    return ActionNoeudSchema(many=True).jsonify(actions), 200


@app.route("/admin/rest/automate/<automate_id>/action_noeud/<action_noeud_id>", methods=['GET'])
def lecture_action_automate(automate_id, action_noeud_id):
    action = db.session.query(ActionNoeud).filter_by(automate_id=automate_id, id=action_noeud_id).one()  # type: ActionNoeud

    if action is None:
        return jsonify({}), 404

    decompose_type_action = action.mapped_class_child.split("'")  # type: list[str]

    if len(decompose_type_action) != 3 or not decompose_type_action[-2].startswith('hermes_ui.models.'):
        return jsonify(
            {'message': 'Type d\'action illégale à la création: "{}"'.format(decompose_type_action[-2])}), 409

    target_module = modules['.'.join(decompose_type_action[-2].split('.')[0:-1])]

    try:
        target_model_class = getattr(target_module, decompose_type_action[-2].split('.')[-1])
    except AttributeError as e:
        return jsonify({'message': 'Le type d\'action demandé à la création est inexistant: {}'.format(
            decompose_type_action[-2].split('.')[-1])}), 400

    target_sub_action = db.session.query(target_model_class).filter_by(automate_id=automate_id, id=action_noeud_id).one()  # type: ActionNoeud

    for schema_action_noeud_class in ActionNoeudSchema.__subclasses__():

        if str(schema_action_noeud_class).split('.')[-1][0:-2].startswith(str(target_model_class).split('.')[-1][0:-2]):
            return schema_action_noeud_class().jsonify(target_sub_action), 200

    return ActionNoeudSchema().jsonify(target_sub_action), 200


@app.route("/admin/rest/automate/<automate_id>/action_noeud", methods=['POST'])
def creation_action(automate_id):
    automate = db.session.query(Automate).get(automate_id)  # type: Automate

    if not request.is_json:
        return jsonify({'message': 'Aucun corps JSON présent dans la requête HTTP'}), 400

    if automate is None:
        return jsonify({'message': 'Aucun automate ne correspond à ID {}'.format(automate_id)}), 404

    payload = request.json  # type: dict

    if 'type' not in payload.keys() or 'parent' not in payload.keys() or 'formulaire' not in payload.keys():
        return jsonify({'message': 'Le JSON présent dans la requête est invalide'}), 400

    type_action = payload['type']
    parent_information = payload['parent']
    formulaire = payload['formulaire']

    decompose_type_action = type_action.split("'")  # type: list[str]

    if len(decompose_type_action) != 3 or not decompose_type_action[-2].startswith('hermes_ui.models.'):
        return jsonify({'message': 'Type d\'action illégale à la création: "{}"'.format(decompose_type_action[-2])}), 409

    target_module = modules['.'.join(decompose_type_action[-2].split('.')[0:-1])]

    try:
        target_model_class = getattr(target_module, decompose_type_action[-2].split('.')[-1])  # type: type(ActionNoeud)
    except AttributeError as e:
        return jsonify({'message': 'Le type d\'action demandé à la création est inexistant: {}'.format(decompose_type_action[-2].split('.')[-1])}), 400

    for key_form in formulaire.keys():
        if isinstance(formulaire[key_form], str) and len(formulaire[key_form].strip()) == 0 and key_form in target_model_class.PARAMETRES.keys() and target_model_class.PARAMETRES[key_form]['required'] is False:
            formulaire[key_form] = None

    try:
        target_model_instance = target_model_class(**formulaire)  # type: ActionNoeud
    except AttributeError as e:
        return jsonify({'message': 'Le formulaire de création est invalide, pour cause de "{}"'.format(str(e))}), 400

    target_model_instance.mapped_class_child = str(target_model_instance.__class__)

    target_model_instance.automate = automate
    target_model_instance.automate_id = automate.id

    target_model_instance.createur = current_user
    target_model_instance.responsable_derniere_modification = current_user

    target_model_instance.date_creation = datetime.datetime.now()
    target_model_instance.date_modification = datetime.datetime.now()

    try:
        db.session.add(target_model_instance)
        db.session.commit()
    except IntegrityError as e:
        return jsonify({'message': str(e)}), 409

    if parent_information is None:
        automate.action_racine = target_model_instance
    else:
        if len(parent_information) != 2:
            return jsonify({'message': 'Les informations de votre action parente sont malformés'}), 400

        action_parente_id, etat_reussite = tuple(parent_information)
        action_noeud_parente = db.session.query(ActionNoeud).filter_by(automate_id=automate_id, id=int(action_parente_id)).one()  # type: ActionNoeud

        if action_noeud_parente is None:
            return jsonify({'message': 'L\'action parente n\'existe pas !'}), 404

        if 'ECHEC' in parent_information:
            target_model_instance.action_echec_id = action_noeud_parente.id
        elif 'REUSSITE' in parent_information:
            target_model_instance.action_reussite_id = action_noeud_parente.id

    try:
        db.session.commit()
        db.session.flush()
    except IntegrityError as e:
        return jsonify({'message': str(e)}), 409

    return jsonify({}), 201


@app.route("/admin/rest/automate/<automate_id>/action_noeud/<action_noeud_id>", methods=['PUT', 'PATCH'])
def modification_action(automate_id, action_noeud_id):
    automate = db.session.query(Automate).get(automate_id)  # type: Automate
    action_noeud = db.session.query(ActionNoeud).filter_by(automate_id=automate_id, id=action_noeud_id).first()  # type: ActionNoeud

    if not request.is_json:
        return jsonify({'message': 'Aucun corps JSON présent dans la requête HTTP'}), 400

    if automate is None:
        return jsonify({'message': 'Aucun automate ne correspond à ID {}'.format(automate_id)}), 404
    if action_noeud is None:
        return jsonify({'message': 'Aucun action noeud ne correspond à ID {} pour l\'automate ID {}'.format(action_noeud_id, automate_id)}), 404

    payload = request.json  # type: dict

    if 'type' not in payload.keys() or 'formulaire' not in payload.keys():
        return jsonify({'message': 'Le JSON présent dans la requête est invalide'}), 400

    type_action = payload['type']
    formulaire = payload['formulaire']  # type: dict

    decompose_type_action = type_action.split("'")  # type: list[str]

    target_module = modules['.'.join(decompose_type_action[-2].split('.')[0:-1])]

    target_model_class = getattr(target_module, decompose_type_action[-2].split('.')[-1])
    target_model_instance = db.session.query(target_model_class).get(action_noeud.id)  # type: ActionNoeud

    for key_attr in formulaire.keys():
        try:
            getattr(target_model_instance, key_attr)
        except AttributeError as e:
            return jsonify({'message': str(e)}), 409

        if key_attr in target_model_class.PARAMETRES.keys() and target_model_class.PARAMETRES[key_attr]['format'] == 'CHECKBOX':
            formulaire[key_attr] = True if formulaire[key_attr] == 1 else False

        if isinstance(formulaire[key_attr], str) and len(formulaire[key_attr].strip()) == 0 and key_attr in target_model_class.PARAMETRES.keys() and target_model_class.PARAMETRES[key_attr]['required'] is False:
            formulaire[key_attr] = None

        setattr(target_model_instance, key_attr, formulaire[key_attr])

    try:
        db.session.commit()
        db.session.flush()
    except IntegrityError as e:
        return jsonify({'message': str(e)}), 409

    return jsonify({}), 200


@app.route("/admin/rest/automate/<automate_id>/action_noeud/<action_noeud_id>", methods=['DELETE'])
def supprimer_action(automate_id, action_noeud_id):
    automate = db.session.query(Automate).get(automate_id)  # type: Automate
    action_noeud = db.session.query(ActionNoeud).filter_by(automate_id=automate_id,
                                                           id=action_noeud_id).one()  # type: ActionNoeud

    if automate is None:
        return jsonify({'message': 'Aucun automate ne correspond à ID {}'.format(automate_id)}), 404
    if action_noeud is None:
        return jsonify({'message': 'Aucun action noeud ne correspond à ID {} pour l\'automate ID {}'.format(action_noeud_id, automate_id)}), 404

    db.session.delete(action_noeud)
    db.session.commit()

    return jsonify({}), 204


def build_sample_db():
    """
    Populate a small db with some example entries.
    """

    db.drop_all()
    db.create_all()

    with app.app_context():

        super_admin_role = Role(name='superadmin')
        admin_role = Role(name='admin')
        consultation_role = Role(name='consultation')
        maintenance_role = Role(name='maintenance')

        db.session.add(super_admin_role)
        db.session.add(admin_role)
        db.session.add(consultation_role)
        db.session.add(maintenance_role)

        db.session.commit()

        test_user = admins_store.create_user(
            first_name='Ahmed',
            last_name='TAHRI',
            email='at.sii.tahri@sesam-vitale.fr',
            password=hash_password('admin'),
            roles=[super_admin_role, admin_role]
        )

        test_user_2 = admins_store.create_user(
            first_name='Didier',
            last_name='JEAN-ROBERT',
            email='djr',
            password=hash_password('djr'),
            roles=[super_admin_role, admin_role]
        )

        db.session.add(test_user)
        db.session.add(test_user_2)

        db.session.commit()
    return


try:
    db.session.query(Role).all()
except NoReferencedTableError as e:
    build_sample_db()
except NoSuchTableError as e:
    build_sample_db()
except OperationalError as e:
    build_sample_db()

# Support des fichiers JSON
legacy_files = glob(app.root_path+'/../legacy/*.json') + glob(app.root_path+'/../legacy/*.yml')

if len(legacy_files) > 10000:

    def rec_(at, act):
        """
        :param Automate at:
        :param ActionNoeud act:
        :return:
        """
        act.automate_id = at.id
        if act.action_reussite is not None:
            rec_(at, act.action_reussite)
        if act.action_echec is not None:
            rec_(at, act.action_echec)

    logger.warning('Attention, le répertoire LEGACY est utilisé. {} automate(s) vont être importés', len(legacy_files))
    logger.warning('Supprime les anciennes données')

    db.session.query(ActionNoeudExecution).delete()
    db.session.query(RechercheInteretExecution).delete()
    db.session.query(AutomateExecution).delete()

    for sb in RechercheInteret.__subclasses__():
        db.session.query(sb).delete()

    db.session.query(RechercheInteret).delete()

    db.session.query(Detecteur).delete()

    for sb in ActionNoeud.__subclasses__():
        db.session.query(sb).delete()

    db.session.query(ActionNoeud).delete()

    db.session.query(LienDetecteurRechercheInteret).delete()
    db.session.query(LienSousRegleOperationLogique).delete()

    db.session.query(Automate).delete()

    db.session.commit()
    db.session.flush()

    user_ra = db.session.query(User).first()

    logger.warning('Fin de suppression des anciennes données')

    for legacy_file in legacy_files:
        logger.warning('Installation du cas JSON : <{}>', legacy_file)

        try:
            with open(legacy_file, 'r', encoding='utf-8') as fp:

                if basename(legacy_file).endswith('.yml'):

                    new_automate = AutomateLegacySchema().loads(
                        json.dumps(
                            yaml.load(fp, yaml.FullLoader)
                        )
                    )

                else:

                    new_automate = AutomateLegacySchema().loads(fp.read())  # type: Automate

                act_r = deepcopy(new_automate.action_racine)
                new_automate.action_racine = None

                db.session.add(new_automate)
                db.session.commit()

                if act_r is not None:
                    rec_(new_automate, act_r)
                    new_automate.action_racine = act_r
                    db.session.commit()

        except IOError as e:
            logger.error(
                "Impossible d'importer votre fichier '{}' car une erreur de lecture fichier est survenue '{}'.", legacy_file, str(e)
            )
            continue
        except SQLAlchemyError as e:
            logger.error(
                "Impossible d'importer votre fichier '{}' car une erreur de transposition en base de données est survenue '{}'." ,
                legacy_file, str(e)
            )
            continue
        except MarshmallowError as e:
            logger.error(
                "Impossible d'importer votre fichier '{}' car votre fichier ne respecte pas la structure JSON obligatoire ! '{}'." ,
                legacy_file,
                str(e)
            )
            continue

    try:
        db.session.flush()
    except SQLAlchemyError as e:
        logger.warning(
            "Erreur SQL '{}'.", str(e)
        )

if __name__ == '__main__':

    app.run()