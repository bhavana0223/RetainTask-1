from flask import Flask
from routes.user_routes import user_routes
import sqlite3
from db import get_db_connection , create_users_table
import logging
logging.basicConfig(
    level=logging.INFO,  # Changed to INFO to see more details
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)

logger = logging.getLogger(__name__)

app = Flask(__name__)
app.register_blueprint(user_routes)

# Log registered routes for debugging
logger.info("Registered routes:")
for rule in app.url_map.iter_rules():
    logger.info(f"  {rule.rule} -> {rule.endpoint} [{', '.join(rule.methods)}]")

create_users_table()  # Ensure the users table is created at startup
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5009, debug=False)
