import os


def get_logger_level() -> str:
    level_map = {
        'silly': 'CRITICAL',
        'verbose': 'DEBUG',
        'info': 'INFO',
        'warn': 'WARNING',
        'error': 'ERROR',
    }
    level: str = os.environ.get('WS_LOG', 'info').lower()
    if level not in level_map:
        raise ValueError(
            'WiseFlow LOG should support the values of `silly`, '
            '`verbose`, `info`, `warn`, `error`'
        )
    return level_map.get(level, 'info')
