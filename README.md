# "PA jak Podjadę"

> ### Team:
> Mykhailo Marfenko
>
> Bartosz Han 
>
> Igor Matynia

## Topic and description of the project
The aim of our project is to create an application that will help users plan their trips by public transport in the Warsaw agglomeration. In particular, our application is intended to enable the traveler to:
  - Displaying timetables for a given line
  - Finding the fastest possible connection between two stops (finding the most optimal route from one point to another and directing the user accordingly)
  - Displaying a map of the stop complex selected by the user
  - Showing the delay of public transport vehicles
  - Showing a map of connections from the selected stop (showing the route of all lines that pass through the selected stop)

## Use cases

The application is intended to facilitate planning a trip by public transport, finding information about timetables, stops and departure times needed for efficient use of public transport. It will also help you find your way around large and complex sets of stops when you don't know exactly which stop you need to go to. The main task of the application is to help prepare a travel route for the user and provide him with the most important information (such as a departure table, indication of the most optimal transfer, or indication of the exact stop to go to to take a given line) so that he can freely travel and use public transport without any problems.

## Implementation assumptions and technologies

As part of this project, we created the following implementation assumptions and selected the following technologies:
- our application will be a desktop application
- we chose Python as the main programming language
- to create a user interface, we will use one of the Python libraries - PySide2
- the OracleDB database will be used to create a timetable database needed to properly provide information about public transport, and the data will be taken from the website of the Public Transport Authority in Warsaw, or from a similar interpreted text file provided by the same company.
- In order to create appropriate maps, the Google Maps or OpenStreetMap API will be used

## General application diagram
- Bus/tram/metro/stationary lines
     - -> After selecting the line, you can select the stop
         - ->The timetable is then displayed
             - ->For each hour in the timetable, you can view arrival times at other stops for a given bus
         - ->The bus stop complex can also be displayed here
         - ->Display where you can get from this place
- Searching for a connection
- Suspected delays for a given bus at a given stop at a given time

## Dependencies:

- PySide6 (https://pypi.org/project/PySide6/)
- Oracle DB (https://pypi.org/project/oracledb/)
- folium (https://pypi.org/project/folium/)
