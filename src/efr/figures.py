"""Quatre figures, chacune portant un résultat du dépôt."""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from gvf.figures import cascade
from gvf.style import GRIS, OKABE_ITO, appliquer, enregistrer, formateur, fr

from .noms import francais
from .panel import ENSEMBLE

DEST = Path("results/figures")


def fig_decomposition(reformulations, dest: Path = DEST) -> dict:
    """D'où vient le rendement des capitaux propres de l'ensemble des entreprises canadiennes.

    Deux cascades, une par façon de traiter les soldes entre sociétés d'un même groupe. Le point de
    départ est le rendement de l'exploitation, et la seule marche est l'apport de l'emprunt.
    """
    appliquer()
    fig, axes = plt.subplots(1, 2, figsize=(11.8, 4.8))
    valeurs = {}
    for ax, (titre, r) in zip(axes, reformulations.items(), strict=True):
        exploitation = 400.0 * r.rendement_exploitation
        apport = 400.0 * r.apport_du_financement
        # l'exploitation est une barre et non un point de départ invisible : sans elle, le lecteur
        # ne voit pas d'où part la cascade
        cumuls = cascade(ax, ["Rendement de\nl'exploitation", "Apport de l'emprunt"],
                         [exploitation, apport], depart=0.0,
                         total="Rendement des\ncapitaux propres", decimales=2)
        ax.set_title(titre, fontsize=11)
        ax.yaxis.set_major_formatter(formateur(0, " %"))
        ax.annotate(f"l'emprunt pèse {fr(100 * apport / cumuls[-1], 1)} % du rendement",
                    (1, exploitation + apport), xytext=(0, 20), textcoords="offset points",
                    ha="center", fontsize=9, color=GRIS)
        valeurs[titre] = {"exploitation_pct": exploitation, "apport_pct": apport,
                          "rendement_pct": float(cumuls[-1])}
    axes[0].set_ylabel("Rendement annuel, en % des capitaux propres")
    fig.suptitle("Presque tout le rendement vient de l'affaire, presque rien de l'emprunt")
    enregistrer(fig, dest, "decomposition")
    plt.close(fig)
    return valeurs


def fig_industries(moyenne, dest: Path = DEST) -> dict:
    """Chaque industrie, son rendement d'exploitation et ce que l'emprunt y ajoute."""
    appliquer()
    bloc = moyenne[moyenne["industrie"].ne(ENSEMBLE)].copy()
    bloc = bloc[np.isfinite(bloc["rendement_exploitation_pct"])
                & np.isfinite(bloc["apport_du_financement_pct"])]

    fig, ax = plt.subplots(figsize=(9.8, 6.6))
    ax.scatter(bloc["rendement_exploitation_pct"], bloc["apport_du_financement_pct"], s=46,
               color=OKABE_ITO[0], alpha=0.8, zorder=4)
    ax.axhline(0, color=GRIS, linewidth=1.0)
    # échelle logarithmique symétrique : une industrie tombe à moins vingt-huit points, et sur une
    # échelle ordinaire elle écraserait les trente-huit autres contre l'axe
    ax.set_yscale("symlog", linthresh=2.0)
    ax.set_yticks([-20, -10, -5, -2, 0, 2, 5])
    ax.get_yaxis().set_major_formatter(formateur(0))
    extremes = bloc.reindex(bloc["apport_du_financement_pct"].abs().sort_values().index).tail(6)
    for rang, (_, ligne) in enumerate(extremes.iterrows()):
        cote = 8 if ligne["rendement_exploitation_pct"] < 25 else -8
        ax.annotate(francais(ligne["industrie"], 38),
                    (ligne["rendement_exploitation_pct"], ligne["apport_du_financement_pct"]),
                    xytext=(cote, 11 if rang % 2 else -13), textcoords="offset points",
                    fontsize=8, color=GRIS, ha="left" if cote > 0 else "right", va="center")
    ax.set_xlabel("Rendement de l'exploitation, moyenne 2010 à 2026 (% par an)")
    ax.set_ylabel("Ce que l'emprunt ajoute au rendement\ndes capitaux propres (points par an)")
    ax.xaxis.set_major_formatter(formateur(0, " %"))
    positifs = int((bloc["apport_du_financement_pct"] > 0).sum())
    ax.set_title(f"Sur {len(bloc)} industries, l'emprunt ajoute du rendement dans {positifs} et en "
                 f"retire dans {len(bloc) - positifs}")
    enregistrer(fig, dest, "industries")
    plt.close(fig)
    return {"industries": int(len(bloc)), "apport_positif": positifs}


def fig_deux_lectures(brut, net, dest: Path = DEST) -> dict:
    """La même industrie lue deux fois, selon le traitement des soldes entre sociétés d'un groupe."""
    appliquer()
    fusion = brut.merge(net, on="industrie", suffixes=("_brut", "_net"))
    fusion = fusion[fusion["industrie"].ne(ENSEMBLE)]
    fusion = fusion.reindex(fusion["apport_du_financement_pct_brut"].sort_values().index).tail(14)
    positions = np.arange(len(fusion))

    fig, ax = plt.subplots(figsize=(9.8, 6.4))
    ax.barh(positions - 0.2, fusion["apport_du_financement_pct_brut"], height=0.38,
            color=OKABE_ITO[0], label="soldes du groupe laissés dans l'exploitation")
    ax.barh(positions + 0.2, fusion["apport_du_financement_pct_net"], height=0.38,
            color=OKABE_ITO[1], label="soldes du groupe comptés comme du financement")
    ax.axvline(0, color=GRIS, linewidth=1.0)
    ax.set_yticks(positions, [francais(nom) for nom in fusion["industrie"]], fontsize=8.5)
    ax.set_xlabel("Ce que l'emprunt ajoute au rendement des capitaux propres (points par an)")
    ax.legend(loc="lower right")
    changent = int((np.sign(fusion["apport_du_financement_pct_brut"])
                    != np.sign(fusion["apport_du_financement_pct_net"])).sum())
    ax.set_title(f"Le traitement des soldes entre sociétés d'un même groupe change le signe dans "
                 f"{changent} des {len(fusion)} industries montrées")
    enregistrer(fig, dest, "deux_lectures")
    plt.close(fig)
    return {"changent_de_signe": changent, "montrees": int(len(fusion))}


def fig_intragroupe(table, dest: Path = DEST) -> dict:
    """La part du passif qui est de l'argent dû à une société du même groupe, trimestre après
    trimestre."""
    appliquer()
    from .donnees import COLONNE_INDUSTRIE, COLONNE_POSTE

    dollars = table[table["UOM"].eq("Dollars") & table[COLONNE_INDUSTRIE].eq(ENSEMBLE)]
    large = dollars.pivot_table(index="REF_DATE", columns=COLONNE_POSTE, values="VALUE")
    part = 100.0 * large["Total amounts owing to affiliates"] / large["Total liabilities"]
    dates = np.arange(len(part))

    fig, ax = plt.subplots(figsize=(9.6, 4.8))
    ax.plot(dates, part, color=OKABE_ITO[0], linewidth=2.0)
    ax.fill_between(dates, 0, part, color=OKABE_ITO[0], alpha=0.15, linewidth=0)
    pas = max(1, len(part) // 12)
    ax.set_xticks(dates[::pas], [str(d) for d in part.index[::pas]], rotation=45, ha="right",
                  fontsize=8)
    ax.set_ylim(0, max(30.0, float(part.max()) * 1.15))
    ax.set_ylabel("Part du passif due à une société\ndu même groupe (%)")
    ax.yaxis.set_major_formatter(formateur(0, " %"))
    ax.set_title(f"Un quart du passif des entreprises canadiennes est de l'argent dû à leur propre "
                 f"groupe ({fr(float(part.iloc[-1]), 1)} % au dernier trimestre)")
    enregistrer(fig, dest, "intragroupe")
    plt.close(fig)
    return {"debut_pct": float(part.iloc[0]), "fin_pct": float(part.iloc[-1]),
            "minimum_pct": float(part.min()), "maximum_pct": float(part.max())}
