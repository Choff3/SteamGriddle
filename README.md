# SteamGriddle

Automatically download and set custom artwork for non-Steam games using the SteamGridDB API.

## Features

- 🎨 Automatically fetches high-quality artwork from SteamGridDB
- 🖼️ Downloads multiple image types: Grid, Wide Cover, Hero, and Logo
- ⚙️ Simple configuration file for API key and preferences
- 🎯 Filter by game name for selective updates
- 📋 List mode to view shortcuts without downloading

## Prerequisites

- Python 3.7+
- Steam installed
- SteamGridDB API key (free)

## Installation

1. Clone or download this repository:
```bash
git clone https://github.com/Choff3/SteamGriddle.git
cd steamgriddb-setter
```

2. Install dependencies:
```bash
pip install requests
```

3. Get your SteamGridDB API key:
   - Visit https://www.steamgriddb.com/profile/preferences/api
   - Create a free account if needed
   - Generate an API key

## Quick Start

### First Time Setup

Run the interactive setup:
```bash
python3 steamgriddle.py --setup
```

This will prompt you for your API key and save it to `~/.config/steamgriddb/config.json`.

### Basic Usage

Download artwork for all non-Steam games:
```bash
python3 steamgriddle.py
```

After running, **restart Steam** to see the changes!

## Usage Examples

### List all shortcuts without downloading
```bash
python3 steamgriddle.py --list
```

### Update artwork for a specific game
```bash
python3 steamgriddle.py --game "Marvel's Spider-Man 2"
```

### Use a custom config file
```bash
python3 steamgriddle.py --config /path/to/config.json
```

### Override API key from command line
```bash
python3 steamgriddle.py --api-key YOUR_API_KEY
```

### Specify custom Steam path
```bash
python3 steamgriddle.py --steam-path /custom/steam/path
```

## Configuration

The configuration file is stored at `~/.config/steamgriddb/config.json`:

```json
{
  "api_key": "your_api_key_here",
  "image_types": {
    "grid": true,
    "hero": true,
    "logo": true,
    "wide": true
  }
}
```

### Image Types

- **grid**: Vertical/portrait image for library grid view (`{app_id}p.png`)
- **wide**: Horizontal capsule image (`{app_id}.png`)
- **hero**: Large background image for detail view (`{app_id}_hero.png`)
- **logo**: Transparent logo overlay (`{app_id}_logo.png`)

Set any to `false` to skip downloading that image type.

## Command Line Options

```
Options:
  --config PATH       Config file path (default: ~/.config/steamgriddb/config.json)
  --api-key KEY       SteamGridDB API key (overrides config)
  --steam-path PATH   Steam installation path (overrides auto-detection)
  --game NAME         Process only this game (case-insensitive partial match)
  --list              List shortcuts without downloading images
  --setup             Run interactive configuration setup
  -h, --help          Show help message
```

## How It Works

1. **Reads Steam shortcuts**: Parses `~/.steam/steam/userdata/*/config/shortcuts.vdf` to find non-Steam games
2. **Extracts App IDs**: Gets the internal App ID Steam uses for each shortcut
3. **Searches SteamGridDB**: Finds matching games on SteamGridDB
4. **Downloads artwork**: Fetches grid, wide, hero, and logo images
5. **Saves to grid directory**: Stores images in `~/.steam/steam/userdata/*/config/grid/` with correct filenames

## Troubleshooting

### Images not showing in Steam

- Make sure you've restarted Steam after running the script
- Verify the files were created: `ls ~/.steam/steam/userdata/*/config/grid/`
- Check that filenames match the App ID format: `{app_id}p.png`, `{app_id}.png`, etc.

### "Steam installation not found"

- Specify the Steam path manually: `--steam-path ~/.local/share/Steam`
- The script looks in: `~/.steam/steam` and `~/.local/share/Steam`

### "No shortcuts found"

- Make sure you have non-Steam games added to your Steam library
- Check that `shortcuts.vdf` exists: `ls ~/.steam/steam/userdata/*/config/shortcuts.vdf`

### Game not found on SteamGridDB or wrong game matched

- The shortcut name must match the entry on [SteamGridDB](https://www.steamgriddb.com)
- Try using `--game` with a different name variant

## File Locations

- **Config**: `~/.config/steamgriddb/config.json`
- **Steam shortcuts**: `~/.steam/steam/userdata/{user_id}/config/shortcuts.vdf`
- **Grid images**: `~/.steam/steam/userdata/{user_id}/config/grid/`

## Credits

- Artwork provided by [SteamGridDB](https://www.steamgriddb.com)
- Project created using Claude Sonnet 4.5

## Contributing

Contributions are welcome! Feel free to open issues or submit pull requests.
