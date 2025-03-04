# Krita SpaceMouse Plugin
![Krita SpaceMouse](krita_spacemouse/images/Krita_Spacemouse_Full_View.png)

A feature-rich plugin integrating SpaceMouse (especially Enterprise) with Krita on Linux, eliminating the keyboard for a streamlined art workflow.

[**Documentation Wiki**](https://github.com/Totem-FPV/Krita_Spacemouse/wiki)

## Features
- Map 6 axes (X, Y, Z, RX, RY, RZ) to canvas actions (Pan, Zoom, Rotate) with custom curves.
- Bind 31 buttons (plus modifiers) to Krita actions via an interactive docker.
- Save presets for buttons and curves, persisting across sessions.

## Installation (Linux-only)
1. **Zip**: Unpack to `~/.local/share/krita/pykrita/`.
2. **Git**: `cd ~/.local/share/krita/pykrita/ && git clone https://github.com/Totem-FPV/Krita_Spacemouse.git`.
3. **Enable**: In Krita, `Settings > Configure Krita > Python Plugin Manager`, enable "SpaceMouse Plugin", restart Krita.
4. **Add Docker**: `Settings > Dockers > SpaceMouse Controls`.

**Note**: Ensure SpaceMouse buttons (including modifiers) pass through as normal keys in `spnav`, not system modifiers.

## Feedback
Report bugs at [GitHub Issues](https://github.com/Totem-FPV/Krita_Spacemouse/issues).
