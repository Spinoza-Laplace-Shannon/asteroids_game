# Asteroids Game

A Python/Pygame implementation of the classic Asteroids arcade game with modern features.

## Features

- 🎮 **Classic Gameplay** - Destroy asteroids, avoid collisions
- 🎯 **Three Weapon Types** - Single, Spread, and Rapid fire modes
- 💣 **Bomb System** - Drop explosive devices with timed fuses
- 🛡️ **Shield Power-ups** - Glowing shields that protect you from one hit
- 🎵 **Synthesized Audio** - Real-time sound effect generation
- 📊 **High Scores** - Persistently saved leaderboard
- 🎛️ **Difficulty Levels** - Easy, Normal, and Hard modes
- ⏸️ **Pause Menu** - Pause and resume your game
- 📖 **Tutorial** - In-game help for new players
- ⌨️ **Arrow Key Controls** - Intuitive movement and rotation

## Project Structure

```
asteroids_game/
├── src/asteroids/          # Main game source code
│   ├── main.py            # Game loop and core logic
│   ├── player.py          # Player ship class
│   ├── asteroid.py        # Asteroid and explosion classes
│   ├── shot.py            # Bullet/projectile class
│   ├── bomb.py            # Explosive weapon class
│   ├── powerup.py         # Power-up items class
│   ├── menu.py            # Menu system
│   ├── constants.py       # Configuration and constants
│   ├── circleshape.py     # Base sprite class
│   ├── asteroidfield.py   # Asteroid spawner
│   ├── logger.py          # Event logging
│   └── __init__.py        # Package initialization
├── assets/                 # Game assets
│   └── images/
│       └── backgrounds/   # Background images
├── data/                   # Persistent data
│   └── high_score.json   # Saved high scores
├── run.py                 # Entry point script
├── pyproject.toml         # Project configuration
├── README.md              # This file
└── .gitignore             # Git exclusions
```

## Installation

### Prerequisites
- Python 3.13+
- pip or uv package manager

### Setup

1. Clone the repository:
```bash
git clone https://github.com/bootdotdev/asteroids_game.git
cd asteroids_game
```

2. Create and activate a virtual environment:
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -e .
# OR with uv:
uv sync
```

## Running the Game

### Using the provided run script:
```bash
python run.py
```

### Using uv:
```bash
uv run run.py
```

### Using Python directly:
```bash
python -m asteroids
```

## Controls

| Action | Key |
|--------|-----|
| Rotate Left | `LEFT ARROW` |
| Rotate Right | `RIGHT ARROW` |
| Thrust Forward | `UP ARROW` |
| Fire | `SPACE` |
| Switch Weapon | `1` / `2` / `3` |
| Drop Bomb | `B` |
| Pause Game | `ESC` |
| Debug Hitbox | `D` |

## Gameplay

### Weapons
- **Single (1)** - White bullets, standard fire rate
- **Spread (2)** - Green cone of 3 bullets
- **Rapid (3)** - Red bullets, fast fire rate

### Power-ups
- **Green Shield** - Absorbs one hit, glows when active

### Bomb
- **Explosive (B)** - 2-second fuse, damages all nearby asteroids

### Scoring
- Small Asteroid: 100 points
- Medium Asteroid: 50 points
- Large Asteroid: 20 points

## Code Comments

The code includes extensive comments explaining every major system, making it perfect for:
- Learning game development
- Understanding Pygame architecture
- Teaching high school students programming concepts

## Contributing

Contributions are welcome! Please feel free to submit pull requests or open issues.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Built with [Pygame](https://www.pygame.org/)
- Inspired by the classic [Asteroids](https://en.wikipedia.org/wiki/Asteroids_(video_game)) arcade game
- Developed for [Boot.dev](https://boot.dev/)

## Development Notes

### Modifying Game Constants

All game parameters can be adjusted in `src/asteroids/constants.py`:

```python
# Asteroid spawn rate (seconds)
ASTEROID_SPAWN_RATE_SECONDS = 0.8

# Player max speed
PLAYER_MAX_SPEED = 450

# Difficulty multipliers
DIFFICULTY_MULT = {
    DIFFICULTY_EASY: 0.7,      # 30% slower
    DIFFICULTY_NORMAL: 1.0,    # Standard
    DIFFICULTY_HARD: 1.5,      # 50% faster
}
```

### Adding New Assets

Place image files in:
- `assets/images/backgrounds/` - Background images

Place audio files in:
- `assets/sounds/` - Sound effects (future feature)

### Testing

From the project root:
```bash
python -m py_compile src/asteroids/*.py
```