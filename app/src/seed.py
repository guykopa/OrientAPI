from sqlalchemy.orm import Session

from src.models import Formation

FORMATIONS: list[dict] = [
    # informatique — BAC+2
    {"nom": "BTS SIO option SLAM", "filiere": "informatique", "niveau": "BAC+2", "selectivite": 50,
     "description": "Services informatiques aux organisations, spécialité logiciels et applications."},
    {"nom": "BTS SIO option SISR", "filiere": "informatique", "niveau": "BAC+2", "selectivite": 48,
     "description": "Services informatiques aux organisations, spécialité infrastructures et réseaux."},
    {"nom": "BTS SNIR", "filiere": "informatique", "niveau": "BAC+2", "selectivite": 55,
     "description": "Systèmes numériques option informatique et réseaux."},
    # informatique — BAC+3
    {"nom": "BUT Informatique", "filiere": "informatique", "niveau": "BAC+3", "selectivite": 65,
     "description": "Bachelor universitaire de technologie en informatique."},
    {"nom": "Licence Informatique", "filiere": "informatique", "niveau": "BAC+3", "selectivite": 60,
     "description": "Licence générale mention informatique."},
    {"nom": "Licence Pro Développement Web", "filiere": "informatique", "niveau": "BAC+3", "selectivite": 62,
     "description": "Licence professionnelle spécialisée en développement web et mobile."},
    # informatique — BAC+5
    {"nom": "Master Informatique parcours IA", "filiere": "informatique", "niveau": "BAC+5", "selectivite": 88,
     "description": "Master spécialisé intelligence artificielle et apprentissage automatique."},
    {"nom": "Master MIAGE", "filiere": "informatique", "niveau": "BAC+5", "selectivite": 80,
     "description": "Méthodes informatiques appliquées à la gestion des entreprises."},
    {"nom": "Diplôme d'ingénieur ENSIMAG", "filiere": "informatique", "niveau": "BAC+5", "selectivite": 95,
     "description": "École nationale supérieure d'informatique et de mathématiques appliquées."},
    # gestion — BAC+2
    {"nom": "BTS Comptabilité et Gestion", "filiere": "gestion", "niveau": "BAC+2", "selectivite": 45,
     "description": "Formation en comptabilité, gestion et fiscalité des entreprises."},
    {"nom": "BTS Gestion de la PME", "filiere": "gestion", "niveau": "BAC+2", "selectivite": 42,
     "description": "Administration et gestion des petites et moyennes entreprises."},
    # gestion — BAC+3
    {"nom": "BUT Gestion des Entreprises", "filiere": "gestion", "niveau": "BAC+3", "selectivite": 58,
     "description": "Bachelor universitaire de technologie en gestion des entreprises et administrations."},
    {"nom": "Licence Gestion", "filiere": "gestion", "niveau": "BAC+3", "selectivite": 55,
     "description": "Licence générale mention gestion."},
    # gestion — BAC+5
    {"nom": "Master Contrôle de Gestion", "filiere": "gestion", "niveau": "BAC+5", "selectivite": 75,
     "description": "Master spécialisé en pilotage financier et contrôle de gestion."},
    {"nom": "Master CPA", "filiere": "gestion", "niveau": "BAC+5", "selectivite": 82,
     "description": "Comptabilité, contrôle, audit — préparation à l'expertise comptable."},
    # commerce — BAC+2
    {"nom": "BTS MCO", "filiere": "commerce", "niveau": "BAC+2", "selectivite": 44,
     "description": "Management commercial opérationnel en point de vente."},
    {"nom": "BTS NDRC", "filiere": "commerce", "niveau": "BAC+2", "selectivite": 46,
     "description": "Négociation et digitalisation de la relation client."},
    # commerce — BAC+3
    {"nom": "BUT TC", "filiere": "commerce", "niveau": "BAC+3", "selectivite": 60,
     "description": "Bachelor universitaire de technologie Techniques de commercialisation."},
    # commerce — BAC+5
    {"nom": "Master Marketing Digital", "filiere": "commerce", "niveau": "BAC+5", "selectivite": 78,
     "description": "Marketing numérique, e-commerce et data marketing."},
    # droit — BAC+3
    {"nom": "Licence Droit", "filiere": "droit", "niveau": "BAC+3", "selectivite": 62,
     "description": "Licence générale mention droit, fondamentaux du droit privé et public."},
    # droit — BAC+5
    {"nom": "Master Droit Public", "filiere": "droit", "niveau": "BAC+5", "selectivite": 78,
     "description": "Master mention droit public, spécialité droit des collectivités territoriales."},
    {"nom": "Master Droit des Affaires", "filiere": "droit", "niveau": "BAC+5", "selectivite": 85,
     "description": "Master droit des affaires et fiscalité."},
    # sciences — BAC+3
    {"nom": "Licence Mathématiques", "filiere": "sciences", "niveau": "BAC+3", "selectivite": 65,
     "description": "Licence générale mention mathématiques."},
    {"nom": "Licence Physique-Chimie", "filiere": "sciences", "niveau": "BAC+3", "selectivite": 60,
     "description": "Licence générale mention physique-chimie."},
    # sciences — BAC+5
    {"nom": "Master Mathématiques et Applications", "filiere": "sciences", "niveau": "BAC+5", "selectivite": 85,
     "description": "Master mention mathématiques et applications, parcours analyse et probabilités."},
    # santé — BAC+2
    {"nom": "BTS SP3S", "filiere": "sante", "niveau": "BAC+2", "selectivite": 50,
     "description": "Services et prestations des secteurs sanitaire et social."},
    # santé — BAC+3
    {"nom": "Licence Sciences Sanitaires et Sociales", "filiere": "sante", "niveau": "BAC+3", "selectivite": 58,
     "description": "Licence professionnelle secteur sanitaire et social."},
    # santé — BAC+5
    {"nom": "Master Santé Publique", "filiere": "sante", "niveau": "BAC+5", "selectivite": 75,
     "description": "Master santé publique, épidémiologie et politiques de santé."},
    # langues — BAC+3
    {"nom": "Licence LLCER Anglais", "filiere": "langues", "niveau": "BAC+3", "selectivite": 55,
     "description": "Langues, littératures et civilisations étrangères et régionales — anglais."},
    # langues — BAC+5
    {"nom": "Master Traduction Spécialisée", "filiere": "langues", "niveau": "BAC+5", "selectivite": 72,
     "description": "Master traduction spécialisée multilingue pour les secteurs techniques et juridiques."},
]


def seed(db: Session) -> None:
    if db.query(Formation).count() > 0:
        return
    db.add_all([Formation(**f) for f in FORMATIONS])
    db.commit()
