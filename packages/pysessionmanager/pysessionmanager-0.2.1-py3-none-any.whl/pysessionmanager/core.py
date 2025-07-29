import datetime
import json
from typing import Dict, Literal, Optional
import csv
import sqlite3
import psycopg2
import logging as log # type: ignore
from pysessionmanager.codes import SessionMessages  # Ensure this import is correct and the module exists
from .security import generate_session_id, hash_password, verify_password
from .utils import get_default_unick_name
# this class is only example class to help as writing a new class
# for storing sessions in different formats
# it is not used in the main code
class SessionStoring:
    def __init__(self, filename: str = "sessions.json", db_name: str = "sessions.db"):
        self.filename = filename
        self.db_name = db_name
        self.logging = False


    def store_sessions_json(self, sessions: Dict[str, Dict], filename: str = "sessions.json", logging: bool = False):
        sessions_to_save = {
            session_id: {
                "unick_name": session["unick_name"],
                "start_time": session["start_time"].isoformat(),
                "end_time": session["end_time"].isoformat(),
                "protected": session["protected"],
                "password": session.get("password"),
                "value": session.get("value"),
            }
            for session_id, session in sessions.items()
        }
        with open(filename, 'w') as f:
            json.dump(sessions_to_save, f)
            if logging or self.logging:
                log.info(SessionMessages.sessions_as_json_added_message(filename)[0])
        return SessionMessages.sessions_as_json_added_message(filename)[1]

    def store_sessions_csv(self, sessions: Dict[str, Dict], filename: str = "sessions.csv"):
        with open(filename, mode='w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(["session_id", "unick_name", "start_time", "end_time", "protected", "password", "value"])
            for session_id, session in sessions.items():
                writer.writerow([
                    session_id,
                    session["unick_name"],
                    session["start_time"].isoformat(),
                    session["end_time"].isoformat(),
                    session["protected"],
                    session["password"],
                    session.get("value", "")
                ])

    def load_sessions_csv(self, csv_filename: str = "sessions.csv") -> Dict[str, Dict]:
        sessions = {}
        try:
            with open(csv_filename, mode='r') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    sessions[row["session_id"]] = {
                        "unick_name": row["unick_name"],
                        "start_time": datetime.datetime.fromisoformat(row["start_time"]),
                        "end_time": datetime.datetime.fromisoformat(row["end_time"]),
                        "protected": row["protected"] == 'True',
                        "password": row["password"],
                        "value": row["value"] if row["value"] else None
                    }
        except FileNotFoundError:
            return {}
        return sessions

    def store_sessions_sqlite(self, filename:str="sessions.db" ,sessions: Dict[str, Dict]=None):
        conn = sqlite3.connect(self.db_name if not filename else filename)
        cursor = conn.cursor()
        cursor.execute("""CREATE TABLE IF NOT EXISTS sessions (
            session_id TEXT PRIMARY KEY,
            unick_name TEXT,
            start_time TEXT,
            end_time TEXT,
            protected INTEGER,
            password TEXT,
            value TEXT
        )""")
        cursor.execute('DELETE FROM sessions')
        for session_id, session in sessions.items():
            cursor.execute('''INSERT INTO sessions VALUES (?, ?, ?, ?, ?, ?, ?)''', (
                session_id,
                session["unick_name"],
                session["start_time"].isoformat(),
                session["end_time"].isoformat(),
                int(session["protected"]),
                session["password"],
                session.get("value", None),
            ))
        conn.commit()
        conn.close()

    def load_sessions_sqlite(self, filename:str="sessions.db") -> Dict[str, Dict]:
        sessions = {}
        conn = sqlite3.connect(self.db_name if not filename else filename)
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM sessions')
        for row in cursor.fetchall():
            sessions[row[0]] = {
                "unick_name": row[1],
                "start_time": datetime.datetime.fromisoformat(row[2]),
                "end_time": datetime.datetime.fromisoformat(row[3]),
                "protected": bool(row[4]),
                "password": row[5],
                "value": row[6] if len(row) > 6 else None
            }
        conn.close()
        return sessions

    def store_sessions_postgresql(self, filename:str="sessions.db", sessions: Dict[str, Dict]=None, conn_string:str=None):
        if not conn_string:
            raise ValueError("Connection string is required for PostgreSQL.")
        conn = psycopg2.connect(conn_string)
        cursor = conn.cursor()
        cursor.execute('''CREATE TABLE IF NOT EXISTS sessions (
            session_id TEXT PRIMARY KEY,
            unick_name TEXT,
            start_time TEXT,
            end_time TEXT,
            protected BOOLEAN,
            password TEXT,
            value TEXT
        )''')
        cursor.execute('DELETE FROM sessions')
        for session_id, session in sessions.items():
            cursor.execute('''INSERT INTO sessions VALUES (%s, %s, %s, %s, %s, %s, %s)''', (
                session_id,
                session["unick_name"],
                session["start_time"].isoformat(),
                session["end_time"].isoformat(),
                session["protected"],
                session["password"],
                session.get("value", None)
            ))
        conn.commit()
        conn.close()

    def load_sessions_postgresql(self, conn_string: str) -> Dict[str, Dict]:
        sessions = {}
        if not conn_string:
            raise ValueError("Connection string is required for PostgreSQL.")
        conn = psycopg2.connect(conn_string)
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM sessions')
        for row in cursor.fetchall():
            sessions[row[0]] = {
                "unick_name": row[1],
                "start_time": datetime.datetime.fromisoformat(row[2]),
                "end_time": datetime.datetime.fromisoformat(row[3]),
                "protected": row[4],
                "password": row[5],
                "value": row[6] if len(row) > 6 else None
            }
        conn.close()
        return sessions


class SessionManager:
    def __init__(self, name:str, protect: bool = False, auto_renew: bool = False, min_password_length:int=6):
        self.sessions: Dict[str, Dict] = {}
        self.filename = "sessions.json"
        self.db_name = "sessions.db"
        self.name = name
        self.protect = protect
        self.logging = auto_renew
        self.storer = SessionStoring(self.filename, self.db_name)
        self.mpl = min_password_length
        self.debug = True
        self.logs={
            "errors": [],
            "successful": [],
            "debug": []
        }


    def create(self, 
            unick_name: str = None, 
            duration_seconds: int = 3600, 
            value: str = None, 
            password: Optional[str] = None, 
            custom_metadata: dict = {}
            ) -> str:
        """
        Create a new session and return its unique session ID.

        This method supports optional password protection, duration setting,
        and attaching custom metadata. If protection is enabled, a valid password
        must be supplied.

        Parameters:
            unick_name (str, optional): A unique name for the session. If not provided,
                a default name will be generated. If that name already exists, session
                creation fails.
            duration_seconds (int): Duration of the session in seconds. Defaults to 3600 (1 hour).
            value (str, optional): Optional value/data to attach to the session.
            password (str, optional): Password for protected sessions. Required if `self.protect` is True.
            custom_metadata (dict, optional): Additional session metadata.

        Returns:
            str: Unique session ID if successful, or error message string if failed.
        """
        session_id = generate_session_id()
        now = datetime.datetime.now()
        protected = self.protect
        if unick_name is None:
            unick_name = get_default_unick_name()
        if any(session.get("unick_name") == unick_name for session in self.sessions.values()):
            return SessionMessages.SESSION_ALREADY_EXISTS
        if protected:
            if not password:
                return SessionMessages.PROTECTED_SESSION
            if len(password) < self.mpl:
                return SessionMessages.session_password_short(self.mpl)
            hashed_password = hash_password(password)
            if self.debug:
                self.logs["successful"].append(SessionMessages.SESSION_PASSWORD_CREATED)
        else:
            hashed_password = None
            if password and self.debug:
                self.logs["errors"].append(SessionMessages.session_password_incorrect_message(unick_name))
        self.sessions[session_id] = {
                "unick_name": unick_name,
                "start_time": now,
                "end_time": now + datetime.timedelta(seconds=duration_seconds),
                "protected": protected,
                "password": hashed_password,
                "value": value,
        }
        print(self.sessions)
        return str(session_id) 


    def remove(self, session_id: str):
        """
        Remove a session by ID.
        """
        if session_id not in self.sessions:
            return SessionMessages.SESSION_NOT_FOUND
        self.sessions.pop(session_id)

    def get(self, session_id: str) -> Optional[Dict]:
        """
        Get the session dictionary for a given session ID.
        """
        if session_id in self.sessions:
            return self.sessions[session_id]
        else:
            message = SessionMessages.session_not_found_message(session_id)[1]
            if self.debug:
                self.logs["errors"].append(message)
                self.logs["debug"].append(f"GET -- {session_id}")
            return message

    def is_active(self, session_id: str) -> bool:
        """
        Check if the session is currently active.
        """
        session = self.sessions[session_id]
        now = datetime.datetime.now()
        if self.debug:
            self.logs["debug"].append(f"IS_ACTIVE -- {session_id}")
        return session["start_time"] <= now <= session["end_time"]

    def get_time_remaining(self, session_id: str) -> float:
        """
        Get the number of seconds remaining before the session expires.
        """
        session = self.get(session_id)
        if self.debug:
            self.logs["debug"].append(f"GET_TIME_REMAINING -- {session_id}")
        return max((session["end_time"] - datetime.datetime.now()).total_seconds(), 0.0)

    def time_passed(self, session_id: str) -> float:
        """
        Get the number of seconds that have passed since the session started.
        """
        session = self.get(session_id)
        if self.debug:
            self.logs["debug"].append(f"TIME_PASSED -- {session_id}")
        return max((datetime.datetime.now() - session["start_time"]).total_seconds(), 0.0)

    def get_all(self) -> Dict[str, Dict]:
        """
        Return all sessions.
        """
        removed_sessions = []
        protected_sessions = []
        for session_id, session in list(self.sessions.items()):
            if session["protected"]:
                if not session.get("password"):
                    protected_sessions.append(session_id)
                    continue
            if session ["end_time"] < datetime.datetime.now():
                removed_sessions.append(session_id)
                self.remove(session_id)
        if self.debug:
            self.logs["debug"].append(f"GET_ALL -- total: {len(self.sessions)}")          
        return {
            session_id: self._flatten_session(session["session"])
            for session_id, session in self.sessions.items()
        }, removed_sessions, protected_sessions

    def save(self, filename: Optional[str] = None) -> bool:
        """
        Save all current session data to a file.
        """
        try:
            self.storer.store_sessions_json(self.sessions, filename)
            msg = SessionMessages.sessions_as_json_added_message(filename)[0]
            if self.debug:
                self.logs["successful"].append(msg)
            return True
        except Exception as e:
            if self.debug:
                self.logs["errors"].append(f"[SAVE ERROR] ({filename}) {str(e)}")
            return False

    def load(self, filename: str = None):
        """
        Load session data from a file and restore it into the session manager.
        """
        ext = self._get_file_extension(filename)

        try:
            with open(filename, 'r') as f:
                data = json.load(f)
            self.sessions = self._deserialize_session_data(data)
            msg = SessionMessages.session_as_json_loaded_message(filename)
            if self.logging or self.logging:
                log.info(msg[0])
            return msg[1]
        except json.JSONDecodeError:
            raise ValueError("Error loading sessions: Invalid JSON format.")
        except FileNotFoundError:
            self.sessions = {}
            raise ValueError(f"[LOAD ERROR] File '{filename}' not found for extension '{ext}'")
        except Exception as e:
            raise ValueError(f"Failed to load sessions: {str(e)}")


    def clean_all(self):
        """
        Clear all sessions and overwrite the session file.
        """
        self.sessions.clear()
        with open(self.filename, 'w') as f:
            json.dump(self.sessions, f)

    def get_with_unick_name(self, unick_name: str, logging:bool=False) -> Optional[str]:
        """get_id_by_unick_name
        Get the session ID for a given session name, if the session is not protected.
        """
        for session_id, session in self.sessions.items():
            if not session.get("protected") and session["unick_name"] == unick_name:
                return session_id
            if session.get("protected") and session["unick_name"] == unick_name:
                if logging or self.logging:
                    log.info(SessionMessages.protected_session_message(session_id)[0])
                return SessionMessages.protected_session_message(session_id)[1]
        return None

    def unlock(self, unick_name: str, password: str, logging:bool=False) -> Optional[str]:
        """
        Unlock a protected session for a given unick_name by verifying the hashed password.
        """
        for session_id, session in self.sessions.items():
            if session["unick_name"] == unick_name and session.get("protected"):
                if verify_password(password, session.get("password")):
                    session["protected"] = False
                    session["password"] = None
                    if logging or self.logging:
                        log.info(SessionMessages.unlock_message(session_id)[0])
                    return SessionMessages.unlock_message(session_id)[1]
                else:
                    return 
        if logging or self.logging:
            log.warning(SessionMessages.session_not_found_message(unick_name)[0])
        return SessionMessages.session_not_found_message(unick_name)[1]
    


    def lock(self, session_id: str, password: str, logging:bool=False) -> Optional[str]:
        """
        Lock a session by setting a password.
        """
        if session_id not in self.sessions:
            if logging or self.logging:
                log.warning(SessionMessages.session_not_found_message(session_id)[0])
            return SessionMessages.session_not_found_message(session_id)[1]
        if self.sessions[session_id].get("protected"):
            if logging or self.logging:
                log.warning(SessionMessages.session_already_locked_message(session_id)[0])
            return SessionMessages.session_already_locked_message(session_id)[1]
        if self.sessions[session_id].get("password"):
            if logging or self.logging:
                log.warning(SessionMessages.session_already_locked_message(session_id)[0])
            return SessionMessages.session_already_locked_message(session_id)[1]
        if not password:
            if logging or self.logging:
                log.error(SessionMessages.session_password_required_message(session_id)[0])
            raise ValueError("Password is required to lock the session.")
        if len(password) < 6:
            if logging or self.logging:
                log.error(SessionMessages.session_password_incorrect_message(session_id)[0])
            raise ValueError("Password must be at least 6 characters long.")
        
        self.sessions[session_id]["protected"] = True
        self.sessions[session_id]["password"] = hash_password(password)
        self.store_sessions(self.filename)
        self.load_sessions(self.filename)

        return self.sessions[session_id]
    

    def get_value(self, session_id: str) -> Optional[str]:
        """
        Get the value associated with a session.
        """
        if session_id in self.sessions:
            if self.sessions[session_id].get("protected"):
                return SessionMessages.session_locked_message(session_id)[1]
            return self.sessions[session_id].get("value")
        else:
            raise ValueError(f"Session ID {session_id} not found.")

    def _get_file_extension(self, filename: str) -> str:
        if '.' not in filename:
            raise ValueError("Filename must include an extension (e.g., 'sessions.json').")
        return filename.split('.')[-1].lower()

    def _deserialize_session_data(self, sessions: dict) -> dict:
        for session_id, session in sessions.items():
            session["start_time"] = datetime.datetime.fromisoformat(session["start_time"])
            session["end_time"] = datetime.datetime.fromisoformat(session["end_time"])
            session["protected"] = session.get("protected", False)
            session["password"] = session.get("password")
            session["unick_name"] = session.get("unick_name", get_default_unick_name())
            session["value"] = session.get("value")
        return sessions


    def _flatten_session(self, session_dict: Dict) -> Dict:
        return {
            "unick_name": session_dict["unick_name"],
            "start_time": session_dict["start_time"].isoformat(),
            "end_time": session_dict["end_time"].isoformat(),
            "protected": session_dict["protected"],
            "password": session_dict.get("password"),
            "value": session_dict.get("value"),
        }

    def __repr__(self):
        return f"<SessionManager(name={self.name}, sessions={len(self.sessions)})>"

    def __str__(self):
        return f"SessionManager '{self.name}' with {len(self.sessions)} sessions"