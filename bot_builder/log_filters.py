import re
import logging


class SensitiveDataFilter(logging.Filter):
    """
    Фильтр для маскирования чувствительных данных в логах.
    """

    # Регулярные выражения для поиска чувствительных данных
    FILTER_PATTERNS = [
        (
            re.compile(r'(oauth_token=)[^&"\s]+', re.IGNORECASE),
            r'\1***'
        ),
        (
            re.compile(r'("token")\s*:\s*"([^"]+)"', re.IGNORECASE),
            r'\1: "***"'
        ),
        (
            re.compile(r'("oauth_token")\s*:\s*"([^"]+)"', re.IGNORECASE),
            r'\1: "***"'
        ),
        (
            re.compile(r'(state=)[^&"\s]+', re.IGNORECASE),
            r'\1***'
        ),
        (
            re.compile(r'(code=)[^&"\s]+', re.IGNORECASE),
            r'\1***'
        ),
        (
            re.compile(r'(cid=)[^&"\s]+', re.IGNORECASE),
            r'\1***'
        ),
        (
            re.compile(r'("password")\s*:\s*"([^"]+)"', re.IGNORECASE),
            r'\1: "***"'
        ),
        (
            re.compile(r'("token")\s*:\s*"([^"]+)"', re.IGNORECASE),
            r'\1: "***"'
        ),
        (
            re.compile(r'("api_key")\s*:\s*"([^"]+)"', re.IGNORECASE),
            r'\1: "***"'
        ),
        (
            re.compile(r'("secret")\s*:\s*"([^"]+)"', re.IGNORECASE),
            r'\1: "***"'),
        (
            re.compile(r'("email")\s*:\s*"([^"]+)"', re.IGNORECASE),
            r'\1: "***@***.***"'
        ),
    ]

    def filter(self, record):
        # Обработка msg
        if isinstance(record.msg, str):
            for pattern, replacement in self.FILTER_PATTERNS:
                record.msg = pattern.sub(replacement, record.msg)

        # Обработка args
        if record.args:
            new_args = []
            for arg in record.args:
                if isinstance(arg, str):
                    cleaned = arg
                    for pattern, replacement in self.FILTER_PATTERNS:
                        cleaned = pattern.sub(replacement, cleaned)
                    new_args.append(cleaned)
                else:
                    new_args.append(arg)
            record.args = tuple(new_args)

        return True
