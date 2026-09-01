"""Quatre figures, chacune portant un résultat du dépôt."""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from gvf.figures import cascade
from gvf.style import GRIS, OKABE_ITO, appliquer, enregistrer, formateur, fr

from .noms import etiquette
from .panel import ENSEMBLE

DEST = Path("results/figures")

MOIS = {"01": "janvier", "02": "février", "03": "mars", "04": "avril", "05": "mai", "06": "juin",
        "07": "juillet", "08": "août", "09": "septembre", "10": "octobre", "11": "novembre",
        "12": "décembre"}


def _trimestre_en_francais(periode: str) -> str:
    """« 2026-04 » rendu « avril 2026 », comme le README l'écrit."""
    annee, mois = str(periode).split("-")
    return f"{MOIS[mois]} {annee}"


# Les six écarts d'un même graphique tombent parfois à la même hauteur, à quelques dixièmes de point
# près, et deux étiquettes posées au même endroit se recouvrent alors mot pour mot. Le placement est
# donc mesuré : chaque étiquette essaie les hauteurs dans l'ordre et garde la première qui tient
# dans le cadre sans toucher ni un point déjà tracé ni une étiquette déjà posée.
HAUTEURS = [13, -17, 58, -62, 103, -107, 148, -152]
TRAIT = {"arrowstyle": "-", "color": GRIS, "linewidth": 0.6, "shrinkA": 0, "shrinkB": 5}


def _poser_etiquettes(fig, ax, extremes) -> None:
    """Les noms des six industries les plus extrêmes, posés sans recouvrement.

    À appeler en dernier : le titre et les deux légendes d'axe rétrécissent le cadre, et une place
    mesurée avant eux ne vaut plus rien une fois qu'ils sont posés. Le calage automatique est figé
    juste après le premier tracé, sans quoi l'enregistrement le rejouerait, déplacerait le cadre et
    rendrait fausses les positions mesurées ici.
    """
    fig.canvas.draw()
    fig.set_layout_engine("none")
    rendu = fig.canvas.get_renderer()
    from matplotlib.transforms import Bbox

    cadre = ax.get_window_extent(rendu)
    occupe = []
    for x, y in ax.collections[0].get_offsets():
        px, py = ax.transData.transform((x, y))
        occupe.append(Bbox.from_extents(px - 7, py - 7, px + 7, py + 7))

    def poser(ligne, hauteur, trait):
        """Une étiquette au-dessus ou au-dessous de son point, rabattue vers l'intérieur du cadre.

        Un point proche d'un bord porte son nom du côté du centre : centrer le texte sur lui le
        ferait déborder du cadre, et le calage à la sauvegarde le rognerait.
        """
        x = ligne["rendement_exploitation_pct"]
        part = (ax.transData.transform((x, 0))[0] - cadre.x0) / cadre.width
        cote, ecart = ("center", 0) if 0.15 < part < 0.85 else (
            ("left", 6) if part <= 0.15 else ("right", -6))
        return ax.annotate(
            etiquette(ligne["industrie"], 24, 2),
            (x, ligne["apport_du_financement_pct"]), xytext=(ecart, hauteur),
            textcoords="offset points", fontsize=8, color=GRIS, ha=cote,
            va="bottom" if hauteur > 0 else "top",
            arrowprops=TRAIT if trait else None)

    for _, ligne in extremes.iterrows():
        # L'essai se fait SANS trait de rappel : l'encombrement d'une annotation fléchée va jusqu'au
        # point, donc toute hauteur paraîtrait occupée, le point étant lui-même dans la liste, et les
        # six étiquettes retomberaient au même endroit.
        retenue, boite = HAUTEURS[0], None
        for hauteur in HAUTEURS:
            essai = poser(ligne, hauteur, trait=False)
            mesure = essai.get_window_extent(rendu)
            essai.remove()
            dedans = (cadre.x0 <= mesure.x0 and mesure.x1 <= cadre.x1
                      and cadre.y0 <= mesure.y0 and mesure.y1 <= cadre.y1)
            if dedans and not any(mesure.overlaps(autre) for autre in occupe):
                retenue, boite = hauteur, mesure
                break
        if boite is None:
            essai = poser(ligne, retenue, trait=False)
            boite = essai.get_window_extent(rendu)
            essai.remove()
        poser(ligne, retenue, trait=True)
        occupe.append(boite)


def fig_decomposition(reformulations, periode: str, dest: Path = DEST) -> dict:
    """D'où vient le rendement des capitaux propres de l'ensemble des entreprises canadiennes.

    Deux cascades, une par façon de traiter les soldes entre sociétés d'un même groupe. Le point de
    départ est le rendement de l'exploitation, et la seule marche est l'apport de l'emprunt.

    Le trimestre porté par le titre est celui qui a servi à choisir les postes, et il est rendu avec
    la figure : sortie du README, elle se lirait sinon comme une moyenne de période.
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
        valeurs[titre] = {"periode": str(periode), "exploitation_pct": exploitation,
                          "apport_pct": apport, "rendement_pct": float(cumuls[-1])}
    axes[0].set_ylabel("Rendement annuel, en % des capitaux propres")
    fig.suptitle("Presque tout le rendement vient de l'affaire, presque rien de l'emprunt "
                 f"({_trimestre_en_francais(periode)})")
    enregistrer(fig, dest, "decomposition")
    plt.close(fig)
    return valeurs


def fig_industries(moyenne, dest: Path = DEST) -> dict:
    """Chaque industrie, son rendement d'exploitation et ce que l'emprunt y ajoute.

    Les bornes de la période sont lues dans le tableau plutôt qu'écrites en dur : l'axe ne peut pas
    annoncer une fenêtre que les moyennes ne couvrent pas.
    """
    appliquer()
    bloc = moyenne[moyenne["industrie"].ne(ENSEMBLE)].copy()
    bloc = bloc[np.isfinite(bloc["rendement_exploitation_pct"])
                & np.isfinite(bloc["apport_du_financement_pct"])]
    debut = str(bloc["periode_min"].min())[:4]
    fin = str(bloc["periode_max"].max())[:4]

    fig, ax = plt.subplots(figsize=(9.8, 6.6))
    ax.scatter(bloc["rendement_exploitation_pct"], bloc["apport_du_financement_pct"], s=46,
               color=OKABE_ITO[0], alpha=0.8, zorder=4)
    ax.axhline(0, color=GRIS, linewidth=1.0)
    # échelle logarithmique symétrique : une industrie tombe très bas, et sur une échelle ordinaire
    # elle écraserait toutes les autres contre l'axe. Le plancher est rendu avec la figure, pour que
    # le README le cite au lieu de lire la graduation.
    ax.set_yscale("symlog", linthresh=2.0)
    ax.set_yticks([-20, -10, -5, -2, 0, 2, 5])
    plancher = float(bloc["apport_du_financement_pct"].min())
    ax.get_yaxis().set_major_formatter(formateur(0))
    extremes = bloc.reindex(bloc["apport_du_financement_pct"].abs().sort_values().index).tail(6)
    ax.set_xlabel(f"Rendement de l'exploitation, moyenne {debut} à {fin} (% par an)")
    ax.set_ylabel("Ce que l'emprunt ajoute au rendement\ndes capitaux propres (points par an)")
    ax.xaxis.set_major_formatter(formateur(0, " %"))
    positifs = int((bloc["apport_du_financement_pct"] > 0).sum())
    ax.set_title(f"Sur {len(bloc)} industries, l'emprunt ajoute du rendement dans {positifs} et en "
                 f"retire dans {len(bloc) - positifs}")
    _poser_etiquettes(fig, ax, extremes)
    enregistrer(fig, dest, "industries")
    plt.close(fig)
    return {"industries": int(len(bloc)), "apport_positif": positifs,
            "apport_minimum_pct": plancher, "periode_min": str(bloc["periode_min"].min()),
            "periode_max": str(bloc["periode_max"].max())}


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
    ax.set_yticks(positions, [etiquette(nom, 34, 2) for nom in fusion["industrie"]], fontsize=8.0)
    ax.set_xlabel("Ce que l'emprunt ajoute au rendement des capitaux propres (points par an)")
    ax.xaxis.set_major_formatter(formateur(1))
    # les barres sont triées par apport croissant dans la lecture brute, donc le coin en haut à
    # gauche est le seul que ni les barres positives ni les barres négatives n'atteignent
    ax.legend(loc="upper left")
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
