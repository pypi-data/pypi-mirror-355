# MTK Logger

Logging utilities for MarkTrack applications.

## Installation

To install from GitHub Packages:

```bash
# Configure pip to use GitHub Packages
pip config set global.extra-index-url https://YOUR_GITHUB_TOKEN@github.com/pprasquier/mtk_logger/raw/main/dist/

# Install the package
pip install mtk_logger
```

Or with Poetry:

```bash
# Add GitHub Packages as a source
poetry source add --priority=supplemental github https://github.com/pprasquier/mtk_logger/raw/main/dist/

# Install the package
poetry add mtk_logger
```

## Usage

```python
from mtk_logger.logger import get_logger

logger = get_logger(__name__)
logger.info("This is a log message")
```

For FastAPI middleware:

```python
from mtk_logger.fastapi_middleware import RequestLoggingMiddleware

app.add_middleware(RequestLoggingMiddleware)
``` 