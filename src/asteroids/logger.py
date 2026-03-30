import inspect
import json
import math
from datetime import datetime

# This module writes JSONL logs about the game.
# JSONL means "JSON Lines": one complete JSON object per line.
# That format is handy because we can append events one by one without having
# to rewrite a huge JSON array every time.
#
# JSONL VISUAL IDEA:
#
#   game_events.jsonl
#   +--------------------------------------------------------------+
#   | {"type":"shield_picked","frame":120,...}                 |
#   | {"type":"asteroid_split","frame":181,...}               |
#   | {"type":"player_hit","frame":244,...}                   |
#   +--------------------------------------------------------------+
#
# Each line is independent.
# That means we can add a NEW line at the end without touching older lines.
# This is much simpler than maintaining one giant JSON list like:
#   [ {...}, {...}, {...} ]
# because a giant list must stay perfectly structured from beginning to end.

__all__ = ["log_state", "log_event"]

# Logging configuration.
# These values limit how much data we write so logs stay readable and small.
_FPS = 60
_MAX_SECONDS = 16
_SPRITE_SAMPLE_LIMIT = 10  # Maximum number of sprites to log per group

# Module-level variables keep their values between function calls.
_frame_count = 0
_state_log_initialized = False
_event_log_initialized = False
_start_time = datetime.now()


def log_state():
    """Record a lightweight snapshot of the game state.

    The interesting trick here is inspect.currentframe(). It lets us look at
    the local variables of the function that called log_state(). That means
    main.py can call log_state() without manually building a giant dictionary
    every frame.

    To avoid huge files, we only write about once per second and we stop after
    a short amount of time.

    CALL STACK IDEA (who called whom?):

        main.py game loop
              |
              | calls
              v
          log_state()
              |
              | inspect.currentframe()
              v
        current frame object
              |
              | .f_back
              v
        caller's frame object
              |
              | .f_locals
              v
        dictionary of local variables

    In plain words:
    log_state() asks Python:
    "Show me the function that called me, and show me its local variables."

    That is why log_state() can discover things like player, asteroids,
    screen, and shots without receiving them as explicit arguments.

    SNAPSHOT TIMELINE:

        frame:   1   2   3   ...  59  60  61  ... 120
        write?   no  no  no       no  yes no      yes

    So the file grows slowly and stays readable.
    """
    global _frame_count, _state_log_initialized

    # Stop logging after a fixed amount of time.
    # Example: 16 seconds * 60 FPS = about 960 frames.
    if _frame_count > _FPS * _MAX_SECONDS:
        return

    # We count frames and only keep every 60th frame.
    # That gives us about one snapshot per second.
    _frame_count += 1
    if _frame_count % _FPS != 0:
        return

    now = datetime.now()

    # currentframe() gives the frame of THIS function call.
    frame = inspect.currentframe()
    if frame is None:
        return

    # .f_back means "one level back in the call stack".
    # That is the function that called log_state().
    frame_back = frame.f_back
    if frame_back is None:
        return

    # Make a copy of the caller's local variables so we can inspect them safely.
    local_vars = frame_back.f_locals.copy()

    screen_size = []
    game_state = {}

    for key, value in local_vars.items():
        # The screen surface has a get_size method, so this is a simple way
        # to identify it among the caller's variables.
        if "pygame" in str(type(value)) and hasattr(value, "get_size"):
            screen_size = value.get_size()

        # Sprite groups hold many game objects like asteroids, shots, etc.
        if hasattr(value, "__class__") and "Group" in value.__class__.__name__:
            sprites_data = []

            for i, sprite in enumerate(value):
                if i >= _SPRITE_SAMPLE_LIMIT:
                    break

                # Build a small summary instead of dumping the whole object.
                sprite_info = {"type": sprite.__class__.__name__}

                if hasattr(sprite, "position"):
                    sprite_info["pos"] = [
                        round(sprite.position.x, 2),
                        round(sprite.position.y, 2),
                    ]

                if hasattr(sprite, "velocity"):
                    sprite_info["vel"] = [
                        round(sprite.velocity.x, 2),
                        round(sprite.velocity.y, 2),
                    ]

                if hasattr(sprite, "radius"):
                    sprite_info["rad"] = sprite.radius

                if hasattr(sprite, "rotation"):
                    sprite_info["rot"] = round(sprite.rotation, 2)

                sprites_data.append(sprite_info)

            game_state[key] = {"count": len(value), "sprites": sprites_data}

        # If there are no groups yet, we may still want to log a single object
        # such as the player, as long as it has a position.
        if len(game_state) == 0 and hasattr(value, "position"):
            sprite_info = {"type": value.__class__.__name__}

            sprite_info["pos"] = [
                round(value.position.x, 2),
                round(value.position.y, 2),
            ]

            if hasattr(value, "velocity"):
                sprite_info["vel"] = [
                    round(value.velocity.x, 2),
                    round(value.velocity.y, 2),
                ]

            if hasattr(value, "radius"):
                sprite_info["rad"] = value.radius

            if hasattr(value, "rotation"):
                sprite_info["rot"] = round(value.rotation, 2)

            game_state[key] = sprite_info

    # Final shape of one JSONL line:
    # {
    #   "timestamp": "12:34:56.789",
    #   "elapsed_s": 3,
    #   "frame": 180,
    #   "screen_size": [1280, 720],
    #   "asteroids": {"count": 5, "sprites": [...]},
    #   "player": {...}
    # }
    entry = {
        "timestamp": now.strftime("%H:%M:%S.%f")[:-3],
        "elapsed_s": math.floor((now - _start_time).total_seconds()),
        "frame": _frame_count,
        "screen_size": screen_size,
        **game_state,
    }

    # First write uses "w" to create a fresh file for this run.
    # Later writes use "a" to append new lines.
    mode = "w" if not _state_log_initialized else "a"
    with open("game_state.jsonl", mode) as f:
        f.write(json.dumps(entry) + "\n")

    _state_log_initialized = True


def log_event(event_type, **details):
    """Record one named event in game_events.jsonl.

    **details collects any extra named values into a dictionary.
    Example:
    log_event("asteroid_split", size=3, score=20)

    This is flexible because different events can store different fields.

    EVENT LOG EXAMPLES:

        log_event("player_hit", lives=2)
        -> {"type": "player_hit", "lives": 2, ...}

        log_event("bomb_exploded", bomb_pos=[500, 300])
        -> {"type": "bomb_exploded", "bomb_pos": [500, 300], ...}

    Same function, different extra fields.
    That flexibility is exactly why **details is useful.
    """
    global _event_log_initialized

    now = datetime.now()

    event = {
        "timestamp": now.strftime("%H:%M:%S.%f")[:-3],
        "elapsed_s": math.floor((now - _start_time).total_seconds()),
        "frame": _frame_count,
        "type": event_type,
        **details,
    }

    # Same idea as log_state: overwrite on first call, append after that.
    mode = "w" if not _event_log_initialized else "a"
    with open("game_events.jsonl", mode) as f:
        f.write(json.dumps(event) + "\n")

    _event_log_initialized = True
