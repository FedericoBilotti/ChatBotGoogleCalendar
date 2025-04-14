import os

from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import BatchHttpRequest

from datetime import datetime, timezone, timedelta
from dateparser import parse
from dotenv import load_dotenv

from app.services.i_singleton import ISingleton

class GoogleCalendarServiceController(ISingleton):
    MAX_EVENTS_SHOW = 7
    SCOPES: list[str] = ["https://www.googleapis.com/auth/calendar"]
    __instance = None

    def __init__(self):
        if GoogleCalendarServiceController.__instance is not None:
            raise Exception("Singleton was instanciated!")

        else:
            load_dotenv()
            developer_key: str | None = os.getenv("DEVELOPER_KEY")
            
            if developer_key is None:
                raise Exception("Developer key not found")

            self.developer_key = developer_key
            self.calendar_id = "primary"
            creds = self._get_credentials("token.json")
            self.service = build(
                "calendar",
                "v3",
                credentials=creds,
                developerKey=self.developer_key,
            )

            GoogleCalendarServiceController.__instance = self

    @staticmethod
    def get_instance():
        if GoogleCalendarServiceController.__instance == None:            
            GoogleCalendarServiceController.__instance = GoogleCalendarServiceController()

        return GoogleCalendarServiceController.__instance

    # ----------- Public methods -----------

    def get_events(self, max_events: int, target_dt: datetime, max_dt: datetime) -> str:
        """Obtain the next "n" events asked by the user, between two dates."""
        events = []
        total_events_to_show = max_events        
        if total_events_to_show > self.MAX_EVENTS_SHOW:
            total_events_to_show = self.MAX_EVENTS_SHOW
        
        additional_days_added = ""

        if max_dt is None:            
            DAYS_ADDED = 7
            additional_days_added = additional_days_added.join(f"Al no especificar una fecha, se añadieron {DAYS_ADDED} días a la busqueda.")
            max_dt = target_dt + timedelta(days=DAYS_ADDED) 

        try:
            events_result = (
                self.service.events()
                .list(
                    calendarId=self.calendar_id,
                    timeMin=target_dt,
                    timeMax=max_dt,
                    maxResults=total_events_to_show,
                    singleEvents=True,
                    orderBy="startTime",
                )
                .execute()
            )

            events = events_result.get("items", [])

            if not events:
                return "No hay eventos"

        except HttpError as error:
            return f"Error al traer eventos {error}"

        return additional_days_added.join(f"\nEventos obtenidos: {events}")

    def add_event(self, event_data: dict) -> str:
        start_datetime: str | None  = event_data.get("start_datetime", None)
        end_datetime: str | None = event_data.get("end_datetime", None)
        description: str | None = event_data.get("description", None)
        
        if start_datetime == None: 
            return f"Error al crear evento. El diccionario no tiene fecha inicial en sus claves."

        if description == None:
            return f"Error al crear evento. El diccionario no tiene descripción en sus claves."

        event_body = {
            "summary": event_data.get("description"),
            "start": {
                "dateTime": start_datetime,
                "timeZone": "America/Argentina/Buenos_Aires"
            },
            "end": {
                "dateTime": end_datetime,
                "timeZone": "America/Argentina/Buenos_Aires"
            }
        }

        try:            
            self.service.events().insert(calendarId=self.calendar_id, body=event_body).execute()
            
            return f"Evento creado el {start_datetime} y finaliza el {end_datetime}, descripción: {description}"

        except HttpError as error:
            return "Error al crear evento"

    def delete_events(self, target_dt: datetime, end_dt: datetime) -> str:        
        events = self._find_events_in_range(target_dt, end_dt)
        if not events:
            return f"No encontré ningún entre {target_dt} y {end_dt}"
        
        self._delete_events_by_id(events)
        return "Evento eliminado"

    # ----------- Private methods -----------

    def _find_events_in_range(self, target_dt: datetime, end_dt: datetime) -> list[str] | list[None]:
        """Search all events in a range of days.
        Args:
            target_dt (datetime): The date to search.
            end_dt (datetime): The end date to search.

        Returns: list[str] | list[None]: The ids of the events found or None."""

        time_min = target_dt
        time_max = end_dt if end_dt != None else (time_min + timedelta(days=1))

        try:
            events_result = (
                self.service.events()
                    .list(
                        calendarId=self.calendar_id,
                        timeMin=time_min.isoformat(),
                        timeMax=time_max.isoformat(),
                        singleEvents=True,
                        orderBy="startTime"
                    )
                    .execute()
            )
        except HttpError as error:
            raise Exception(f"An error occurred: {error}")
        
        return events_result.get("items", [])

    def _delete_events_by_id(self, events) -> str:
        try:
            if list is None:
                return "No se encontraron eventos para eliminar"

            for event in events:
                self.service.events().delete(
                        calendarId = self.calendar_id, 
                        eventId = event["id"]
                    ).execute()

            return "Eventos eliminados"
            
        except Exception as e:
            return f"Error al eliminar evento {str(e)}"

    def _get_credentials(self, token_path: str) -> Credentials | None:
        try:
            current_dir = os.path.dirname(os.path.abspath(__file__))
            credentials_path = os.path.join(current_dir, "credentials.json")

            if os.path.exists(token_path) == None:
                return None
            
            creds = Credentials.from_authorized_user_file(token_path, self.SCOPES)

            if not creds or not creds.valid:
                if creds and creds.expired and creds.refresh_token:
                    creds.refresh(Request())
                else:
                    flow = InstalledAppFlow.from_client_secrets_file(
                        credentials_path, self.SCOPES
                    )
                    creds = flow.run_local_server(port=0)

                with open(token_path, "w") as token:
                    token.write(creds.to_json())
        except HttpError as e:
            raise Exception("An error occurred: %s" % e)

        return creds  # type: ignore