"""Les commandes du dépôt. Chaque chiffre du README sort d'une de ces commandes, dans `results/`."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import typer

from . import donnees
from .panel import ENSEMBLE, controles, moyennes_par_industrie, panel, verdict
from .reformulation import reformuler

app = typer.Typer(add_completion=False, help=__doc__)
RESULTATS = Path("results")
LECTURES = {"exploitation": "Soldes du groupe laissés dans l'exploitation",
            "financement": "Soldes du groupe comptés comme du financement"}


def _ecrire(table: pd.DataFrame, nom: str) -> Path:
    RESULTATS.mkdir(parents=True, exist_ok=True)
    chemin = RESULTATS / nom
    table.to_csv(chemin, index=False)
    typer.echo(f"écrit {chemin}")
    return chemin


@app.command()
def fetch():
    """Télécharger le tableau 33-10-0225 de Statistique Canada dans `data/raw`."""
    chemin = donnees.fetch()
    typer.echo(f"{chemin} : {chemin.stat().st_size:,} octets".replace(",", " "))


@app.command()
def identites():
    """Vérifier les deux égalités qui doivent tenir partout avant tout commentaire."""
    table = donnees.charger()
    resultat = controles(table)
    _ecrire(resultat, "identites.csv")
    typer.echo(resultat.to_string(index=False))


@app.command()
def ensemble(periode: str = "2026-04"):
    """La décomposition du rendement de l'ensemble des entreprises non financières."""
    table = donnees.charger()
    postes = donnees.postes(table, ENSEMBLE, periode)
    lignes = []
    for cle, titre in LECTURES.items():
        r = reformuler(postes, cle)
        lignes.append({"lecture": titre, "periode": periode,
                       "rendement_exploitation_pct": 400.0 * r.rendement_exploitation,
                       "cout_de_la_dette_pct": 400.0 * r.cout_de_la_dette,
                       "levier": r.levier,
                       "apport_du_financement_pct": 400.0 * r.apport_du_financement,
                       "rendement_capitaux_propres_pct": 400.0 * r.rendement_capitaux_propres,
                       "actif_exploitation_net": r.actif_exploitation_net,
                       "dette_financiere_nette": r.dette_financiere_nette,
                       "capitaux_propres": r.capitaux_propres})
    resultat = pd.DataFrame(lignes)
    _ecrire(resultat, "ensemble.csv")
    for _, ligne in resultat.iterrows():
        typer.echo(f"{ligne['lecture']:46s} exploitation "
                   f"{ligne['rendement_exploitation_pct']:6.2f} %  emprunt "
                   f"{ligne['apport_du_financement_pct']:6.2f} pt  total "
                   f"{ligne['rendement_capitaux_propres_pct']:6.2f} %")


@app.command()
def industries():
    """Le calcul sur les quarante industries et sur tous les trimestres calculables, deux lectures."""
    table = donnees.charger()
    verdicts = []
    for cle in LECTURES:
        detail = panel(table, cle)
        _ecrire(detail, f"panel_{cle}.csv")
        moyenne = moyennes_par_industrie(detail)
        _ecrire(moyenne, f"moyennes_{cle}.csv")
        verdicts.append({"lecture": cle, **verdict(moyenne)})
    resultat = pd.DataFrame(verdicts)
    _ecrire(resultat, "verdict.csv")
    typer.echo(resultat.to_string(index=False))


@app.command()
def figures():
    """Les quatre figures, en PNG pour le README et en PDF vectoriel pour le rapport.

    Chaque fabrique rend les nombres qu'elle dessine. Ils sont écrits dans `results/figures.json`,
    faute de quoi les chiffres que le README lit sur les figures ne seraient nulle part dans
    `results/` et ne se retrouveraient qu'en relisant la sortie console.
    """
    from . import figures as fig

    table = donnees.charger()
    periode = "2026-04"
    postes = donnees.postes(table, ENSEMBLE, periode)
    lectures = {titre: reformuler(postes, cle) for cle, titre in LECTURES.items()}
    brut = pd.read_csv(RESULTATS / "moyennes_exploitation.csv")
    net = pd.read_csv(RESULTATS / "moyennes_financement.csv")
    rendus = {
        "decomposition": fig.fig_decomposition(lectures, periode),
        "industries": fig.fig_industries(brut),
        "deux_lectures": fig.fig_deux_lectures(brut, net),
        "intragroupe": fig.fig_intragroupe(table),
    }
    RESULTATS.mkdir(parents=True, exist_ok=True)
    chemin = RESULTATS / "figures.json"
    chemin.write_text(json.dumps(rendus, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    typer.echo(f"écrit {chemin}")
    typer.echo(json.dumps(rendus, indent=2, ensure_ascii=False))


@app.command()
def tout():
    """Tous les calculs et toutes les figures. Exige `efr fetch` au préalable."""
    identites()
    ensemble()
    industries()
    figures()


if __name__ == "__main__":
    app()
