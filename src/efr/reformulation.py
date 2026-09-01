"""Séparer ce qu'une entreprise gagne en vendant de ce qu'elle gagne en empruntant.

**Le problème, en mots simples.** Quand une entreprise rapporte de l'argent à ses propriétaires, deux
explications sont possibles. Soit elle vend bien ce qu'elle fabrique. Soit elle a beaucoup emprunté,
et l'argent emprunté lui rapporte plus qu'il ne lui coûte. Ce n'est pas la même chose : la première
explication tient dans la durée, la seconde se retourne dès que les taux montent.

Le bilan publié ne fait pas cette séparation. Il range les actifs par nature, pas par usage.
Reformuler, c'est le réécrire en deux blocs.

**Le premier bloc est l'exploitation.** Ce qu'il faut pour faire tourner l'affaire : les stocks, les
créances clients, les usines, moins les dettes fournisseurs et les charges à payer. La différence
s'appelle l'**actif d'exploitation net**, et ce qu'il rapporte s'appelle le **rendement de
l'exploitation**.

**Le second bloc est le financement.** L'argent emprunté, moins la trésorerie et les placements. La
différence s'appelle la **dette financière nette**, et ce qu'elle coûte s'appelle le **coût de la
dette**.

De là vient l'égalité de la reformulation, vraie par construction et non par estimation :

    rendement des capitaux propres = rendement de l'exploitation
                                     + levier × (rendement de l'exploitation − coût de la dette)

Elle dit que l'emprunt n'ajoute de la rentabilité que si l'exploitation rapporte plus que la dette ne
coûte, et qu'il en retire sinon. Le terme entre parenthèses s'appelle l'**écart**, et le levier est
le rapport de la dette nette aux capitaux propres.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

# Les postes du tableau de Statistique Canada, rangés selon leur usage. Ce classement est le seul
# vrai choix du dépôt, et c'est pourquoi il est écrit ici en clair plutôt que caché dans du code.
ACTIFS_FINANCIERS = [
    "Cash and deposits",
    "Total investments in non-affiliates",
    "Total loans to non-affiliates",
    "Derivative assets",
    "Reverse repurchase agreements",
]
DETTES_FINANCIERES = [
    "Total borrowings from non-affiliates",
    "Equity securities classified as liabilities",
]
ACTIFS_INTRAGROUPE = ["Total investments in and claims on parent, subsidiaries and affiliates"]
DETTES_INTRAGROUPE = ["Total amounts owing to affiliates"]

PRODUITS_FINANCIERS = ["Total interest revenue", "Total dividends"]
CHARGES_FINANCIERES = ["Total interest expense",
                       "Dividends paid on equity securities classified as liabilities"]
# Les intérêts qui portent sur les soldes entre sociétés d'un même groupe. Ils doivent suivre le
# sort du solde lui-même. Compter l'intérêt en charge financière tout en laissant la dette
# correspondante dans l'exploitation rapporterait une charge et un solde de périmètres différents,
# donc un coût de la dette qui n'est celui d'aucune dette.
PRODUITS_INTRAGROUPE = ["Interest revenue from debt claims on affiliates"]
CHARGES_INTRAGROUPE = ["Interest expense, amounts owing to affiliates"]
# Le produit des participations dans les sociétés du groupe. Il suit la même règle que les intérêts
# ci-dessus : quand le solde part au financement, son produit part avec lui. Il vaut 6 837 M$ au
# 2026-04, soit sept fois les 971 M$ d'intérêts intragroupe, donc l'oublier ne serait pas un détail.
# Une différence avec les intérêts, et elle décide du calcul : ce poste est déjà NET d'impôt. Le
# tableau vérifie « résultat après impôt + quote-part = résultat net » sur 98,86 % de ses 2 640
# lignes, à 9 M$ près au pire. Il ne passe donc pas par le facteur (1 - taux) qui répartit l'impôt
# entre exploitation et financement : le multiplier une seconde fois taxerait deux fois le même
# produit.
PRODUITS_PARTICIPATIONS = ["Equity in unconsolidated affiliates"]

TOTAL_ACTIF = "Total assets"
TOTAL_PASSIF = "Total liabilities"
TOTAL_CAPITAUX = "Total equity"
RESULTAT_NET = "Net income or loss"
RESULTAT_AVANT_IMPOT = "Income or loss before income taxes"
IMPOTS = ["Current income tax expense", "Deferred income tax expense"]
PARTICIPATIONS_MINORITAIRES = "Non-controlling interest"
ACTIONS_PRIVILEGIEES = "Preferred stocks"
CHIFFRE_AFFAIRES = "Total operating revenue"


@dataclass(frozen=True)
class Reformulation:
    """Le bilan et le résultat réécrits en deux blocs, plus les cinq grandeurs qui en découlent."""

    actif_exploitation_net: float
    dette_financiere_nette: float
    capitaux_propres: float
    resultat_exploitation: float
    charge_financiere_nette: float
    chiffre_affaires: float
    taux_impot: float
    intragroupe_actif: float
    intragroupe_passif: float

    @property
    def rendement_exploitation(self) -> float:
        """Ce que rapporte un dollar investi dans l'affaire elle-même."""
        return self.resultat_exploitation / self.actif_exploitation_net

    @property
    def cout_de_la_dette(self) -> float:
        """Ce que coûte un dollar de dette nette. Non défini quand la dette nette est nulle.

        Quand elle est négative, c'est-à-dire quand l'entreprise a plus de trésorerie et de
        placements que d'emprunts, le rapport reste calculé, mais il change de signe et ne mesure
        plus le prix d'un emprunt.
        """
        if abs(self.dette_financiere_nette) < 1e-9:
            return np.nan
        return self.charge_financiere_nette / self.dette_financiere_nette

    @property
    def levier(self) -> float:
        return self.dette_financiere_nette / self.capitaux_propres

    @property
    def ecart(self) -> float:
        return self.rendement_exploitation - self.cout_de_la_dette

    @property
    def rendement_capitaux_propres(self) -> float:
        """Ce que rapporte un dollar de capitaux propres, calculé directement."""
        return (self.resultat_exploitation - self.charge_financiere_nette) / self.capitaux_propres

    @property
    def apport_du_financement(self) -> float:
        """La part du rendement des capitaux propres qui vient de l'emprunt et non de l'affaire."""
        return self.levier * self.ecart

    @property
    def marge(self) -> float:
        return self.resultat_exploitation / self.chiffre_affaires

    @property
    def rotation(self) -> float:
        """Combien de dollars de ventes chaque dollar investi dans l'affaire fait tourner."""
        return self.chiffre_affaires / self.actif_exploitation_net

    def en_ligne(self) -> dict:
        return {
            "actif_exploitation_net": self.actif_exploitation_net,
            "dette_financiere_nette": self.dette_financiere_nette,
            "capitaux_propres": self.capitaux_propres,
            "rendement_exploitation": self.rendement_exploitation,
            "cout_de_la_dette": self.cout_de_la_dette,
            "levier": self.levier,
            "ecart": self.ecart,
            "apport_du_financement": self.apport_du_financement,
            "rendement_capitaux_propres": self.rendement_capitaux_propres,
            "marge": self.marge,
            "rotation": self.rotation,
            "taux_impot": self.taux_impot,
            "intragroupe_actif": self.intragroupe_actif,
            "intragroupe_passif": self.intragroupe_passif,
        }


def _somme(postes: pd.Series, noms: list[str]) -> float:
    """La somme de quelques postes, qui vaut NaN dès que l'un d'eux n'est pas publié.

    Le NaN est voulu. Statistique Canada n'a ouvert huit des postes utilisés ici qu'au premier
    trimestre de 2020. Les compter pour zéro avant cette date rangerait des montants réels du mauvais
    côté de la séparation, sans que rien ne le signale. Le NaN se propage donc jusqu'à l'actif
    d'exploitation net, et la ligne est écartée puis comptée par `controles`.
    """
    return float(sum(float(postes.get(nom, 0.0) or 0.0) for nom in noms))


def reformuler(postes: pd.Series, intragroupe: str = "exploitation") -> Reformulation:
    """Le bilan et le résultat d'une industrie, réécrits en deux blocs.

    Le traitement des soldes entre sociétés d'un même groupe est le point qui change tout, et il est
    laissé au choix de l'appelant. En « exploitation », ils restent là où le bilan les met, ce qui
    est la lecture brute. En « financement », ils sont sortis de l'exploitation et rangés avec la
    dette. C'est la lecture économique : un prêt d'une filiale à sa mère n'est pas un moyen de
    produire, c'est un moyen de financer.
    """
    if intragroupe not in ("exploitation", "financement"):
        raise ValueError("le traitement de l'intragroupe doit être « exploitation » ou « financement »")

    actif_total = float(postes[TOTAL_ACTIF])
    passif_total = float(postes[TOTAL_PASSIF])
    capitaux = float(postes[TOTAL_CAPITAUX])
    minoritaires = float(postes.get(PARTICIPATIONS_MINORITAIRES, 0.0) or 0.0)
    privilegiees = float(postes.get(ACTIONS_PRIVILEGIEES, 0.0) or 0.0)
    capitaux_ordinaires = capitaux - minoritaires - privilegiees

    actifs_financiers = _somme(postes, ACTIFS_FINANCIERS)
    dettes_financieres = _somme(postes, DETTES_FINANCIERES)
    intra_actif = _somme(postes, ACTIFS_INTRAGROUPE)
    intra_passif = _somme(postes, DETTES_INTRAGROUPE)
    if intragroupe == "financement":
        actifs_financiers += intra_actif
        dettes_financieres += intra_passif

    dette_nette = dettes_financieres - actifs_financiers
    actif_exploitation = (actif_total - actifs_financiers) - (passif_total - dettes_financieres)
    # les participations minoritaires et les actions privilégiées sont retirées des capitaux
    # propres : elles ne reviennent pas à l'actionnaire ordinaire, et les laisser dedans gonflerait
    # le dénominateur du rendement
    actif_exploitation -= minoritaires + privilegiees

    avant_impot = float(postes[RESULTAT_AVANT_IMPOT])
    impots = _somme(postes, IMPOTS)
    taux = impots / avant_impot if abs(avant_impot) > 1e-9 else 0.0
    taux = float(np.clip(taux, 0.0, 0.6))

    produits = _somme(postes, PRODUITS_FINANCIERS)
    charges = _somme(postes, CHARGES_FINANCIERES)
    participations = 0.0
    if intragroupe == "exploitation":
        produits -= _somme(postes, PRODUITS_INTRAGROUPE)
        charges -= _somme(postes, CHARGES_INTRAGROUPE)
    else:
        participations = _somme(postes, PRODUITS_PARTICIPATIONS)
    # la quote-part des sociétés du groupe est retranchée APRÈS le facteur d'impôt, parce que le
    # tableau la publie déjà nette ; tout le reste est avant impôt et se répartit au taux effectif
    charge_nette = (charges - produits) * (1.0 - taux) - participations
    resultat_net = float(postes[RESULTAT_NET])
    resultat_exploitation = resultat_net + charge_nette

    return Reformulation(
        actif_exploitation_net=actif_exploitation, dette_financiere_nette=dette_nette,
        capitaux_propres=capitaux_ordinaires, resultat_exploitation=resultat_exploitation,
        charge_financiere_nette=charge_nette,
        chiffre_affaires=float(postes.get(CHIFFRE_AFFAIRES, np.nan)), taux_impot=taux,
        intragroupe_actif=intra_actif, intragroupe_passif=intra_passif)


def ecart_a_l_identite(r: Reformulation) -> float:
    """De combien l'égalité de la reformulation ne se referme pas.

    Elle doit tenir exactement : le rendement calculé directement doit égaler le rendement de
    l'exploitation plus l'apport du financement. Si l'écart n'est pas nul, c'est qu'un poste a été
    compté deux fois ou oublié.

    Quand la dette nette est nulle, l'apport n'est pas fini et il n'y a rien à contrôler. La fonction
    rend alors NaN et non zéro : un zéro se confondrait avec une identité vérifiée, et le contrôle
    s'éteindrait sans bruit là où la reformulation est la plus fragile.
    """
    if not np.isfinite(r.apport_du_financement):
        return np.nan
    return r.rendement_capitaux_propres - (r.rendement_exploitation + r.apport_du_financement)
