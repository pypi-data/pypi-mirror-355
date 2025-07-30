from asup import Asup
from tasks import ensure_config_exists


def asup():
    ensure_config_exists()
    app = Asup()
    app.run()
