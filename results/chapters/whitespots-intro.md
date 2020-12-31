### Lücken in der Infrastruktur erkennen
Das Ziel des folgenden Abschnitts liegt darin, Lücken in der Mobiltiätsinfrastruktur aufzuzeigen. Dabei werden die
Ebenen der Mobilitätsinfrastruktur zunächst gesondert und abschließend gemeinsam betrachtet. Um die Schwachstellen
auf in der Infrastruktur sichtbar zu machen, werden zunächst 10.000 Punkte zufällig auf der Fläche der Stadt generiert. 
Ausgenommen sind davon Wasser und Grünflächen um die grundsätzliche Erreichbarkeit der Punkte sicherzustellen.
Diese Punkte dienen als Ausgangspunkt zur Berechnung der relativen Erreichbarkeit unterschiedlicher Orte in der Stadt 
mithilfe der im vorangegangenen Abschnitt vorgestellten Isochrone. 

Für jeden der 10.000 Punkte werden alle möglichen Wege berechnet, die eine Person in einer bestimmten Zeit und einem 
bestimmten Verkehrsmittel oder einer Kombination aus verschiedenen Verkehrsmitteln zurücklegen könnte. 
Aus der Summe der Wege wird die durchschnittlich zurücklegbare Distanz für jeden Punkt errechnet. Auf diese Weise wird
die Erreichbarkeit des Punktes quantifiziert. Das bedeutet, je höher die durchschnittliche Distanz der möglichen Wege,
desto höher die Erreichbarkeit des Punktes. Anhand dieser Berechnung lässt sich die relative Erreichbarkeit über die 
gesamte Fläche der Stadt ermitteln und visualisieren. Die Visualisierung der Erreichbarkeit wird im folgenden
Abschnitt mithilfe einer Farbskala erreicht. Grün eingefärbte Hexagone signalisieren eine, im Vergleich zu
anderen Teilen des Stadtgebiets, relativ hohe Erreichbarkeit. Magentafarbene Hexagone zeigen eine im Vergleich
zu anderen Teilen des Stadtgebiets relativ geringe Erreichbarkeit. Die Farbskalierung erfolgt demnach dynamisch aus 
den vorhandenen Daten. Die absolute Erreichbarkeit kann demnach zwar nicht abgelesen werden, jedoch können vergleichsweise
schlecht angebundene Orte identifiziert werden. 