### Lücken in der Infrastruktur erkennen
Aufbauend auf dem Grundverständnis der Berliner Verkehrsinfrastruktur, gilt es nun **Lücken in der Verkehrsinfrastruktur 
aufzuzeigen**. Dabei werden die **Ebenen der Verkehrsinfrastruktur zunächst gesondert und abschließend gemeinsam 
betrachtet**. Um die Schwachstellen in der Infrastruktur sichtbar zu machen, werden zunächst **10.000 Punkte generiert 
und zufällig im Stadtgebiet verteilt**. Lediglich Wasser- und Grünflächen sind ausgenommen, um die grundsätzliche 
Erreichbarkeit der Punkte sicherzustellen. **Diese Punkte dienen als Ausgangspunkt zur Berechnung der relativen 
Erreichbarkeit** unterschiedlicher Orte in der Stadt mithilfe der im vorangegangenen Abschnitt vorgestellten Isochronen. 

**Für jeden der 10.000 Punkte werden alle möglichen Wege berechnet, die eine Person in einer bestimmten Zeit und einem 
bestimmten Verkehrsmittel oder einer Kombination aus verschiedenen Verkehrsmitteln zurücklegen könnte**. Aus der Summe 
der Wege wird die durchschnittlich zurücklegbare Distanz für jeden Punkt ermittelt. Auf diese Weise wird die 
Erreichbarkeit des Punktes quantifiziert. Das bedeutet, je höher die durchschnittliche Distanz der möglichen Wege, 
desto höher die Erreichbarkeit des Punktes.

Anhand dieser Berechnung lässt sich die relative Erreichbarkeit über die gesamte Fläche der Stadt ermitteln und 
visualisieren. Dafür werden Punkte die nah aneinander liegen zu Flächen (Hexagone) zusammengefasst. Ausgehend von der 
durchschnittlichen Erreichbarkeit aller Punkte in einem Hexagon, wird dieses entlang einer Farbskala eingefärbt. 
**Grün eingefärbte Hexagone signalisieren eine, im Vergleich zu anderen Teilen des Stadtgebiets, relativ hohe 
Erreichbarkeit. Magentafarbene Hexagone zeigen eine, im Vergleich zu anderen Teilen des Stadtgebiets, relativ geringe 
Erreichbarkeit**. Die Farbskalierung erfolgt demnach dynamisch aus den vorhandenen Daten. Die absolute Erreichbarkeit 
kann demnach zwar nicht abgelesen werden, jedoch können vergleichsweise schlecht angebundene Orte identifiziert werden.
