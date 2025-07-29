# pastimepy

`pastimepy` is a simple Python package to format `datetime` objects into human-readable strings like "5 minutes ago", "yesterday at 3:00 PM", or "Jan 01, 2024 at 12:00 PM".

## Installation
```bash
pip install pastimepy
```

## Usage
```python
from pastime import format_time
from datetime import datetime, timedelta

print(format_time(datetime.now() - timedelta(minutes=5)))
# Output: '5 minutes ago'
```

## License
MIT License