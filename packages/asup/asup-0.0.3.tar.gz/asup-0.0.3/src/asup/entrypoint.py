from asup.asup import Asup
from asup.tasks import ensure_config_exists


def asup():
    ensure_config_exists()
    app = Asup()
    app.run()
