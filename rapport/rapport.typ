#set document(title: "Les entreprises canadiennes gagnent leur argent en vendant, pas en empruntant", author: "Guillaume Vaudescal")
#set page(
  paper: "a4",
  margin: (x: 2.2cm, y: 2.4cm),
  numbering: "1 / 1",
  footer: context [
    #set text(size: 8pt, fill: luma(90))
    #grid(columns: (1fr, auto), align: (left, right),
      [etats-financiers], [#counter(page).display("1 / 1", both: true)])
  ],
)
#set text(font: ("Helvetica", "Arial", "DejaVu Sans"), size: 10pt, lang: "fr")
#set par(justify: true, leading: 0.68em, spacing: 1.1em)
#set heading(numbering: none)
#show heading.where(level: 2): it => block(above: 1.6em, below: 0.8em, text(size: 13pt, it))
#show heading.where(level: 3): it => block(above: 1.2em, below: 0.6em, text(size: 11pt, it))
#show raw.where(block: true): it => block(
  fill: luma(246), inset: 8pt, radius: 3pt, width: 100%, text(size: 8.5pt, it))
#show raw.where(block: false): it => text(size: 9pt, fill: rgb("#1a3f66"), it)
#show quote.where(block: true): it => block(
  inset: (left: 10pt), stroke: (left: 1.5pt + luma(180)),
  text(style: "italic", fill: luma(45), it.body))
// la table NE DOIT PAS être enfermée dans un par() : Typst 0.15 la supprime alors
// entièrement, sans erreur. Le réglage se pose donc dans la portée du bloc.
#show table: it => block(above: 1.1em, below: 1.1em,
  [#set par(justify: false); #text(size: 8.8pt, it)])
#show figure: it => block(above: 1.4em, below: 1.4em, it)
#show figure.caption: it => text(size: 8.5pt, fill: luma(70), it)
#show link: it => text(fill: rgb("#0072B2"), it)

#align(center)[
  #block(width: 100%)[
    #text(size: 18pt, weight: "bold")[Les entreprises canadiennes gagnent leur argent en vendant, pas en empruntant]
    #v(0.6em)
    #text(size: 10pt, fill: luma(70))[Guillaume Vaudescal · 2026-08-30 · #link("https://github.com/Guilou001/28-etats-financiers-reformules")[Guilou001/28-etats-financiers-reformules]]
  ]
]
#v(1.2em)
#line(length: 100%, stroke: 0.6pt + luma(190))
#v(0.8em)

Quand une entreprise rapporte de l'argent à ses propriétaires, deux explications sont possibles. Soit elle vend bien ce qu'elle fabrique. Soit elle a beaucoup emprunté, et l'argent emprunté lui rapporte plus qu'il ne lui coûte. Ce n'est pas la même chose : la première explication tient dans la durée, la seconde se retourne dès que les taux montent. Ce dépôt sépare les deux, sur toutes les entreprises non financières du Canada.

*Résultat en une phrase.* Sur 66 trimestres et 39 industries, l'affaire elle-même rapporte *11,5 %* par an en médiane, et l'emprunt n'ajoute qu'entre *+0,18 et −0,98 point* selon la façon de traiter les soldes entre sociétés d'un même groupe ; autrement dit *entre 1,5 % et −7 % du rendement*, et jamais davantage.

_Summary in English. A Nissim-Penman reformulation of Statistics Canada's quarterly aggregate balance sheet and income statement (table 33-10-0225, 327 360 rows, 66 quarters, 40 industries), separating operating from financing returns. Operating return is 11.5 % a year at the median; the contribution of leverage is between +0.18 and −0.98 points depending on how intercompany balances are treated, which is 1.5 % to −7 % of return on equity. Both accounting identities hold to machine precision on all 1 040 industry-quarters._

== 1. La question posée

*En mots simples.* Une entreprise qui rapporte 12 % par an à ses actionnaires : d'où viennent ces 12 % ? Le bilan publié ne le dit pas, parce qu'il range les actifs par nature et non par usage. La trésorerie y côtoie les usines, et la dette bancaire y côtoie les factures à payer aux fournisseurs.

Reformuler, c'est réécrire ce bilan en deux blocs. D'un côté ce qu'il faut pour faire tourner l'affaire : les stocks, les créances clients, les usines, moins les dettes fournisseurs. De l'autre l'argent emprunté, moins la trésorerie et les placements.

De là vient une égalité *vraie par construction*, et non estimée :

#quote(block: true)[rendement des capitaux propres = rendement de l'affaire + levier × (rendement de l'affaire − coût de la dette)]

Elle dit que l'emprunt n'ajoute de la rentabilité que si l'affaire rapporte plus que la dette ne coûte, et qu'il en retire sinon.

== 2. D'où vient le projet, et ce qu'il apporte

La méthode vient de Doron Nissim et Stephen Penman, qui l'ont posée en 2001 sur des entreprises américaines cotées. Elle est enseignée partout et appliquée société par société. Elle ne l'avait pas été sur le panneau officiel canadien.

Trois apports.

- *Une reformulation complète du bilan agrégé canadien*, industrie par industrie et trimestre par

trimestre, soit 1 040 calculs.

- *Deux lectures des soldes entre sociétés d'un même groupe*, publiées côte à côte parce qu'elles

changent le signe du verdict pour quatre industries sur les quatorze les plus concernées.

- *Deux identités vérifiées à la machine* sur chaque ligne, plutôt qu'un résultat affirmé.

== 3. Les données

Le tableau 33-10-0225 de Statistique Canada donne le bilan et le compte de résultat agrégés des entreprises non financières du pays. Mesuré le 30 août 2026 : *327 360 lignes*, 66 trimestres de janvier 2010 à avril 2026, 40 industries, 122 postes, 63 536 828 octets une fois décompressé. Licence ouverte de Statistique Canada, usage et redistribution permis avec attribution ; rien n'est redistribué ici.

Les noms d'industries qui s'affichent ne sont pas traduits : ils sont recopiés de la version française du même tableau.

== 4. La méthode, pas à pas

+ *Vérifier que le bilan se referme.* L'actif moins le passif moins les capitaux propres doit valoir zéro. Mesuré : l'écart maximal sur les 1 040 lignes vaut *1 million de dollars*, c'est-à-dire l'arrondi de publication sur des montants de neuf mille milliards.
+ *Ranger chaque poste* selon son usage, financier ou d'exploitation. C'est le seul vrai choix du dépôt, et il est écrit en clair dans le code plutôt que caché.
+ *Sortir les participations minoritaires et les actions privilégiées* des capitaux propres : elles ne reviennent pas à l'actionnaire ordinaire.
+ *Répartir l'impôt* entre exploitation et financement, au taux effectif de chaque industrie.
+ *Vérifier la seconde identité.* Le rendement calculé directement doit égaler le rendement de l'affaire plus l'apport de l'emprunt. Mesuré : l'écart maximal vaut *2 × 10⁻⁵ point*.

== 5. Les résultats

=== 5.1 D'où vient le rendement de l'ensemble des entreprises canadiennes

Au dernier trimestre publié, avril 2026.

#table(
  columns: 6,
  stroke: (x, y) => if y == 0 { (bottom: 0.6pt) } else { none },
  align: left + top,
  inset: 5pt,
    [*Lecture*],
    [*L'affaire rapporte*],
    [*Coût de la dette*],
    [*Levier*],
    [*L'emprunt ajoute*],
    [*Total*],
    [Soldes du groupe laissés dans l'exploitation],
    [11,46 %],
    [5,64 %],
    [0,221],
    [*+1,29 point*],
    [12,75 %],
    [Soldes du groupe comptés comme du financement],
    [13,02 %],
    [non interprétable],
    [0,078],
    [*−0,27 point*],
    [12,75 %],
)

Comment lire ce tableau, en trois constats. Le premier est que la colonne de droite est la même dans les deux lignes, et c'est normal : le rendement des capitaux propres est un fait comptable, seule sa décomposition dépend du rangement. Le deuxième est que l'emprunt pèse *10,1 % du rendement* dans la première lecture et *−2,1 %* dans la seconde : dans les deux cas, c'est l'affaire qui fait presque tout. Le troisième est que le coût de la dette de la seconde lecture n'est pas interprétable, et le dépôt le déclare : en compensant une créance de 1 806 milliards par une dette de 1 290 milliards, on divise des intérêts bruts par un solde net presque nul, ce qui produit un rapport sans signification.

#figure(image("../results/figures/decomposition.png", width: 100%), caption: [La décomposition du rendement, dans les deux lectures])

Comment lire cette figure : la première barre est ce que l'affaire rapporte, la deuxième est ce que l'emprunt y ajoute ou en retire, la troisième est le total. Les deux volets aboutissent au même total et se distinguent seulement par le rangement des soldes entre sociétés d'un même groupe.

=== 5.2 Le même calcul sur 39 industries et 66 trimestres

#table(
  columns: 7,
  stroke: (x, y) => if y == 0 { (bottom: 0.6pt) } else { none },
  align: left + top,
  inset: 5pt,
    [*Lecture*],
    [*Industries*],
    [*L'emprunt ajoute*],
    [*L'emprunt domine*],
    [*Apport médian*],
    [*Part du rendement*],
    [*L'affaire rapporte*],
    [Soldes dans l'exploitation],
    [39],
    [21],
    [*0*],
    [+0,18 point],
    [0,26 %],
    [11,55 %],
    [Soldes en financement],
    [39],
    [14],
    [*1*],
    [−0,98 point],
    [−7,39 %],
    [13,15 %],
)

Comment lire ce tableau, en trois constats. Le premier est la colonne « l'emprunt domine » : dans la première lecture, *aucune* des 39 industries ne tire de l'emprunt plus que de son affaire, et une seule le fait dans la seconde. Le deuxième est que l'apport médian est petit dans les deux sens, de +0,18 à −0,98 point sur un rendement de 11 à 13 % : le levier est un ajustement, pas un moteur. Le troisième est que le nombre d'industries pour lesquelles l'emprunt ajoute du rendement passe de 21 à 14 selon la lecture, ce qui est exactement la raison de publier les deux.

#figure(image("../results/figures/industries.png", width: 100%), caption: [Chaque industrie, son affaire et ce que l'emprunt y ajoute])

Comment lire cette figure : un point par industrie, moyenne des 66 trimestres. L'axe vertical est en échelle logarithmique symétrique, parce qu'une industrie tombe à −22 points et écraserait les trente-huit autres sur une échelle ordinaire. Les points au-dessus de la ligne sont les industries où l'emprunt paie.

#figure(image("../results/figures/deux_lectures.png", width: 100%), caption: [La même industrie lue deux fois])

Comment lire cette figure : deux barres par industrie, une par lecture. Sur les quatorze industries les plus concernées, *quatre changent de signe* selon le traitement des soldes du groupe. C'est la limite honnête du résultat, et elle est publiée plutôt que cachée.

=== 5.3 Un quart du passif est de l'argent dû à son propre groupe

#figure(image("../results/figures/intragroupe.png", width: 100%), caption: [La part du passif due au groupe, trimestre par trimestre])

Comment lire cette figure : la part du passif total qui est de l'argent dû à une société du même groupe. Elle passe de *29,8 % au premier trimestre de 2010 à 24,6 % au dernier*, sans jamais descendre sous ce dernier niveau. Ce n'est pas une dette envers l'extérieur : c'est un jeu d'écritures entre une mère et ses filiales. Toute mesure de levier qui l'ignore surestime l'endettement réel des entreprises canadiennes, et c'est pourquoi le dépôt publie les deux lectures au lieu d'en choisir une.

== 6. Reproduire

#raw("uv sync --locked --all-extras\nuv run pytest                 # 12 tests fermés, sans réseau\nuv run efr fetch              # le tableau de Statistique Canada, 63 Mo\nuv run efr tout               # les trois calculs et les quatre figures", block: true, lang: "bash")

Les tests ne touchent jamais le réseau : ils tournent sur un bilan minuscule dont chaque nombre est choisi pour que le résultat se calcule de tête. Tous les chiffres de ce README viennent des fichiers de #raw("results/").

== 7. Limites, avec leur statut

#table(
  columns: 2,
  stroke: (x, y) => if y == 0 { (bottom: 0.6pt) } else { none },
  align: left + top,
  inset: 5pt,
    [*Limite*],
    [*Statut*],
    [Le rangement des postes entre exploitation et financement est un choix],
    [déclaré ; les listes sont en tête du module de reformulation, lisibles et modifiables],
    [Le traitement des soldes entre sociétés d'un même groupe change le signe du verdict pour 4 industries sur 14],
    [mesuré ; les deux lectures sont publiées côte à côte],
    [Le coût de la dette de la lecture nette n'est pas interprétable],
    [déclaré ; son dénominateur est presque nul, alors que le produit levier fois écart, lui, reste juste],
    [Les données sont agrégées par industrie, non par entreprise],
    [reconnu ; une industrie qui mêle des sociétés très endettées et des sociétés sans dette donne une moyenne qui ne décrit aucune des deux],
    [Soixante-six trimestres ne portent qu'un choc de taux et une récession],
    [déclaré ; le verdict se pose par industrie, sur 2 574 observations en coupe, et non par époque],
    [L'impôt est réparti au taux effectif de l'industrie, borné entre 0 et 60 %],
    [déclaré ; une industrie en perte produit sinon un taux aberrant],
    [Les dividendes reçus sont comptés comme un produit financier],
    [déclaré ; pour une société de portefeuille, ils seraient de l'exploitation, et ce cas n'est pas distingué],
)

== 8. Crédits, licence, citation

Données de Statistique Canada, tableau 33-10-0225, sous licence ouverte, avec attribution. Méthode d'après Doron Nissim et Stephen Penman, _Ratio Analysis and Equity Valuation: From Research to Practice_, Review of Accounting Studies, 2001. Code sous licence MIT, rapport sous licence CC BY 4.0. Figures produites par #link("https://github.com/Guilou001/gv-fintools")[gv-fintools].

Voisinage dans le portefeuille : #link("https://github.com/Guilou001/09-valorisation-entreprise")[09-valorisation-entreprise] fait le même travail sur une seule société, le Canadien National, et va jusqu'au prix de l'action. Celui-ci reste au niveau de l'industrie et ne valorise rien. Le rapport #raw("rapport/rapport.pdf") est engendré depuis ce README.
