from krita import Krita
from .extension import SpacenavControlExtension

def initialize():
    app = Krita.instance()
    if app:
        # Register the extension
        app.addExtension(SpacenavControlExtension(app))
        print("Krita_Spacemouse plugin v1.0 registered")

        # Optional: Log successful initialization for debugging
        from .utils import debug_print
        debug_print("Plugin initialization complete", 1, debug_level=1)
    else:
        print("Krita instance not found")

# Run initialization
initialize()
