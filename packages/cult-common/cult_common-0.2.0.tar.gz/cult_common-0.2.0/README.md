```
# cult-common

Shared configuration and utility library for Cult microservices.

## Installation

pip install cult-common==0.1.0


## Usage

from cult_common.config import settings
logger = cult_common.logging.get_logger(__name__)

print(settings.KAFKA_BOOTSTRAP_SERVERS)
```