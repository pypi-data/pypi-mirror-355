class SessionMessages:
    """Contains all session-related message templates and their corresponding log codes."""

    # Log codes (constant identifiers)
    PROTECTED_SESSION = "PROTECTED_SESSION"
    ACTIVE_SESSION = "ACTIVE_SESSION"
    UNLOCK_SESSION = "UNLOCK_SESSION"
    LOCK_SESSION = "LOCK_SESSION"
    SESSION_NOT_FOUND = "SESSION_NOT_FOUND"
    SESSION_ALREADY_LOCKED = "SESSION_ALREADY_LOCKED"
    SESSION_ALREADY_UNLOCKED = "SESSION_ALREADY_UNLOCKED"
    SESSION_LOCKED = "SESSION_LOCKED"
    SESSION_UNLOCK_FAILED = "SESSION_UNLOCK_FAILED"
    SESSION_UNLOCK_SUCCESS = "SESSION_UNLOCK_SUCCESS"
    SESSION_LOCK_SUCCESS = "SESSION_LOCK_SUCCESS"
    SESSION_LOCK_FAILED = "SESSION_LOCK_FAILED"
    SESSION_CREATE_SUCCESS = "SESSION_CREATE_SUCCESS"
    SESSION_CREATE_FAILED = "SESSION_CREATE_FAILED"
    SESSION_DELETE_SUCCESS = "SESSION_DELETE_SUCCESS"
    SESSION_DELETE_FAILED = "SESSION_DELETE_FAILED"
    SESSION_LIST = "SESSION_LIST"
    SESSION_LIST_EMPTY = "SESSION_LIST_EMPTY"
    SESSION_LIST_NOT_FOUND = "SESSION_LIST_NOT_FOUND"
    SESSION_TIMEOUT = "SESSION_TIMEOUT"
    SESSION_RESTORE_SUCCESS = "SESSION_RESTORE_SUCCESS"
    SESSION_RESTORE_FAILED = "SESSION_RESTORE_FAILED"
    SESSION_ALREADY_EXISTS = "SESSION_ALREADY_EXISTS"
    INVALID_SESSION_ID = "INVALID_SESSION_ID"
    SESSION_ACCESS_DENIED = "SESSION_ACCESS_DENIED"
    SESSION_PASSWORD_REQUIRED = "SESSION_PASSWORD_REQUIRED"
    SESSION_PASSWORD_INCORRECT = "SESSION_PASSWORD_INCORRECT"
    SESSIONS_AS_JSON_ADDED = "SESSIONS_AS_JSON_ADDED"
    SESSIONS_AS_JSON_FAILED = "SESSIONS_AS_JSON_FAILED"
    SESSIONS_AS_CSV_ADDED = "SESSIONS_AS_CSV_ADDED"
    SESSIONS_AS_CSV_FAILED = "SESSIONS_AS_CSV_FAILED"
    SESSIONS_AS_SQLITE_ADDED = "SESSIONS_AS_SQLITE_ADDED"
    SESSIONS_AS_SQLITE_FAILED = "SESSIONS_AS_SQLITE_FAILED"
    SESSIONS_AS_POSTGRESQL_ADDED = "SESSIONS_AS_POSTGRESQL_ADDED"
    SESSIONS_AS_POSTGRESQL_FAILED = "SESSIONS_AS_POSTGRESQL_FAILED"
    SESSION_AS_JSON_LOADED = "SESSION_AS_JSON_LOADED"
    SESSION_AS_JSON_LOADED_FAILED = "SESSION_AS_JSON_LOADED_FAILED"
    SESSION_AS_CSV_LOADED = "SESSION_AS_CSV_LOADED"
    SESSION_AS_CSV_LOADED_FAILED = "SESSION_AS_CSV_LOADED_FAILED"
    SESSION_AS_SQLITE_LOADED = "SESSION_AS_SQLITE_LOADED"
    SESSION_AS_SQLITE_LOADED_FAILED = "SESSION_AS_SQLITE_LOADED_FAILED"
    SESSION_AS_POSTGRESQL_LOADED = "SESSION_AS_POSTGRESQL_LOADED"
    SESSION_AS_POSTGRESQL_LOADED_FAILED = "SESSION_AS_POSTGRESQL_LOADED_FAILED"
    SESSION_PASSWORD_CREATED = "SESSION_PASSWORD_CREATED"
    SESSION_SAVE_FILE_EXTENSION_FAILED = "SESSION_SAVE_FILE_EXTENSION_FAILED"
    UNSUPPORTED_FILE_EXTENSION = "UNSUPPORTED_FILE_EXTENSION"
    SESSION_PASSWORD_TOO_SHORT = "SESSION_PASSWORD_TOO_SHORT"

    # Message methods
    @staticmethod
    def protected_session_message(session_id): return (f"Session {session_id} is protected. Please unlock it.", SessionMessages.PROTECTED_SESSION)
    @staticmethod
    def session_message(session_id): return (f"Session {session_id} is active.", SessionMessages.ACTIVE_SESSION)
    @staticmethod
    def unlock_message(session_id): return (f"Session {session_id} is unlocked.", SessionMessages.UNLOCK_SESSION)
    @staticmethod
    def lock_message(session_id): return (f"Session {session_id} is locked.", SessionMessages.LOCK_SESSION)
    @staticmethod
    def session_not_found_message(session_id): return (f"Session {session_id} not found.", SessionMessages.SESSION_NOT_FOUND)
    @staticmethod
    def session_already_locked_message(session_id): return (f"Session {session_id} is already locked.", SessionMessages.SESSION_ALREADY_LOCKED)
    @staticmethod
    def session_already_unlocked_message(session_id): return (f"Session {session_id} is already unlocked.", SessionMessages.SESSION_ALREADY_UNLOCKED)
    @staticmethod
    def session_locked_message(session_id): return (f"Session {session_id} is locked.", SessionMessages.SESSION_LOCKED)
    @staticmethod
    def session_unlock_failed_message(session_id): return (f"Failed to unlock session {session_id}.", SessionMessages.SESSION_UNLOCK_FAILED)
    @staticmethod
    def session_unlock_success_message(session_id): return (f"Session {session_id} unlocked successfully.", SessionMessages.SESSION_UNLOCK_SUCCESS)
    @staticmethod
    def session_lock_success_message(session_id): return (f"Session {session_id} locked successfully.", SessionMessages.SESSION_LOCK_SUCCESS)
    @staticmethod
    def session_lock_failed_message(session_id): return (f"Failed to lock session {session_id}.", SessionMessages.SESSION_LOCK_FAILED)
    @staticmethod
    def session_create_success_message(session_id): return (f"Session {session_id} created successfully.", SessionMessages.SESSION_CREATE_SUCCESS)
    @staticmethod
    def session_create_failed_message(session_id): return (f"Failed to create session {session_id}.", SessionMessages.SESSION_CREATE_FAILED)
    @staticmethod
    def session_delete_success_message(session_id): return (f"Session {session_id} deleted successfully.", SessionMessages.SESSION_DELETE_SUCCESS)
    @staticmethod
    def session_delete_failed_message(session_id): return (f"Failed to delete session {session_id}.", SessionMessages.SESSION_DELETE_FAILED)
    @staticmethod
    def session_list_message(sessions): return (f"Active sessions: {', '.join(sessions)}", SessionMessages.SESSION_LIST)
    @staticmethod
    def session_list_empty_message(): return ("No active sessions.", SessionMessages.SESSION_LIST_EMPTY)
    @staticmethod
    def session_list_not_found_message(session_id): return (f"Session {session_id} not found.", SessionMessages.SESSION_LIST_NOT_FOUND)
    @staticmethod
    def session_timeout_message(session_id): return (f"Session {session_id} has timed out due to inactivity.", SessionMessages.SESSION_TIMEOUT)
    @staticmethod
    def session_restore_success_message(session_id): return (f"Session {session_id} has been restored successfully.", SessionMessages.SESSION_RESTORE_SUCCESS)
    @staticmethod
    def session_restore_failed_message(session_id): return (f"Failed to restore session {session_id}.", SessionMessages.SESSION_RESTORE_FAILED)
    @staticmethod
    def session_already_exists_message(session_id): return (f"Session {session_id} already exists.", SessionMessages.SESSION_ALREADY_EXISTS)
    @staticmethod
    def invalid_session_id_message(session_id): return (f"The session ID '{session_id}' is invalid.", SessionMessages.INVALID_SESSION_ID)
    @staticmethod
    def session_access_denied_message(session_id): return (f"Access denied for session {session_id}.", SessionMessages.SESSION_ACCESS_DENIED)
    @staticmethod
    def session_password_required_message(session_id): return (f"Password is required for this session. SESSION_ID: {session_id}", SessionMessages.SESSION_PASSWORD_REQUIRED)
    @staticmethod
    def session_password_incorrect_message(session_id): return (f"Incorrect password for this session. SESSION_ID: {session_id}", SessionMessages.SESSION_PASSWORD_INCORRECT)
    @staticmethod
    def sessions_as_json_added_message(file_path): return (f"Sessions added to JSON file: {file_path}", SessionMessages.SESSIONS_AS_JSON_ADDED)
    @staticmethod
    def sessions_as_json_failed_message(file_path): return (f"Failed to add sessions to JSON file: {file_path}", SessionMessages.SESSIONS_AS_JSON_FAILED)
    @staticmethod
    def sessions_as_csv_added_message(file_path): return (f"Sessions added to CSV file: {file_path}", SessionMessages.SESSIONS_AS_CSV_ADDED)
    @staticmethod
    def sessions_as_csv_failed_message(file_path): return (f"Failed to add sessions to CSV file: {file_path}", SessionMessages.SESSIONS_AS_CSV_FAILED)
    @staticmethod
    def sessions_as_sqlite_added_message(file_path): return (f"Sessions added to SQLite file: {file_path}", SessionMessages.SESSIONS_AS_SQLITE_ADDED)
    @staticmethod
    def sessions_as_sqlite_failed_message(file_path): return (f"Failed to add sessions to SQLite file: {file_path}", SessionMessages.SESSIONS_AS_SQLITE_FAILED)
    @staticmethod
    def sessions_as_postgresql_added_message(file_path): return (f"Sessions added to PostgreSQL file: {file_path}", SessionMessages.SESSIONS_AS_POSTGRESQL_ADDED)
    @staticmethod
    def sessions_as_postgresql_failed_message(file_path): return (f"Failed to add sessions to PostgreSQL file: {file_path}", SessionMessages.SESSIONS_AS_POSTGRESQL_FAILED)
    @staticmethod
    def session_as_json_loaded_message(file_path): return (f"Session loaded from JSON file: {file_path}", SessionMessages.SESSION_AS_JSON_LOADED)
    @staticmethod
    def session_as_json_loaded_failed_message(file_path): return (f"Failed to load session from JSON file: {file_path}", SessionMessages.SESSION_AS_JSON_LOADED_FAILED)
    @staticmethod
    def session_as_csv_loaded_message(file_path): return (f"Session loaded from CSV file: {file_path}", SessionMessages.SESSION_AS_CSV_LOADED)
    @staticmethod
    def session_as_csv_loaded_failed_message(file_path): return (f"Failed to load session from CSV file: {file_path}", SessionMessages.SESSION_AS_CSV_LOADED_FAILED)
    @staticmethod
    def session_as_sqlite_loaded_message(file_path): return (f"Session loaded from SQLite file: {file_path}", SessionMessages.SESSION_AS_SQLITE_LOADED)
    @staticmethod
    def session_as_sqlite_loaded_failed_message(file_path): return (f"Failed to load session from SQLite file: {file_path}", SessionMessages.SESSION_AS_SQLITE_LOADED_FAILED)
    @staticmethod
    def session_as_postgresql_loaded_message(file_path): return (f"Session loaded from PostgreSQL file: {file_path}", SessionMessages.SESSION_AS_POSTGRESQL_LOADED)
    @staticmethod
    def session_as_postgresql_loaded_failed_message(file_path): return (f"Failed to load session from PostgreSQL file: {file_path}", SessionMessages.SESSION_AS_POSTGRESQL_LOADED_FAILED)
    @staticmethod
    def session_password_short(mpl: int): return (f"Password must be at least {mpl} characters long.", SessionMessages.SESSION_PASSWORD_TOO_SHORT)
