"""La reformulation, vérifiée sur ses identités et sur un bilan construit à la main."""

import numpy as np
import pandas as pd
import pytest

from efr.donnees import COLONNE_INDUSTRIE, COLONNE_POSTE, identite_du_bilan
from efr.noms import FRANCAIS, etiquette, francais
from efr.panel import ENSEMBLE, controles, moyennes_par_industrie, panel, verdict
from efr.reformulation import Reformulation, ecart_a_l_identite, reformuler


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


# La lecture nette du bilan d'essai annule exactement la dette nette, ce qui est le sujet de
# test_la_dette_nette_se_calcule_a_la_main. L'apport de l'emprunt y vaut alors NaN et l'écart à
# l'identité n'est pas défini, donc l'identité doit se contrôler sur un bilan dont la dette nette
# reste non nulle dans les deux lectures. Cent de créances sur le groupe au lieu de deux cents
# laissent 250 plus 50 moins 100 moins 100, soit 100.
_CREANCES_GROUPE = "Total investments in and claims on parent, subsidiaries and affiliates"
CAS_IDENTITE = {"exploitation": {}, "financement": {_CREANCES_GROUPE: 100.0}}


def test_l_identite_de_la_reformulation_tient_exactement():
    """L'égalité qui porte tout : le rendement des capitaux propres doit être exactement le
    rendement de l'exploitation plus l'apport de l'emprunt. Ce n'est pas une approximation."""
    for mode, remplacements in CAS_IDENTITE.items():
        r = reformuler(_bilan(**remplacements), mode)
        assert np.isfinite(r.apport_du_financement), "sinon l'écart ne contrôle rien"
        assert ecart_a_l_identite(r) == pytest.approx(0.0, abs=1e-12)


def test_l_ecart_a_l_identite_rend_nan_quand_il_n_y_a_rien_a_controler():
    """Quand la dette nette est nulle, l'apport de l'emprunt n'est pas défini. Rendre zéro ferait
    passer une ligne non contrôlée pour une identité vérifiée."""
    r = reformuler(_bilan(), "financement")
    assert r.dette_financiere_nette == pytest.approx(0.0)
    assert np.isnan(ecart_a_l_identite(r))


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
    """Le défaut trouvé en route : l'intérêt du groupe était compté en charge financière alors que la
    dette correspondante restait dans l'exploitation. En lecture brute, la charge nette exclut donc
    les 5 payés et les 3 reçus au sein du groupe. Il reste 20 moins 2, soit 18 avant impôt et
    14,4 après."""
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


def _reformulation(actif, dette, capitaux, resultat, charge) -> Reformulation:
    """Une reformulation posée directement, pour contrôler les cinq grandeurs sur des nombres
    choisis hors du code plutôt que recalculés par lui."""
    return Reformulation(actif_exploitation_net=actif, dette_financiere_nette=dette,
                         capitaux_propres=capitaux, resultat_exploitation=resultat,
                         charge_financiere_nette=charge, chiffre_affaires=1000.0, taux_impot=0.2,
                         intragroupe_actif=0.0, intragroupe_passif=0.0)


def test_l_apport_de_l_emprunt_vaut_le_levier_fois_l_ecart_sur_des_nombres_choisis():
    """Actif d'exploitation net 750, égal à 150 de dette nette plus 600 de capitaux propres, qui
    rapporte 37,50, soit 5 %. La dette nette coûte 6,90, soit 4,6 %. Le levier vaut 150 sur 600, soit
    0,25, et l'écart 0,4 point, donc l'apport vaut 0,1 point. Le rendement des capitaux propres
    ressort à 30,60 sur 600, soit 5,1 %, ce qui est bien 5 % plus 0,1 point."""
    r = _reformulation(750.0, 150.0, 600.0, 37.5, 6.9)
    assert r.rendement_exploitation == pytest.approx(0.05)
    assert r.cout_de_la_dette == pytest.approx(0.046)
    assert r.levier == pytest.approx(0.25)
    assert r.ecart == pytest.approx(0.004)
    assert r.apport_du_financement == pytest.approx(0.001)
    assert r.rendement_capitaux_propres == pytest.approx(0.051)
    assert ecart_a_l_identite(r) == pytest.approx(0.0, abs=1e-12)


def test_un_levier_negatif_retourne_le_signe_de_l_apport_sans_toucher_a_l_ecart():
    """Une entreprise qui a plus de trésorerie que d'emprunts a une dette nette négative. Actif
    d'exploitation net 450, égal à moins 150 plus 600, qui rapporte 22,50, soit les mêmes 5 %. L'écart
    reste 0,4 point et l'apport change de signe, donc le rendement des capitaux propres tombe à
    4,9 %."""
    negatif = _reformulation(450.0, -150.0, 600.0, 22.5, -6.9)
    assert negatif.rendement_exploitation == pytest.approx(0.05)
    assert negatif.ecart == pytest.approx(0.004)
    assert negatif.levier == pytest.approx(-0.25)
    assert negatif.apport_du_financement == pytest.approx(-0.001)
    assert negatif.rendement_capitaux_propres == pytest.approx(0.049)
    assert ecart_a_l_identite(negatif) == pytest.approx(0.0, abs=1e-12)


def test_l_emprunt_ajoute_du_rendement_quand_l_exploitation_rapporte_plus_qu_il_ne_coute():
    """Le sens de l'égalité : l'apport de l'emprunt est positif si et seulement si l'exploitation
    rapporte plus que la dette ne coûte, le levier du bilan d'essai valant 150 sur 600."""
    r = reformuler(_bilan(), "exploitation")
    assert r.levier > 0
    assert (r.apport_du_financement > 0) == (r.ecart > 0)


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
    borné entre zéro et soixante pour cent plutôt que laissé courir. Les trois cas touchent les deux
    bornes et le milieu, sans quoi la borne haute ne serait vérifiée par rien."""
    perte = reformuler(_bilan(**{"Income or loss before income taxes": -10.0,
                                 "Net income or loss": -8.0}), "exploitation")
    assert perte.taux_impot == pytest.approx(0.0)
    ecrete = reformuler(_bilan(**{"Income or loss before income taxes": 10.0,
                                  "Current income tax expense": 15.0}), "exploitation")
    assert ecrete.taux_impot == pytest.approx(0.6)
    assert reformuler(_bilan(), "exploitation").taux_impot == pytest.approx(0.2)


def test_l_identite_du_bilan_est_verifiable_directement():
    assert identite_du_bilan(_bilan()) == pytest.approx(0.0)
    assert identite_du_bilan(_bilan(**{"Total equity": 500.0})) == pytest.approx(100.0)


def test_les_quarante_industries_ont_leur_nom_francais():
    """Les noms ne sont pas traduits mais recopiés de la version française du même tableau."""
    assert len(FRANCAIS) == 40
    assert francais("Warehousing [493]") == "Entreposage"
    assert francais("Telecommunications [517]") == "Télécommunications"
    assert francais("inconnue") == "inconnue"
    # l'étiquette d'une figure se replie entre deux mots, jamais au milieu d'un mot
    replie = etiquette("Motor vehicle and trailer manufacturing", 24, 2)
    assert replie == "Fabrication de véhicules\nautomobiles et de\u2026"
    assert all(len(bout) <= 25 for bout in replie.split("\n"))
    assert etiquette("Warehousing [493]") == "Entreposage"


def test_le_cout_de_la_dette_n_a_pas_de_sens_quand_la_dette_nette_est_nulle():
    """La lecture nette peut annuler la dette nette. Le rapport de la charge à zéro n'est alors pas
    un coût de la dette, et la fonction le dit au lieu de rendre l'infini."""
    r = reformuler(_bilan(**{"Total borrowings from non-affiliates": 300.0,
                             "Total amounts owing to affiliates": 0.0,
                             "Cash and deposits": 100.0,
                             "Total investments in and claims on parent, subsidiaries and affiliates":
                                 200.0}), "financement")
    assert np.isnan(r.cout_de_la_dette)


def test_le_produit_des_participations_suit_le_solde_du_groupe():
    """Le pendant du test précédent, du côté des participations. Le produit des participations dans
    les sociétés du groupe reste dans l'exploitation tant que le solde y reste, et part au
    financement avec lui. Dix de produit en plus allègent la charge financière nette de dix moins
    l'impôt de 20 %, soit huit, dans la seule lecture nette."""
    avec = {"Equity in unconsolidated affiliates": 10.0, _CREANCES_GROUPE: 100.0}
    sans = {_CREANCES_GROUPE: 100.0}
    net_avec = reformuler(_bilan(**avec), "financement")
    net_sans = reformuler(_bilan(**sans), "financement")
    assert net_avec.charge_financiere_nette == pytest.approx(net_sans.charge_financiere_nette - 8.0)
    brut_avec = reformuler(_bilan(**avec), "exploitation")
    brut_sans = reformuler(_bilan(**sans), "exploitation")
    assert brut_avec.charge_financiere_nette == pytest.approx(brut_sans.charge_financiere_nette)


def _table_longue(periodes, industries, absents_par_periode=None) -> pd.DataFrame:
    """Le bilan d'essai mis en forme longue, comme le tableau de Statistique Canada.

    Les créances sur le groupe valent 100 et non 200, pour que la dette nette reste non nulle dans
    les deux lectures. Sinon l'écart à l'identité vaudrait NaN et le contrôle ne contrôlerait rien.

    `absents_par_periode` retire un poste d'une période donnée, ce qui reproduit le seul défaut de
    couverture du tableau réel : un poste ouvert en cours de route.
    """
    absents_par_periode = absents_par_periode or {}
    lignes = []
    for periode in periodes:
        for industrie in industries:
            for poste, valeur in _bilan(**{_CREANCES_GROUPE: 100.0}).items():
                if poste in absents_par_periode.get(periode, ()):
                    continue
                lignes.append({"REF_DATE": periode, COLONNE_INDUSTRIE: industrie,
                               COLONNE_POSTE: poste, "VALUE": valeur, "UOM": "Dollars"})
    return pd.DataFrame(lignes)


def test_le_panel_annualise_en_multipliant_le_trimestre_par_quatre():
    """Le tableau est trimestriel et un rendement trimestriel ne se compare à rien. Sur le bilan
    d'essai, le résultat des capitaux propres vaut 60 moins 14,4 de charge financière nette, sur 600,
    soit 10 % par trimestre et donc 40 % par an."""
    detail = panel(_table_longue(["2024-01"], ["A"]), "exploitation")
    ligne = detail.iloc[0]
    assert ligne["rendement_capitaux_propres_pct"] == pytest.approx(40.0)
    assert ligne["marge_pct"] == pytest.approx(9.3)
    assert ligne["rotation"] == pytest.approx(800.0 / 750.0 * 4.0)


def test_la_part_du_passif_due_au_groupe_est_une_part_et_non_un_montant():
    """50 dus au groupe sur 400 de passif font 12,5 %. Le montant est publié à côté, sous un nom qui
    dit qu'il est en millions."""
    ligne = panel(_table_longue(["2024-01"], ["A"]), "exploitation").iloc[0]
    assert ligne["part_intragroupe_passif_pct"] == pytest.approx(12.5)
    assert ligne["intragroupe_passif_millions"] == pytest.approx(50.0)


def test_le_panel_couvre_tous_les_trimestres_du_tableau_quand_les_postes_sont_publies():
    """Le contrôle qui manquait : deux industries sur trois trimestres font six lignes, et aucune ne
    doit disparaître en silence."""
    table = _table_longue(["2024-01", "2024-04", "2024-07"], ["A", "B"])
    detail = panel(table, "exploitation")
    assert len(detail) == 6
    assert detail["periode"].nunique() == 3
    assert controles(table)["lignes_ecartees"].tolist() == [0, 0]


def test_un_poste_ouvert_en_cours_de_route_ecarte_la_ligne_et_le_controle_le_compte():
    """Huit postes du tableau réel ne sont publiés qu'à partir de 2020. La ligne qui les précède
    n'est pas calculable, et le nombre de lignes écartées doit se lire dans les contrôles plutôt que
    de disparaître."""
    table = _table_longue(["2024-01", "2024-04"], ["A", "B"],
                          absents_par_periode={"2024-01": ("Total interest revenue",)})
    detail = panel(table, "exploitation")
    assert detail["periode"].unique().tolist() == ["2024-04"]
    controle = controles(table)
    assert controle["lignes_ecartees"].tolist() == [2, 2]
    assert controle["periode_min"].tolist() == ["2024-04", "2024-04"]
    assert controle["lignes_non_controlees"].tolist() == [0, 0]


def test_le_verdict_compte_les_industries_ou_l_emprunt_domine():
    """« L'emprunt domine » veut dire que son apport pèse plus, en valeur absolue, que le rendement
    de l'affaire. Sur trois industries fabriquées, une seule est dans ce cas, et l'ensemble est exclu
    du compte."""
    moyenne = pd.DataFrame({
        "industrie": ["A", "B", "C", ENSEMBLE],
        "apport_du_financement_pct": [2.0, -1.0, -9.0, 5.0],
        "rendement_exploitation_pct": [10.0, 8.0, 6.0, 9.0],
        "rendement_capitaux_propres_pct": [12.0, 7.0, -3.0, 14.0],
        "part_du_financement_pct": [16.0, -14.0, 300.0, 35.0],
    })
    v = verdict(moyenne)
    assert v["industries"] == 3
    assert v["financement_positif"] == 1
    assert v["financement_dominant"] == 1
    assert v["apport_median_pct"] == pytest.approx(-1.0)
    assert v["exploitation_mediane_pct"] == pytest.approx(8.0)


def test_les_moyennes_portent_la_fenetre_qu_elles_couvrent():
    """La figure des industries lit ses bornes de période ici plutôt que de les écrire en dur."""
    moyenne = moyennes_par_industrie(panel(_table_longue(["2024-01", "2024-04"], ["A"]),
                                           "exploitation"))
    assert moyenne["trimestres"].tolist() == [2]
    assert moyenne["periode_min"].tolist() == ["2024-01"]
    assert moyenne["periode_max"].tolist() == ["2024-04"]
