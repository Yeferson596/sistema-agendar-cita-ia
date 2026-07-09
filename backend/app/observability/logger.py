import json
import logging
from datetime import datetime
from pathlib import Path

LOG_DIR = Path(__file__).parent.parent.parent / 'logs'
LOG_DIR.mkdir(parents=True, exist_ok=True)

logger = logging.getLogger('mediflow')
logger.setLevel(logging.INFO)
fh = logging.FileHandler(LOG_DIR / 'mediflow-app.log', encoding='utf-8')
fh.setLevel(logging.INFO)

class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload = {
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'level': record.levelname,
            'service': 'mediflow-agent',
            'message': record.getMessage(),
        }
        if hasattr(record, 'context'):
            payload['context'] = record.context
        return json.dumps(payload, ensure_ascii=False)

fh.setFormatter(JsonFormatter())
logger.addHandler(fh)


def log_event(level: str, context: str, data: dict | None = None) -> None:
    msg = context
    extra = {'context': data or {}}
    if level.upper() == 'INFO':
        logger.info(msg, extra=extra)
    elif level.upper() == 'WARN' or level.upper() == 'WARNING':
        logger.warning(msg, extra=extra)
    elif level.upper() == 'ERROR':
        logger.error(msg, extra=extra)
    else:
        logger.debug(msg, extra=extra)
