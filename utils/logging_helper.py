import logging

log_data = []

class CustomHandler(logging.StreamHandler):
    def emit(self, record):
        log_entry = self.format(record)
        log_data.append(log_entry)
        super().emit(record)

def setup_logging():
    handler = CustomHandler()
    handler.setLevel(logging.INFO)
    logging.getLogger().addHandler(handler)
    logging.basicConfig(level=logging.INFO)
