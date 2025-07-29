"""
Sample scene.
"""

from pathlib import Path

from nextrpg.character.rpg_maker_drawing import (
    Margin,
    RpgMakerCharacterDrawing,
    SpriteSheet,
    SpriteSheetSelection,
)
from nextrpg.draw_on_screen import Drawing
from nextrpg.scene.map_scene import MapScene
from nextrpg.scene.scene import Scene


def entry_scene() -> Scene:
    """
    Defines the entry scene for the game.

    Returns:
        `Scene`: The sample scene.
    """
    return MapScene(
        Path("assets/interior.tmx"),
        RpgMakerCharacterDrawing(
            SpriteSheet(
                Drawing(Path("assets/Characters_MV.png")),
                SpriteSheetSelection(row=0, column=1),
                Margin(top=28),
            ),
        ),
    )
