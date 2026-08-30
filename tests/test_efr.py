"""La reformulation, vérifiée sur ses identités et sur un bilan construit à la main."""

import numpy as np
import pandas as pd
import pytest

from efr.donnees import identite_du_bilan
from efr.noms import FRANCAIS, francais
from efr.reformulation import ecart_a_l_identite, reformuler


def _bilan(**remplacements) -> pd.Series:
    """Un bilan minuscule, dont chaque nombre est choisi pour que le résultat se calcule de tête.

    Actif 1 000, dont 100 de trésorerie et 200 de créances sur le groupe. Passif 400, dont 250
    d'emprunts et 50 dus au groupe. Capitaux propres 600. Résultat net 60, dont 25 d'intérêts payés
    et 5 reçus, impôt de 20 % du résultat avant impôt.
    """
    postes = {
        "Total assets": 1000.0, "Total liabilities": 400.0, "Total equity": 600.0,
        "Cash and deposits": 100.0,
        "Total investments in and claims on parent, subsidiaries and affiliates": 200.0,
        "Total borrowings from non-affiliates": 250.0,
        "Total amounts owing to affiliates": 50.0,
        "Total interest expense": 25.0, "Interest expense, amounts owing to affiliates": 5.0,
        "Total interest revenue": 5.0, "Interest revenue from debt claims on affiliates": 3.0,
        "Net income or loss": 60.0, "Income or loss before income taxes": 75.0,
        "Current income tax expense": 15.0, "Deferred income tax expense": 0.0,
        "Total operating revenue": 800.0, "Non-controlling interest": 0.0, "Preferred stocks": 0.0,
    }
    postes.update(remplacements)
    return pd.Series(postes)


def test_l_identite_de_la_reformulation_tient_exactement():
    """L'égalité qui porte tout : le rendement des capitaux propres doit être exactement le
    rendement de l'exploitation plus l'apport de l'emprunt. Ce n'est pas une approximation."""
    for mode in ("exploitation", "financement"):
        r = reformuler(_bilan(), mode)
        assert ecart_a_l_identite(r) == pytest.approx(0.0, abs=1e-12)


def test_le_bilan_se_referme_dans_la_reformulation():
    """L'actif d'exploitation net doit égaler la dette financière nette plus les capitaux propres,
    sans quoi un poste a été compté deux fois ou oublié."""
    for mode in ("exploitation", "financement"):
        r = reformuler(_bilan(), mode)
        assert (r.actif_exploitation_net - r.dette_financiere_nette
                - r.capitaux_propres) == pytest.approx(0.0, abs=1e-9)


def test_la_dette_nette_se_calcule_a_la_main():
    """En lecture brute : 250 d'emprunts moins 100 de trésorerie font 150. En lecture nette, les
    50 dus au groupe s'ajoutent et les 200 de créances sur le groupe se retranchent, ce qui donne
    250 plus 50 moins 100 moins 200, soit zéro."""
    assert reformuler(_bilan(), "exploitation").dette_financiere_nette == pytest.approx(150.0)
    assert reformuler(_bilan(), "financement").dette_financiere_nette == pytest.approx(0.0)


def test_les_interets_du_groupe_suivent_le_solde_du_groupe():
    """Le défaut trouvé en route : compter l'intérêt du groupe en charge financière tout en laissant
    la dette correspondante dans l'exploitation faisait apparaître un coût de la dette de seize pour
    cent là où il en vaut six. En lecture brute, la charge nette exclut donc les 5 payés et les 3
    reçus au sein du groupe, ce qui laisse 20 moins 2, soit 18 avant impôt et 14,4 après."""
    r = reformuler(_bilan(), "exploitation")
    assert r.taux_impot == pytest.approx(0.20)
    assert r.charge_financiere_nette == pytest.approx((25.0 - 5.0 - (5.0 - 3.0)) * 0.8)


def test_le_rendement_ne_depend_pas_du_traitement_du_groupe():
    """C'est le contrôle le plus fort : le rendement des capitaux propres est un fait comptable, il
    ne peut pas changer selon la façon dont on range les postes. Seule sa décomposition change."""
    brut = reformuler(_bilan(), "exploitation")
    net = reformuler(_bilan(), "financement")
    assert brut.rendement_capitaux_propres == pytest.approx(net.rendement_capitaux_propres)
    assert brut.rendement_exploitation != pytest.approx(net.rendement_exploitation)


def test_l_emprunt_ajoute_du_rendement_quand_l_exploitation_rapporte_plus_qu_il_ne_coute():
    """Le sens de l'égalité : l'apport de l'emprunt est le levier fois l'écart, donc il est positif
    si et seulement si l'exploitation rapporte plus que la dette ne coûte."""
    r = reformuler(_bilan(), "exploitation")
    assert (r.apport_du_financement > 0) == (r.ecart > 0)
    assert r.apport_du_financement == pytest.approx(r.levier * r.ecart)


def test_un_traitement_inconnu_du_groupe_est_refuse():
    with pytest.raises(ValueError, match="exploitation"):
        reformuler(_bilan(), "au-choix")


def test_les_participations_minoritaires_sortent_des_capitaux_propres():
    """Elles ne reviennent pas à l'actionnaire ordinaire : les laisser dedans gonflerait le
    dénominateur et ferait paraître le rendement plus faible qu'il n'est."""
    sans = reformuler(_bilan(), "exploitation")
    avec = reformuler(_bilan(**{"Non-controlling interest": 100.0}), "exploitation")
    assert avec.capitaux_propres == pytest.approx(sans.capitaux_propres - 100.0)
    assert ecart_a_l_identite(avec) == pytest.approx(0.0, abs=1e-12)


def test_le_taux_d_impot_reste_dans_des_bornes_raisonnables():
    """Une industrie qui perd de l'argent produit un rapport d'impôt sur résultat aberrant : il est
    borné entre zéro et soixante pour cent plutôt que laissé courir."""
    perte = reformuler(_bilan(**{"Income or loss before income taxes": -10.0,
                                 "Net income or loss": -8.0}), "exploitation")
    assert 0.0 <= perte.taux_impot <= 0.6


def test_l_identite_du_bilan_est_verifiable_directement():
    assert identite_du_bilan(_bilan()) == pytest.approx(0.0)
    assert identite_du_bilan(_bilan(**{"Total equity": 500.0})) == pytest.approx(100.0)


def test_les_quarante_industries_ont_leur_nom_francais():
    """Les noms ne sont pas traduits mais recopiés de la version française du même tableau."""
    assert len(FRANCAIS) == 40
    assert francais("Warehousing [493]") == "Entreposage"
    assert francais("Telecommunications [517]") == "Télécommunications"
    assert francais("inconnue") == "inconnue"


def test_le_cout_de_la_dette_n_a_pas_de_sens_quand_la_dette_nette_est_nulle():
    """La lecture nette peut annuler la dette nette. Le rapport de la charge à zéro n'est alors pas
    un coût de la dette, et la fonction le dit au lieu de rendre l'infini."""
    r = reformuler(_bilan(**{"Total borrowings from non-affiliates": 300.0,
                             "Total amounts owing to affiliates": 0.0,
                             "Cash and deposits": 100.0,
                             "Total investments in and claims on parent, subsidiaries and affiliates":
                                 200.0}), "financement")
    assert np.isnan(r.cout_de_la_dette)
