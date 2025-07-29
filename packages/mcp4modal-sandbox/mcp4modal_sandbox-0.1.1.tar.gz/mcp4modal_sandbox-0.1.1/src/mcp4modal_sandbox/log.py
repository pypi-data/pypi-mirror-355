import logging 

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(filename)s - line:%(lineno)03d - %(levelname)s - %(message)s",
)

logger = logging.getLogger(name="mcp4modal_sandbox")


if __name__ == "__main__":
    logger.info("log initialized")