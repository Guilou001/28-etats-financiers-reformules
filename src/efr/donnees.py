"""Le bilan trimestriel des entreprises canadiennes, téléchargé par script et jamais commité.

Statistique Canada publie chaque trimestre le bilan et le compte de résultat agrégés des entreprises
non financières du pays, découpés en quarante industries. Le tableau porte le numéro 33-10-0225. Il
compte 327 360 lignes et couvre 66 trimestres, de janvier 2010 à avril 2026.

Sa licence est la licence ouverte de Statistique Canada, qui permet l'usage et la redistribution avec
attribution. Rien n'est redistribué ici quand même, par convention du portefeuille.
"""

from __future__ import annotations

import io
import ssl
import urllib.request
import zipfile
from pathlib import Path

import pandas as pd

RACINE = Path("data/raw")
AGENT = "Guillaume Vaudescal 88989051+Guilou001@users.noreply.github.com"
URL = "https://www150.statcan.gc.ca/n1/tbl/csv/33100225-eng.zip"
FICHIER = "33100225.csv"

COLONNE_INDUSTRIE = "North American Industry Classification System (NAICS)"
COLONNE_POSTE = "Balance sheet and income statement components, selected financial ratios"


def _contexte() -> ssl.SSLContext:
    """Le magasin de certificats du système, faute de quoi Python échoue là où curl passe."""
    try:
        import truststore

        return truststore.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    except ImportError:      # pragma: no cover - dépend de l'environnement
        return ssl.create_default_context()


def fetch(racine: Path = RACINE) -> Path:
    """Le tableau, décompressé sur le disque."""
    racine.mkdir(parents=True, exist_ok=True)
    requete = urllib.request.Request(URL, headers={"User-Agent": AGENT})
    with urllib.request.urlopen(requete, timeout=300, context=_contexte()) as reponse:  # noqa: S310
        archive = zipfile.ZipFile(io.BytesIO(reponse.read()))
    archive.extract(FICHIER, racine)
    return racine / FICHIER


def charger(racine: Path = RACINE) -> pd.DataFrame:
    """Le tableau, réduit au Canada et aux colonnes utiles.

    Le fichier commence par une marque d'ordre des octets que pandas laisse collée au nom de la
    première colonne. La retirer évite une erreur de clé qui ne se voit qu'à l'exécution.
    """
    chemin = racine / FICHIER
    if not chemin.exists():
        raise FileNotFoundError(f"{chemin} absent : lancer d'abord `efr fetch`")
    table = pd.read_csv(chemin, low_memory=False)
    table.columns = [c.strip("﻿") for c in table.columns]
    table = table[table["GEO"] == "Canada"]
    return table[["REF_DATE", COLONNE_INDUSTRIE, COLONNE_POSTE, "VALUE", "UOM"]]


def postes(table: pd.DataFrame, industrie: str, periode: str) -> pd.Series:
    """Tous les postes d'une industrie à un trimestre, en millions de dollars."""
    bloc = table[table["REF_DATE"].eq(periode) & table[COLONNE_INDUSTRIE].eq(industrie)
                 & table["UOM"].eq("Dollars")]
    if bloc.empty:
        raise ValueError(f"aucune donnée pour {industrie} au {periode}")
    return bloc.set_index(COLONNE_POSTE)["VALUE"]


def industries(table: pd.DataFrame) -> list[str]:
    """Les quarante industries du tableau, l'ensemble en tête."""
    return list(table[COLONNE_INDUSTRIE].unique())


def periodes(table: pd.DataFrame) -> list[str]:
    return sorted(table["REF_DATE"].unique())


def identite_du_bilan(postes_industrie: pd.Series) -> float:
    """L'actif moins le passif moins les capitaux propres. Doit valoir zéro."""
    return float(postes_industrie["Total assets"] - postes_industrie["Total liabilities"]
                 - postes_industrie["Total equity"])
