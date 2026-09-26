# p-Center – wie weit ist der Weiteste noch weg? – Streamlit-Demo

*(noch nicht deployed)*

Drittes Stück der **Standortplanungs-Linie** der "Konzepte"-Reihe für die Website "Sebastian Hanisch – Operations Research und Machine Learning", Kind von [standortplanung-demo](https://github.com/sebastian-hanisch/standortplanung-demo) (Standortproblem ohne Kapazität):
anders als die Fall-Demos im Portfolio (ein Anwendungsfall, mehrere Verfahren im Vergleich) zeigt diese Demo **ein** Modell – das **p-Center-Problem (Minimax-Standortplanung)** – an einem wachsenden Beispiel.
Bisher war das Ziel der Standortwahl eine **Summe**. Hier zählt nur der **Weiteste**: von n Punkten werden p zu Mittelpunkten, jeder Punkt geht zum nächsten, und gesucht ist die Auswahl, bei der der **größte Abstand** (der Radius) möglichst klein ist.
Das genaue Optimum ist leicht zu berechnen (Binärsuche über den Radius mit einer Überdeckungsrechnung). Das klassische einfache Verfahren, **Farthest-first** (Gonzalez 1985), hat eine **Garantie**: nie mehr als das Doppelte des Optimums. Die Demo zeigt, was von dieser Garantie in der Praxis übrig bleibt, wie stark der **Startpunkt** wirkt, wie die **Swap-Lokalsuche** nachbessert und was der **Preis der Fairness** gegenüber der Summen-Lösung (p-Median) ist.

**Einordnung in die Reihe (die Kanten des Graphen):** Kind von `standortplanung-demo` (dasselbe Standortgerüst, andere Zielfunktion: Maximum statt Summe); Kontrast zur [kapazitierten Standortplanung](https://github.com/sebastian-hanisch/kapazitierte-standortplanung-demo) (Summe, Lagrange) und zur [k-Means-Demo](https://github.com/sebastian-hanisch/kmeans-demo) (k-Medoids wird dort nur erklärt, nicht gerechnet; das p-Median rechnet diese Demo als exakten Vergleich); Nachbar `ems_demo` (Überdeckung mit Verfügbarkeit, Fall-Demo). Ein k-Center gab es im Portfolio bisher nicht.
```
standortplanung-demo (UFL, Wurzel: Summe der Kosten)                                    [gebaut]
  ├─ kapazitierte-standortplanung-demo (Kapazität + Single-Sourcing, Lagrange)           [gebaut]
  ├─ p-center-demo (Maximum statt Summe: Farthest-first, exakt per Überdeckung)          [dieses Stück]
  ├─ p-Hub-Median                                                                        [geplant]
  ├─ Wettbewerbsstandort                                                                 [geplant]
  └─ Standort + Bestand (Risk Pooling)                                                   [geplant]
```

## Ergebnis (Zahlen aus den Tests)

Jede hier genannte Zahl ist in `tests/test_claims.py` belegt: Lehrnetze von Hand, Beispielnetze über ihre Seeds, Verteilungen über feste Netze (Seeds ab 100000: 40 Netze für die Verteilung, 20 je p der Reihe und im Ausreißer-Test). Standard: 50 gleichverteilte Punkte, p = 5, Seed 1, Farthest-first ab Punkt 1. Die **Mittelpunkte sind Punkte der Menge** (nur dafür gilt die Garantie 2).
Abstände sind ganzzahlig (Zehntel-Einheiten, abgerundet), also sind alle Radien und Summen ganze Zahlen und auf allen Plattformen dieselben; angezeigt werden sie durch 10 geteilt (Karteneinheiten). Nur die Überdeckungs-LP ist ein Gleitkommawert; sie wird als ganzzahliger LP-Radius (kleinster Radius mit zulässiger LP) gezählt. Nie gezählt wird, welche der gleich guten Auswahlen der Löser liefert.

**Standardnetz.** Der **Optimalradius** ist **28,4** (der LP-Radius ebenfalls). **Farthest-first** ab Punkt 1 kommt nach 1 bis 5 Mittelpunkten auf die Radien 96,8 / 81,6 / 65,0 / 48,6 / **42,6**, das ist das **1,50-Fache** des Optimums. Die **Swap-Lokalsuche** ab diesem Ergebnis endet bei 32,6 (4 Züge, Summe 843,9), nur mit dem Radius als Kriterium ebenfalls bei 32,6 (2 Züge).
Der **Startpunkt** entscheidet: der beste (Punkt 25) liefert 36,0, der schlechteste (Punkt 22) 48,6. Die p-Median-Lösung (Summe 795,9) hat den Radius 35,3; die p-Center-Lösung mit der kleinsten Summe unter den Optima kostet 856,2, die Farthest-first-Lösung 1 029,0.

**Die Garantie 2 ist eine Obergrenze, die Praxis liegt bei 1,4 bis 1,5.** 40 gleichverteilte Netze (50 Punkte, p = 5): Farthest-first (Start Punkt 1) im Mittel **1,415-fach** des Optimalradius (Median 1,441, schlechtestes Netz 1,718), **nie exakt**; mit dem besten Startpunkt je Netz **1,199-fach** (schlechtestes 1,458), ebenfalls nie exakt; mit dem schlechtesten Startpunkt 1,633 (bis 1,804). In 40 Clusternetzen (p = 4): 1,491 (bis 1,826), bester Start 1,293, schlechtester 1,665 (bis 1,923). Die Garantie 2 wird in keinem Netz verletzt.
Über p (20 Netze je p = 1 / 2 / 3 / 5 / 8): Start Punkt 1 im Mittel 1,495 / 1,407 / 1,482 / 1,446 / 1,372; bester Start 1,000 / 1,151 / 1,148 / 1,215 / 1,163 – bei p = 1 ist der beste Startpunkt der beste Mittelpunkt.

**Die Garantie wird erreicht.** Lehrnetz (7 Punkte, p = 2): Farthest-first ab Punkt 1 endet bei 16,0, das Optimum {Punkt 3, Punkt 6} hat den Radius 8,0: **genau das Doppelte**. Der beste Startpunkt (Punkt 6) trifft das Optimum, die Swap-Lokalsuche findet es nach einem Zug.

**Swap-Lokalsuche.** Über die 40 gleichverteilten Netze **1,045-fach** (schlechtestes 1,196, exakt in **15** Netzen, im Mittel 7,1 Züge) mit dem Summen-Kriterium als zweitem Schlüssel gegen **1,120** (schlechtestes 1,357, exakt in 8, 3,7 Züge) mit dem Radius allein: auf den Plateaus, auf denen viele Tausche den Radius nicht ändern, bleibt die Suche ohne den zweiten Schlüssel stehen. In den Clusternetzen 1,021 (exakt in 30) gegen 1,141 (exakt in 17).
Kein einheitlicher Gewinner: im Cluster-Beispiel (50 Punkte, p = 4, Optimalradius 16,1) endet die Suche mit Summe bei 18,6, nur mit dem Radius bei 16,1. Lehrnetz „steckt fest“ (8 Punkte, p = 3): Farthest-first ab Punkt 1 endet bei 10,0, kein einzelner Tausch senkt Radius oder Summe, das Optimum ist 6,0 (bester Startpunkt: Punkt 5).

**Preis der Fairness.** Die p-Median-Lösung (Summe minimal) hat im Mittel den **1,276-fachen** Optimalradius (schlechtestes Netz 1,614), die p-Center-Lösung (unter den Radius-Optima die mit der kleinsten Summe) die **1,079-fache** Summe (schlechtestes 1,187). Über p = 1 / 2 / 3 / 5 / 8: Radius der Median-Lösung 1,045 / 1,185 / 1,217 / 1,271 / 1,347, Summe der Center-Lösung 1,008 / 1,057 / 1,049 / 1,074 / 1,073: moderat, in beide Richtungen.
Lehrnetz „Summe gegen Maximum“ (9 Punkte, p = 2): das p-Center-Optimum hat den Radius 9,2 bei der Summe 46,8, das p-Median-Optimum die Summe 37,5, aber den Radius 19,6 (2,13-fach).

**Die Überdeckungs-LP ist praktisch exakt.** Der LP-Radius trifft den Optimalradius in 40 von 40 gleichverteilten und 40 von 40 Clusternetzen; über p in 20 / 20 / 20 / 20 / 19 von 20 Netzen (das Muster der Wurzel: mit starker Kopplung ist die LP fast exakt).

**Ausreißer.** Ein zusätzlicher Punkt bei (150, 150), weit außerhalb der Karte (p = 4, 20 Netze): der Optimalradius steigt im Mittel auf das **1,251-Fache** (1,122 bis 1,380), die p-Median-Kosten auf das **1,120-Fache** (1,097 bis 1,154): der Radius reagiert stärker, weil der Ausreißer ihn direkt bestimmt, aber nicht in einer anderen Größenordnung. Voreinstellung *Ein Ausreißer* (51 Punkte, p = 4): Optimalradius 41,1, Farthest-first 65,0, Swap mit Summe 41,1, nur mit Radius 47,4.

**Mittelpunkt frei statt auf einem Punkt (p = 1).** Der kleinste umschließende Kreis (Welzl) hat einen kleineren Radius als der beste Punkt als Mittelpunkt: im Mittel über 40 Netze ist der Punkt-Mittelpunkt **1,073-fach** so weit (größtes Verhältnis 1,171; das kleinste, 0,999, entsteht nur durch das Abrunden der Abstände auf Zehntel).

**Voreinstellungen.** *Ein Mittelpunkt* (p = 1): Optimalradius 60,5, Farthest-first ab Punkt 1 96,8 (1,60-fach), bester Startpunkt (Punkt 13) trifft das Optimum, Swap nach einem Zug. *Großes Netz* (80 Punkte, p = 8): Optimalradius 21,4, Farthest-first 29,1 (1,36-fach), Swap erreicht das Optimum nach 8 Zügen, bester Start 25,6.

## Was nicht funktioniert hat / Vorab-Hypothesen

Vor dem Bau standen mehrere Vermutungen im Plan (Modellprüfung der Erweiterung E3). Gemessen:

- **„p-Center reagiert viel stärker auf einen Ausreißer als die Summe“ – nur teilweise.** Radius ×1,251 gegen p-Median-Kosten ×1,120: stärker, aber nicht dramatisch. (Eine erste Vorprüfung mit dem Ausreißer bei (250, 250) hatte ×1,27 gegen ×1,19 ergeben: der Unterschied hängt von der Lage ab und ist nie groß.)
- **„Die Heuristik trifft das Optimum meistens“ – widerlegt.** Farthest-first ab Punkt 1 ist in 40 gleichverteilten Netzen nie exakt, auch der beste Startpunkt nicht; erst die Swap-Lokalsuche kommt nahe (exakt in 15 von 40).
- **„Der Startpunkt ist nebensächlich“ – widerlegt.** Bester gegen schlechtester Startpunkt: 1,199 gegen 1,633 im Mittel, bis 1,804 im schlechtesten Netz.
- **„Das Summen-Kriterium beim Tauschen ist überflüssig“ – widerlegt (im Mittel).** Mit dem Radius allein bleibt die Suche auf Plateaus stehen (1,120 gegen 1,045); im Einzelfall (Cluster-Beispiel) hilft der Radius allein sogar mehr.
- **„Die Überdeckungs-LP ist eine schwache Schranke“ – widerlegt.** Der LP-Radius ist in 80 von 80 Netzen gleich dem Optimum.
- **„Ein exaktes p-Center-Verfahren ist schwer“ – nicht in dieser Größe.** Binärsuche plus Überdeckungs-MILP löst alle Netze bis 80 Punkte; die Näherung ist hier ein Lehrstück über Garantien, kein Bedarf.
- **Bestätigt:** die Garantie 2 wird nie verletzt und im Lehrnetz genau erreicht; der Preis der Fairness ist in beide Richtungen moderat.

## Grenzen (was die Demo nicht zeigt)

Mittelpunkte sind Punkte der Menge (kontinuierliches p-Center nur für p = 1 als Kreis), keine Kapazitäten, keine Gewichte, Luftlinie mit auf Zehntel abgerundeten Abständen, keine Verfügbarkeit (siehe `ems_demo`), erzeugte Netze ohne Fremddaten; die Lehrnetze sind Konstruktionen.
Die Einheit „bewertete Tausche“ ist eine Zählung, keine Uhr.

## Dateien

| Datei | Inhalt |
|---|---|
| `app.py` | Streamlit-Oberfläche: Selbst probieren, Farthest-first Schritt für Schritt, Wie gut ist das?, Preis der Fairness, Experimente auf Abruf |
| `pc_scenario.py` | Netze (gleichverteilt, Cluster), Ausreißer, Lehrnetze, SplitMix64-Zufallsstrom (Kopie aus den Vorgängern) |
| `pc_algorithms.py` | Farthest-first (Startpunkt wählbar, Trace), Swap-Lokalsuche (mit und ohne Summen-Kriterium) |
| `pc_exact.py` | HiGHS: Optimalradius per Binärsuche + Überdeckung, LP-Radius, billigste Auswahl bei optimalem Radius, p-Median, Brute Force |
| `pc_circle.py` | kleinster umschließender Kreis (p = 1, Mittelpunkt frei) |
| `pc_evaluation.py`, `pc_visualization.py` | Vergleiche, Reihen, Verteilungen, Ausreißer- und Kreis-Test; Karte, Radiusverlauf, Balken |
| `pc_presets.py`, `pc_constants.py` | Presets, Permalink, Regler-Grenzen, feste Seeds |
| `tests/` | 297 Tests: Szenario, Algorithmen (Garantie 2 über alle Startpunkte), Exakt gegen Brute Force, Kreis, Presets, Zahlen (`test_claims.py`), App |

Lokal starten: `pip install -r requirements.txt`, dann `streamlit run app.py`; Tests: `pip install -r requirements-dev.txt`, dann `python -m pytest tests`.
