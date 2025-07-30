import json, typing, re
from dataclasses import dataclass
from typing import Optional
from . import Products
from datetime import datetime



class Serializable:
    def __str__(self):
        return json.dumps(self.__dict__, default=self._default, indent=4, ensure_ascii=False)
    
    def __repr__(self):
        return self.__str__()
    
    @staticmethod
    def _default(o):
        if isinstance(o, datetime):
            return o.isoformat()
        try:
            return o.__dict__
        except AttributeError:
            return str(o)
    
@dataclass
class Location(Serializable):
    latitude: str
    longitude: str

@dataclass
class BaseNamedStop(Serializable):
    evaNumber: Optional[str] = None
    name: Optional[str] = None
    canceled: Optional[bool] = None
    additional: Optional[bool] = None
    separation: Optional[bool] = None
    slug: Optional[str] = None
    displayPriority: Optional[int] = None
    nameParts: Optional[list] = None

    def __post_init__(self):
        self.id = self.evaNumber


class StopPlace(BaseNamedStop): pass

class Destination(BaseNamedStop): pass

class Stop(BaseNamedStop): pass

class Message(Serializable):
    def __init__(self, text = "", type = "", change = "", important: bool = False, **kwargs):
        self.text: str = text
        self.type: str = type
        self.change: bool = change
        self.important: bool = important


class DepArrBase(Serializable):
    def __init__(self, bahnhofsId = "", zeit = "", ezZeit="", gleis = "", ezGleis = "", ueber = [], journeyId = "", verkehrmittel = {'mittelText': ""}, terminus = "", meldungen = [], **kwargs):
        self.station_id = bahnhofsId
        self.time: datetime = datetime.fromisoformat(zeit)
        self.time_delayed: datetime = datetime.fromisoformat(ezZeit) if ezZeit else None
        self.planed_platform = gleis
        self.platform = ezGleis
        self.via: typing.List[str] = ueber
        self.journey_id: str = journeyId
        self.line_name: str = verkehrmittel['mittelText']
        self.end_station: str = terminus

class Departure(DepArrBase): ...

class Arrival(DepArrBase): ...



class Station(Serializable):
    def __init__(self, name: str, id: str, lid: str, lat: str = "", lon: str = "", products: list = [], stopover_time: int = 0, **kwargs):
        self.name: str = name
        self.id: str = id
        self.lid: str = lid
        self.stopover_time: int = stopover_time
        self.location: Location = Location(lat, lon)
        self.products: typing.List[Products] = products

class Operator(Serializable):
    def __init__(self, code, hatShop, kuerzel, description, logo, shortDescription, **kwargs):
        self.id: int = int(code)
        self.has_shop: bool = hatShop
        self.code: str = kuerzel
        self.description: str = description
        self.logo: str = logo
        self.short_description: str = shortDescription

class J_StopOver(Serializable):
    def __init__(self, id, abfahrtsZeitpunkt = None, ezAbfahrtsZeitpunkt = None, ankunftsZeitpunkt = None, ezAnkunftsZeitpunkt = None, auslastungsmeldungen = None, gleis = None, ezGleis = None, haltTyp = None, name = None, risNotizen = None, bahnhofsInfoId = None, extId = None, himMeldungen = None, **kwargs):
        self.id = id
        self.departure_time: str = abfahrtsZeitpunkt
        self.arrival_time: str = ankunftsZeitpunkt
        #self.auslastungsmeldungen = auslastungsmeldungen # Кол. Людей
        self.platform: str = gleis
        #self.haltTyp: str = haltTyp
        self.station_name: str = name
        #self.risNotizen: list = risNotizen
        #self.bahnhofsInfoId: str = bahnhofsInfoId
        self.station_id: str = extId
        #self.himMeldungen = himMeldungen
        #self.routeIdx = routeIdx
        #self.priorisierteMeldungen = priorisierteMeldungen

class J_means_of_transport(Serializable):
    def __init__(self, name = None, nummer = None, richtung = None, zugattribute = None, kurzText = None, mittelText = None, langText = None, **kwargs):
        self.name: str = name
        self.transport_way_id: str = nummer
        self.direction: str = richtung
        self.info: list = zugattribute
        self.short_name: str = kurzText
        self.middle_name: str = mittelText
        self.full_name: str = langText

class Connection(Serializable):
    """
    Represents a leg of a journey, containing details such as departure and arrival times and stations,
    the means of transport used, and a list of intermediate stopovers.

    Attributes:
        departure_time (str): Scheduled departure time.
        arrival_time (str): Scheduled arrival time.
        departure_station (str): Name of the departure station.
        arrival_station (str): Name of the arrival station.
        stopovers (List[J_StopOver]): Intermediate stops during the connection.
        journeyId (str): Identifier for the journey leg.
        means_of_transport (J_means_of_transport): Transport method used for the connection.
    """
    def __init__(self, risNotizen = None, himMeldungen = None, priorisierteMeldungen = None, externeBahnhofsinfoIdOrigin = None, externeBahnhofsinfoIdDestination = None, abfahrtsZeitpunkt = None, ezAbfahrtsZeitpunkt = None, abfahrtsOrt = None, abfahrtsOrtExtId = None, abschnittsDauer = None, ezAbschnittsDauerInSeconds = None, abschnittsAnteil = None, ankunftsZeitpunkt = None, ezAnkunftsZeitpunkt = None, ankunftsOrt = None, ankunftsOrtExtId = None, auslastungsmeldungen = None, halte = None, idx = None, journeyId = None, verkehrsmittel = None, iceSprinterNote = None, **kwargs):
        #self.risNotizen = risNotizen
        #self.himMeldungen = himMeldungen
        #self.priorisierteMeldungen = priorisierteMeldungen
        #self.externeBahnhofsinfoIdOrigin = externeBahnhofsinfoIdOrigin
        #self.externeBahnhofsinfoIdDestination = externeBahnhofsinfoIdDestination
        self.departure_time: str = abfahrtsZeitpunkt
        self.departure_station: str = abfahrtsOrt
        #self.iceSprinterNote = iceSprinterNote
        #self.abfahrtsOrtExtId = abfahrtsOrtExtId
        #self.abschnittsDauer = abschnittsDauer
        #self.abschnittsAnteil = abschnittsAnteil
        #self.ezAbschnittsDauerInSeconds = ezAbschnittsDauerInSeconds
        self.arrival_time: str = ankunftsZeitpunkt
        self.arrival_station: str = ankunftsOrt
        #self.ankunftsOrtExtId = ankunftsOrtExtId
        #self.auslastungsmeldungen = auslastungsmeldungen
        self.stopovers: typing.List[J_StopOver] = [J_StopOver(**stop) for stop in halte] if halte else []
        #self.idx = idx
        self.journeyId: str = journeyId
        self.means_of_transport: J_means_of_transport = J_means_of_transport(**verkehrsmittel)


class Journey(Serializable):
    """
    Represents a full journey from a departure station to a destination, including all connections.

    Attributes:
        trip_lid (str): Context-based ID for this journey.
        changes_amont (int): Number of transfers during the journey.
        departure_name (str): Name of the departure station.
        arrival_name (str): Name of the destination station.
        connections (List[Connection]): List of connections (legs) within the journey.
        journey_time_in_seconds (int): Estimated journey duration in seconds.
        is_alternative_connection (bool): Whether this is an alternative route.
        preis (str): Ticket price, if available.
    """
    def __init__(self, tripId = None, ctxRecon = None, verbindungsAbschnitte = None, umstiegsAnzahl = None, verbindungsDauerInSeconds = None, ezVerbindungsDauerInSeconds = None, isAlternativeVerbindung = None, auslastungsmeldungen = None, auslastungstexte = None, himMeldungen = None, risNotizen = None, priorisierteMeldungen = None, reservierungsMeldungen = None, isAngebotseinholungNachgelagert = None, isAlterseingabeErforderlich = None, serviceDays = None, angebotsPreis = None, angebotsPreisKlasse = None, hasTeilpreis = None, reiseAngebote = None, hinRueckPauschalpreis = None, isReservierungAusserhalbVorverkaufszeitraum = None, gesamtAngebotsbeziehungList = None, ereignisZusammenfassung = None, meldungen = None, meldungenAsObject = None, angebotsInformationen = None, angebotsInformationenAsObject = None, **kwargs):
        #self.tripId: str = tripId
        self.link: str = ""
        self.trip_lid: str = ctxRecon
        self.changes_amont: int = umstiegsAnzahl
        self.departure_name: str = verbindungsAbschnitte[0]['abfahrtsOrt']
        self.arrival_name: str = verbindungsAbschnitte[-1]['ankunftsOrt']
        self.connections: typing.List[Connection] = [Connection(**stop) for stop in verbindungsAbschnitte] if verbindungsAbschnitte else []
        self.departure_time: str = self.connections[0].departure_time
        self.arrival_time: str = self.connections[-1].arrival_time
        self.journey_time_in_seconds: int = verbindungsDauerInSeconds
        #self.journey_time_in_seconds_e: int = ezVerbindungsDauerInSeconds
        self.is_alternative_connection: bool = isAlternativeVerbindung
        #self.auslastungsmeldungen = auslastungsmeldungen
        self.auslastungstexte = auslastungstexte # MARK: КОЛ. ЛЮДЕЙ
        #self.himMeldungen = himMeldungen
        #self.risNotizen = risNotizen
        #self.priorisierteMeldungen = priorisierteMeldungen
        #self.reservierungsMeldungen = reservierungsMeldungen
        self.meldungen: typing.List[str] = meldungen
        #self.meldungenAsObject = meldungenAsObject
        #self.isAngebotseinholungNachgelagert: bool = isAngebotseinholungNachgelagert
        #self.isAlterseingabeErforderlich: bool = isAlterseingabeErforderlich
        #self.serviceDays = serviceDays
        self.preis = str(angebotsPreis['betrag']) + " " + angebotsPreis['waehrung'] if angebotsPreis else None
        #self.angebotsPreisKlasse: str = angebotsPreisKlasse
        #self.hasTeilpreis: bool = hasTeilpreis
        #self.reiseAngebote = reiseAngebote
        #self.angebotsInformationen = angebotsInformationen
        #self.angebotsInformationenAsObject = angebotsInformationenAsObject
        #self.hinRueckPauschalpreis: bool = hinRueckPauschalpreis
        #self.isReservierungAusserhalbVorverkaufszeitraum: bool = isReservierungAusserhalbVorverkaufszeitraum
        #self.gesamtAngebotsbeziehungList = gesamtAngebotsbeziehungList
    
    def get_db_link(self):
        """Returns a link compatible with `DB Navigator` and [int.bahn.de](https://int.bahn.de) """
        return self.link

if __name__ == "__main__":
    raise RuntimeError("This module is not intended to be run or imported directly.")
