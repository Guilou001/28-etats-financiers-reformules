"""Le calcul répété sur les quarante industries et les soixante-six trimestres."""

from __future__ import annotations

import numpy as np
import pandas as pd

from .donnees import COLONNE_INDUSTRIE, COLONNE_POSTE, identite_du_bilan, industries, periodes
from .reformulation import ecart_a_l_identite, reformuler

ENSEMBLE = "Total, non-financial industries"


def panel(table: pd.DataFrame, intragroupe: str = "exploitation") -> pd.DataFrame:
    """Une ligne par industrie et par trimestre.

    Les grandeurs de rentabilité sont annualisées en multipliant par quatre : le tableau est
    trimestriel, et un rendement trimestriel ne se compare à rien.
    """
    dollars = table[table["UOM"].eq("Dollars")]
    large = dollars.pivot_table(index=["REF_DATE", COLONNE_INDUSTRIE], columns=COLONNE_POSTE,
                                values="VALUE")
    lignes = []
    for (periode, industrie), postes_ligne in large.iterrows():
        try:
            r = reformuler(postes_ligne, intragroupe)
        except (KeyError, ZeroDivisionError, ValueError):
            continue
        if not np.isfinite(r.actif_exploitation_net) or abs(r.actif_exploitation_net) < 1.0:
            continue
        lignes.append({
            "periode": periode, "industrie": industrie, "intragroupe": intragroupe,
            "rendement_exploitation_pct": 400.0 * r.rendement_exploitation,
            "cout_de_la_dette_pct": 400.0 * r.cout_de_la_dette,
            "levier": r.levier,
            "apport_du_financement_pct": 400.0 * r.apport_du_financement,
            "rendement_capitaux_propres_pct": 400.0 * r.rendement_capitaux_propres,
            "marge_pct": 100.0 * r.marge, "rotation": 4.0 * r.rotation,
            "part_intragroupe_passif": r.intragroupe_passif,
            "ecart_identite": ecart_a_l_identite(r),
            "identite_bilan": identite_du_bilan(postes_ligne),
        })
    return pd.DataFrame(lignes)


def moyennes_par_industrie(detail: pd.DataFrame) -> pd.DataFrame:
    """La moyenne de chaque industrie sur toute la période, et la part du financement.

    La moyenne est prise sur les trimestres et non sur un seul, pour que le résultat ne dépende pas
    du point du cycle où l'on regarde.
    """
    colonnes = ["rendement_exploitation_pct", "cout_de_la_dette_pct", "levier",
                "apport_du_financement_pct", "rendement_capitaux_propres_pct", "marge_pct",
                "rotation"]
    moyenne = detail.groupby("industrie", sort=False)[colonnes].mean()
    moyenne["trimestres"] = detail.groupby("industrie", sort=False).size()
    with np.errstate(divide="ignore", invalid="ignore"):
        moyenne["part_du_financement_pct"] = 100.0 * (moyenne["apport_du_financement_pct"]
                                                      / moyenne["rendement_capitaux_propres_pct"])
    return moyenne.reset_index()


def verdict(moyenne: pd.DataFrame) -> dict:
    """Les trois nombres qui répondent à la question du dépôt."""
    hors_ensemble = moyenne[moyenne["industrie"].ne(ENSEMBLE)]
    positif = hors_ensemble[hors_ensemble["apport_du_financement_pct"] > 0]
    dominant = hors_ensemble[
        hors_ensemble["apport_du_financement_pct"].abs()
        > hors_ensemble["rendement_exploitation_pct"].abs()]
    return {
        "industries": int(len(hors_ensemble)),
        "financement_positif": int(len(positif)),
        "financement_dominant": int(len(dominant)),
        "apport_median_pct": float(hors_ensemble["apport_du_financement_pct"].median()),
        "apport_median_part_pct": float(hors_ensemble["part_du_financement_pct"].median()),
        "exploitation_mediane_pct": float(hors_ensemble["rendement_exploitation_pct"].median()),
    }


def controles(table: pd.DataFrame) -> pd.DataFrame:
    """Les deux identités qui doivent tenir partout : le bilan, et l'égalité de la reformulation."""
    lignes = []
    for intragroupe in ("exploitation", "financement"):
        detail = panel(table, intragroupe)
        lignes.append({
            "intragroupe": intragroupe, "lignes": len(detail),
            "identite_bilan_max": float(detail["identite_bilan"].abs().max()),
            "identite_reformulation_max": float(detail["ecart_identite"].abs().max()),
        })
    return pd.DataFrame(lignes)


__all__ = ["ENSEMBLE", "controles", "industries", "moyennes_par_industrie", "panel", "periodes",
           "verdict"]
