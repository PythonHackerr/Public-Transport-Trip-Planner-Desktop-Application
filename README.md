# Projekt PAP - zespół 14

## "PA jak Podjadę"

> ### Skład zespołu:
> Bartosz Han 318658
>
> Mykhailo Marfenko 323558
>
> Igor Matynia 318693

>Prowadzący zespołu: Michał Chwesiuk

## Temat i opis projektu
Celem naszego projektu jest stworzenie aplikacji, która ma pomóc użytkownikowi w planowaniu swoich podróży komunikacją miejską w aglomeracji warszawskiej. W szczególności, nasza aplikacja ma umożliwić podróżnemu:
 - Wyświetlenie rozkładów jazdy dla danej linii
 - Wyszukanie jak najszybszego połączenia pomiędzy dwoma przystankami (znalezienie najoptymalniejszej trasy z jednego punktu do drugiego i odpowiednie pokierowanie użytkownika)
 - Wyświetlenie mapy wybranego przez użytkownika zespołu przystankowego
 - Pokazywanie opóźnienia pojazdów komunikacji publicznej
 - Pokazanie mapy połączeń z wybranego przystanku (pokazanie trasy wszystkich linii, które przejeżdżają przez wybrany przystanek)

## Przypadki użytkowania

Aplikacja ma na celu ułatwienie planowania podróży komunikacją miejską, wyszukiwanie informacji o rozkładach, przystankach czy czasach odjazdów, potrzebnych do sprawnego poruszania się transportem publicznym. Pomoże także w orientacji na rozległych i skomplikowanych zespołach przystanków, gdy nie wiadomo na który dokładnie przystanek trzeba się udać. Głównym zadaniem aplikacji jest pomoc w przygotowaniu trasy podróży dla użytkownika, oraz przekazanie mu najważniejszych informacji (takich jak tabela odjazdów, wskazanie najoptymalniejszej przesiadki, czy wskazanie, na który dokładnie przystanek należy się udać, aby pojechać daną linią) tak, aby podczas podróży mógł swobodnie i bez żadnych problemów posługiwać się komunikacją miejską.

## Założenia realizacji i technologie

W ramach tego projektu, stworzyliśmy nastepujące założenia realizaji i wybraliśmy następujące technologie:
- nassza aplikacja będzie aplikacją desktopową
- jako główny język programowania wybraliśmy język Python
- w celu stworzenia interfeju użytkownika zastosujemy jedną z bibliotek to Pythona - PySide2
- do stworzenia bazy danych rozkładowych potrzebnych do prawidłowego przekazywania informacji o transporcie publicznym zostanie wykorzystana baza danych OracleDB, a dane będą wzięte ze strony Zarządu Transportu Miejskiego w Warszawie, lub z analogicznego interpretowanego pliku tekstowego udostępnianego przez tą samą spółkę.
- W celu tworzenia odpowiednich map, zostanie wykorzystane api do map Google lub OpenStreetMap

## Ogólny schemat aplikacji
- Linie autobusowe/tramwajowe/metra/skm
    - -> Po wyborze linii, można wybrać przystanek
        - ->Wyświetla się wtedy rozkład jazdy
            - ->Dla każdej godziny w rozkładzie można podejrzeć czasy przyjazdu na inne przystanki dla danego autobusu
        - ->W tym miejscu można też wyświetlić zespół przystankowy
        - ->Wyświetlanie gdzie można dojechać z tego miejsca
- Szukanie połączenia
-  Podejrzenie spóźnień dla danego autobusu na danym przystanku o danej porze

## Dependencies:

- PySide6 (https://pypi.org/project/PySide6/)
- Oracle DB (https://pypi.org/project/oracledb/)
- folium (https://pypi.org/project/folium/)