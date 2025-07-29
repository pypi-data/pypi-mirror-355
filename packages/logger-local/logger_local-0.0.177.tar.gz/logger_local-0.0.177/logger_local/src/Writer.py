import queue
import threading
import time

from python_sdk_remote.mini_logger import MiniLogger as logger

from .Connector import get_connection


class Writer:
    _instance = None  # Class variable to store the single instance
    _queue: queue.Queue = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(Writer, cls).__new__(cls, *args, **kwargs)
            cls._queue = queue.Queue()
            cls._instance._initialize_sending_thread()
        return cls._instance

    def _initialize_sending_thread(self):
        self.sending_thread = threading.Thread(target=self._flush_queue)
        self.sending_thread.daemon = True
        self.sending_thread.name = 'logger-sending-thread'
        self.sending_thread.start()

    def _flush_queue(self):
        while self._queue.empty():
            time.sleep(1)
        connection = get_connection(schema_name="logger", is_treading=True)
        cursor = connection.cursor()
        # TODO use executemany?
        while not self._queue.empty():
            query, values = self._queue.get()
            cursor.execute(query, values)

        cursor.close()
        connection.commit()

    # INSERT to logger_table should be disabled by default and activated using combination of json and Environment variable enabling INSERTing to the logger_table
    # This function is called when `self.write_to_sql and self.debug_mode.is_logger_output(component_id=
    #                               self.component_id, logger_output=LoggerOutputEnum.MySQLDatabase, message_severity.value)`
    def add_message_and_payload(self, message: str, params_to_insert: dict) -> None:
        try:
            try:
                # location_id = 0
                if params_to_insert.get('latitude') and params_to_insert.get('longitude'):
                    location_query = (f"INSERT INTO location.location_table (coordinate) "
                                      f"VALUES (POINT({params_to_insert.get('latitude')},"
                                      f"              {params_to_insert.get('longitude')}));")
                    # TODO: location_id = cursor.lastrowid
                    self._queue.put((location_query, []))

                    params_to_insert.pop('latitude', None)
                    params_to_insert.pop('longitude', None)

                # params_to_insert['location_id'] = location_id

            except Exception as exception:
                logger.exception("Exception logger Writer.py add_message_and_payload after adding location ", exception)

            listed_values = [str(k) for k in params_to_insert.values()]
            joined_keys = ','.join(list(params_to_insert.keys()))
            if 'message' not in params_to_insert:
                listed_values.append(message)
                joined_keys += (',' if params_to_insert else '') + 'message'

            placeholders = ','.join(['%s'] * len(listed_values))
            logger_query = f"INSERT INTO logger.logger_table ({joined_keys}) VALUES ({placeholders})"
            self._queue.put((logger_query, listed_values))
            if not self.sending_thread.is_alive():
                self._initialize_sending_thread()

        except Exception as exception:
            logger.exception("Exception logger Writer.py add_message_and_payload after insert to logger table",
                             exception)
            if " denied " not in str(exception).lower():
                raise exception
