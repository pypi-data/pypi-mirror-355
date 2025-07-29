import logging

import litellm
from dotenv import load_dotenv
load_dotenv()
litellm.drop_params = True


root_pkg_logger = logging.getLogger(__name__)
root_pkg_logger.propagate = False

handler = logging.StreamHandler()
handler.setLevel(logging.DEBUG)

formatter = logging.Formatter(
    "%(asctime)s - %(name)s - %(lineno)d - %(levelname)s - %(message)s"
)
handler.setFormatter(formatter)

root_pkg_logger.addHandler(handler)

root_pkg_logger.setLevel(logging.DEBUG)


# Silence prisma generated module logger
logging.getLogger("evalassist.prisma_client").setLevel(logging.CRITICAL + 1)
