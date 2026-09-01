"""Le calcul répété sur les quarante industries et sur les trimestres qui se calculent.

Le tableau porte soixante-six trimestres, mais huit des postes que la reformulation additionne ne
sont publiés qu'à partir du premier trimestre de 2020. Avant cette date, l'actif d'exploitation net
n'est pas calculable, et la ligne est écartée. `controles` publie la fenêtre obtenue et le nombre de
lignes écartées, pour que la couverture réelle se lise dans `results/` plutôt que dans le code.
"""

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
        # Un poste non publié rend NaN et le NaN se propage. La ligne est écartée plutôt que
        # publiée à moitié, et `controles` la compte. Le coût de la dette fait exception : il vaut
        # NaN quand la dette nette est nulle, ce qui est un résultat et non une lacune.
        if not np.isfinite(r.actif_exploitation_net) or abs(r.actif_exploitation_net) < 1.0:
            continue
        if not (np.isfinite(r.resultat_exploitation) and np.isfinite(r.capitaux_propres)):
            continue
        lignes.append({
            "periode": periode, "industrie": industrie, "intragroupe": intragroupe,
            "rendement_exploitation_pct": 400.0 * r.rendement_exploitation,
            "cout_de_la_dette_pct": 400.0 * r.cout_de_la_dette,
            "levier": r.levier,
            "apport_du_financement_pct": 400.0 * r.apport_du_financement,
            "rendement_capitaux_propres_pct": 400.0 * r.rendement_capitaux_propres,
            "marge_pct": 100.0 * r.marge, "rotation": 4.0 * r.rotation,
            "intragroupe_passif_millions": r.intragroupe_passif,
            "part_intragroupe_passif_pct": 100.0 * r.intragroupe_passif
            / float(postes_ligne["Total liabilities"]),
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
    groupes = detail.groupby("industrie", sort=False)
    moyenne = groupes[colonnes].mean()
    moyenne["trimestres"] = groupes.size()
    moyenne["periode_min"] = groupes["periode"].min()
    moyenne["periode_max"] = groupes["periode"].max()
    with np.errstate(divide="ignore", invalid="ignore"):
        moyenne["part_du_financement_pct"] = 100.0 * (moyenne["apport_du_financement_pct"]
                                                      / moyenne["rendement_capitaux_propres_pct"])
    return moyenne.reset_index()


def verdict(moyenne: pd.DataFrame) -> dict:
    """Les six nombres qui répondent à la question du dépôt.

    Trois portent le verdict : le nombre d'industries où l'emprunt ajoute du rendement, le nombre
    où il pèse plus que l'affaire, et l'apport médian. Les trois autres situent les premiers : le
    nombre d'industries retenues, la part médiane du rendement qui revient à l'emprunt et le
    rendement médian de l'exploitation.
    """
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


def _lignes_du_tableau(table: pd.DataFrame) -> int:
    """Le nombre de couples industrie-trimestre que le tableau contient, calculables ou non."""
    dollars = table[table["UOM"].eq("Dollars")]
    return int(dollars.groupby(["REF_DATE", COLONNE_INDUSTRIE], sort=False).ngroups)


def _bilan_sur_tout_le_tableau(table: pd.DataFrame) -> float:
    """L'écart maximal de l'identité du bilan sur les lignes du tableau, écartées comprises.

    Les trois totaux qu'elle emploie sont publiés sur les soixante-six trimestres, donc ce contrôle
    couvre aussi les lignes que la reformulation ne calcule pas.
    """
    dollars = table[table["UOM"].eq("Dollars")]
    large = dollars.pivot_table(index=["REF_DATE", COLONNE_INDUSTRIE], columns=COLONNE_POSTE,
                                values="VALUE")
    ecart = large["Total assets"] - large["Total liabilities"] - large["Total equity"]
    return float(ecart.abs().max())


def controles(table: pd.DataFrame) -> pd.DataFrame:
    """Les deux identités qui doivent tenir partout, et la couverture réellement obtenue.

    Aux deux écarts maximaux s'ajoutent quatre colonnes de couverture. `lignes_ecartees` compte les
    couples industrie-trimestre que le tableau porte et que le calcul n'a pas pu produire.
    `lignes_non_controlees` compte les lignes calculées dont l'écart à l'identité n'est pas défini,
    faute d'une dette nette non nulle. Elle doit valoir zéro, sans quoi le maximum publié porte sur
    moins de lignes qu'il n'y paraît.
    """
    attendues = _lignes_du_tableau(table)
    bilan_partout = _bilan_sur_tout_le_tableau(table)
    lignes = []
    for intragroupe in ("exploitation", "financement"):
        detail = panel(table, intragroupe)
        lignes.append({
            "intragroupe": intragroupe, "lignes": len(detail),
            "lignes_ecartees": attendues - len(detail),
            "periode_min": detail["periode"].min(), "periode_max": detail["periode"].max(),
            "trimestres": int(detail["periode"].nunique()),
            "identite_bilan_max": float(detail["identite_bilan"].abs().max()),
            "identite_bilan_max_tableau_entier": bilan_partout,
            "identite_reformulation_max": float(detail["ecart_identite"].abs().max()),
            "identite_reformulation_max_point_annuel":
                400.0 * float(detail["ecart_identite"].abs().max()),
            "lignes_non_controlees": int(detail["ecart_identite"].isna().sum()),
        })
    return pd.DataFrame(lignes)


__all__ = ["ENSEMBLE", "controles", "industries", "moyennes_par_industrie", "panel", "periodes",
           "verdict"]
