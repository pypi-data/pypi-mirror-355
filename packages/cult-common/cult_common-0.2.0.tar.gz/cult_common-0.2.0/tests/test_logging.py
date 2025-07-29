import logging
from cult_common import logging as lc_logging

def test_logger_setup(caplog):
    logger = lc_logging.get_logger("test_logger_setup")
    caplog.set_level(logging.INFO, logger=logger.name) 
    logger.info("hello")
    assert "hello" in caplog.messages