"""Le nom français de chaque industrie, tel que Statistique Canada le publie.

Le calcul tourne sur le fichier anglais, dont les libellés de postes servent de clés. Les noms
qui s'affichent, eux, doivent être en français. Ils ne sont pas traduits ici : ils sont recopiés
de la version française du même tableau, téléchargée le 2026-08-30.
"""

import textwrap

# ruff: noqa: E501
# Les libellés officiels dépassent parfois cent dix caractères. Les couper serait les réécrire,
# et ce fichier a justement pour raison d'être de ne pas les réécrire.
FRANCAIS = {
    "Total, non-financial industries":
        "Total des branches d'activité non financières",
    "Agriculture, forestry, fishing and hunting [11]":
        "Agriculture, foresterie, pêche et chasse [11]",
    "Oil and gas extraction and support services":
        "Extraction de pétrole et de gaz et services de soutien",
    "Mining and quarrying (except oil and gas) and support activities":
        "Extraction minière et exploitation en carrière (sauf l'extraction de pétrole et de gaz) et activités de soutien",
    "Utilities [22]":
        "Services publics [22]",
    "Construction [23]":
        "Construction [23]",
    "Food and soft drink and ice manufacturing":
        "Fabrication d'aliments, de boissons gazeuses et de glace",
    "Alcohol beverage, tobacco and cannabis product manufacturing":
        "Fabrication de boissons alcoolisées, du tabac et de produits du cannabis",
    "Wood product and paper manufacturing":
        "Fabrication de produits en bois et de papier",
    "Petroleum and coal product manufacturing [324]":
        "Fabrication de produits du pétrole et du charbon [324]",
    "Basic chemical manufacturing and resin, synthetic rubber, and artificial and synthetic fibres and filaments manufacturing":
        "Fabrication de produits chimiques de base et de résines, de caoutchouc synthétique et de fibres et de filaments artificiels et synthétiques",
    "Pharmaceutical and medecine manufacturing, and soap, agricultural chemicals, paint and other chemical product manufacturing":
        "Fabrication de produits pharmaceutiques et de médicaments, de savons, de produits chimiques agricoles, de peintures et d'autres produits chimiques",
    "Plastics and rubber products manufacturing [326]":
        "Fabrication de produits en plastique et en caoutchouc [326]",
    "Non-metallic mineral product manufacturing [327]":
        "Fabrication de produits minéraux non métalliques [327]",
    "Primary metal and fabricated metal product and machinery manufacturing":
        "Première transformation des métaux, fabrication de produits métalliques et de machines",
    "Computer and electronic equipment manufacturing [334]":
        "Fabrication de produits informatiques et électroniques [334]",
    "Motor vehicle and trailer manufacturing":
        "Fabrication de véhicules automobiles et de remorques de véhicules automobiles",
    "Motor vehicle parts manufacturing [3363]":
        "Fabrication de pièces pour véhicules automobiles [3363]",
    "Aerospace, rail and ship products and other transportation equipment manufacturing":
        "Fabrication de produits aérospaciaux et ferroviaires, construction de navires et fabrication d'autres types de matériel de transport",
    "Clothing, textile, leather and furniture manufacturing, and other manufacturing":
        "Fabrication de vêtements, de produits textiles et de produits en cuir, de meubles et d'autres activités de fabrication",
    "Motor vehicle and motor vehicle parts and accessories merchant wholesalers [415]":
        "Grossistes-marchands de véhicules automobiles, et de pièces et d'accessoires de véhicules automobiles [415]",
    "Building material and supplies merchant wholesalers [416]":
        "Grossistes-marchands de matériaux et fournitures de construction [416]",
    "Machinery, equipment and supplies merchant wholesalers [417]":
        "Grossistes-marchands de machines, de matériel et de fournitures [417]",
    "Other wholesalers":
        "Autres grossistes-marchands",
    "Motor vehicle and parts dealers [441]":
        "Concessionnaires de véhicules et de pièces automobiles [441]",
    "Food and beverage stores [445]":
        "Magasins d'alimentation [445]",
    "Clothing, sporting goods, and general merchandise stores":
        "Magasins de vêtements, d'articles de sport et de marchandises diverses",
    "Other retailers":
        "Autres détaillants",
    "Transportation, postal and couriers services, and support activities for transportation":
        "Transport, services postaux et services de messagers, et support aux activités de transport",
    "Pipelines [486]":
        "Transport par pipeline [486]",
    "Warehousing [493]":
        "Entreposage [493]",
    "Publishing, motion picture and sound recording, broadcasting, and information services":
        "Édition, industries du film et de l'enregistrement sonore, radiotélévision et services d'information",
    "Telecommunications [517]":
        "Télécommunications [517]",
    "Real estate [531]":
        "Services immobiliers [531]",
    "Rental and leasing of automotive, machinery and equipment, and other goods":
        "Services de location et de location à bail de véhicules automobiles, de machinerie et d'équipement, et d'autres biens",
    "Professional, scientific and technical services [54]":
        "Services professionnels, scientifiques et techniques [54]",
    "Administrative and support, waste management and remediation services [56]":
        "Services administratifs, services de soutien, services de gestion des déchets et services d'assainissement [56]",
    "Educational, health care and social assistance services":
        "Services d'enseignement, soins de santé et assistance sociale",
    "Arts, entertainment and recreation, and accommodation and food services":
        "Arts, spectacles et loisirs, et services d'hébergement et de restauration",
    "Repair, maintenance and personal services":
        "Réparation, entretien et services personnels",
}


def francais(nom: str) -> str:
    """Le nom français, sans son code entre crochets."""
    return FRANCAIS.get(nom, nom).split(" [")[0]


def etiquette(nom: str, largeur: int = 24, lignes: int = 2) -> str:
    """Le nom français replié sur plusieurs lignes, coupé seulement entre deux mots.

    Une coupe au caractère près donnait « Fabrication de véhicules automobiles e », que le lecteur
    ne peut ni prononcer ni rattacher à une industrie. Le repli respecte les mots, et quand le nom
    dépasse encore le nombre de lignes autorisé, les points de suspension disent qu'il est tronqué.
    """
    entier = francais(nom)
    morceaux = textwrap.wrap(entier, largeur) or [entier]
    gardees = morceaux[:lignes]
    if len(morceaux) > lignes:
        gardees[-1] = gardees[-1] + "\u2026"
    return "\n".join(gardees)
