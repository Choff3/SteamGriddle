#!/usr/bin/env python3
"""
SteamGridDB Image Setter for Steam Shortcuts
Sets custom artwork for non-Steam games using SteamGridDB API
"""

import sys
import re
import json
import requests
from pathlib import Path
from typing import List, Tuple, Optional
import argparse


class Config:
    """Configuration manager"""
    
    DEFAULT_CONFIG = {
        "api_key": "",
        "image_types": {
            "grid": True,
            "hero": True,
            "logo": True,
            "wide": True
        }
    }
    
    def __init__(self, config_path: Path):
        self.config_path = config_path
        self.data = self.load()
    
    def load(self) -> dict:
        """Load configuration from file"""
        if self.config_path.exists():
            try:
                with open(self.config_path) as f:
                    return {**self.DEFAULT_CONFIG, **json.load(f)}
            except Exception as e:
                print(f"Warning: Could not load config: {e}")
        return self.DEFAULT_CONFIG.copy()
    
    def save(self):
        """Save configuration to file"""
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.config_path, 'w') as f:
            json.dump(self.data, f, indent=2)
    
    def get(self, key: str, default=None):
        """Get configuration value"""
        return self.data.get(key, default)
    
    def set(self, key: str, value):
        """Set configuration value"""
        self.data[key] = value


class SteamGridDB:
    """SteamGridDB API client"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://www.steamgriddb.com/api/v2"
        self.headers = {"Authorization": f"Bearer {api_key}"}
    
    def search(self, game_name: str) -> Optional[int]:
        """Search for a game and return its ID"""
        try:
            response = requests.get(
                f"{self.base_url}/search/autocomplete/{game_name}",
                headers=self.headers
            )
            response.raise_for_status()
            data = response.json()
            return data["data"][0]["id"] if data.get("success") and data.get("data") else None
        except Exception as e:
            print(f"      Search error: {e}")
            return None
    
    def get_artwork(self, game_id: int, art_type: str) -> Optional[str]:
        """Get artwork URL for a game (grid, heroes, or logos)"""
        try:
            response = requests.get(
                f"{self.base_url}/{art_type}/game/{game_id}",
                headers=self.headers
            )
            response.raise_for_status()
            data = response.json()
            return data["data"][0]["url"] if data.get("success") and data.get("data") else None
        except:
            return None
    
    def download(self, url: str, output_path: Path) -> bool:
        """Download an image from URL"""
        try:
            response = requests.get(url, stream=True)
            response.raise_for_status()
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            return True
        except Exception as e:
            print(f"      Download error: {e}")
            return False


class SteamManager:
    """Steam shortcuts manager"""
    
    def __init__(self, steam_path: Optional[Path] = None):
        self.steam_path = steam_path or self._find_steam_path()
        if not self.steam_path:
            raise ValueError("Steam installation not found")
    
    def _find_steam_path(self) -> Optional[Path]:
        """Find Steam installation path on Linux"""
        for path in [
            Path.home() / ".steam" / "steam",
            Path.home() / ".local" / "share" / "Steam",
        ]:
            if path.exists():
                return path
        return None
    
    def get_user_dirs(self) -> List[Path]:
        """Find all Steam user directories"""
        userdata = self.steam_path / "userdata"
        return [d for d in userdata.iterdir() if d.is_dir() and d.name.isdigit()] if userdata.exists() else []
    
    def get_shortcuts(self, user_dir: Path) -> List[Tuple[str, str, int]]:
        """
        Extract non-Steam games from shortcuts.vdf
        Returns: List of (name, exe, app_id) tuples
        """
        shortcuts_path = user_dir / "config" / "shortcuts.vdf"
        if not shortcuts_path.is_file():
            return []
        
        try:
            shortcuts_bytes = shortcuts_path.read_bytes()
            pattern = re.compile(
                rb"\x00\x02appid\x00(.{4})\x01appname\x00([^\x08]+?)\x00\x01exe\x00([^\x08]+?)\x00\x01.+?\x00tags\x00(?:\x01([^\x08]+?)|)\x08\x08",
                flags=re.DOTALL | re.IGNORECASE
            )
            
            games = []
            for match in pattern.findall(shortcuts_bytes):
                app_id = int.from_bytes(match[0], byteorder='little', signed=False)
                name = match[1].decode('utf-8')
                exe = match[2].decode('utf-8')
                games.append((name, exe, app_id))
            
            return games
        except Exception as e:
            print(f"  Error reading shortcuts: {e}")
            return []


def setup_config(config_path: Path) -> Config:
    """Interactive configuration setup"""
    config = Config(config_path)
    
    if not config.get("api_key"):
        print("First time setup - please provide your configuration:\n")
        api_key = input("SteamGridDB API key (from https://www.steamgriddb.com/profile/preferences/api): ").strip()
        if api_key:
            config.set("api_key", api_key)
            config.save()
            print(f"\n✓ Configuration saved to {config_path}")
        else:
            print("\nError: API key is required")
            sys.exit(1)
    
    return config


def main():
    parser = argparse.ArgumentParser(description="Set SteamGridDB artwork for Steam shortcuts")
    parser.add_argument("--config", type=Path, default=Path.home() / ".config" / "steamgriddb" / "config.json",
                        help="Config file path")
    parser.add_argument("--api-key", help="SteamGridDB API key (overrides config)")
    parser.add_argument("--steam-path", type=Path, help="Steam installation path (overrides config)")
    parser.add_argument("--game", help="Process only this game (case-insensitive partial match)")
    parser.add_argument("--list", action="store_true", help="List shortcuts without downloading")
    parser.add_argument("--setup", action="store_true", help="Run configuration setup")
    
    args = parser.parse_args()
    
    # Load/setup config
    config = Config(args.config)
    if args.setup or not config.get("api_key"):
        config = setup_config(args.config)
    
    # Get API key
    api_key = args.api_key or config.get("api_key")
    if not api_key:
        print("Error: No API key provided. Run with --setup or use --api-key")
        return 1
    
    # Initialize
    try:
        steam_path = args.steam_path or (Path(config.get("steam_path")) if config.get("steam_path") else None)
        sgdb = SteamGridDB(api_key)
        steam = SteamManager(steam_path)
    except ValueError as e:
        print(f"Error: {e}")
        return 1
    
    print(f"Steam: {steam.steam_path}\n")
    
    # Process users
    user_dirs = steam.get_user_dirs()
    if not user_dirs:
        print("No Steam users found")
        return 1
    
    image_types = config.get("image_types", {})
    total = 0
    
    for user_dir in user_dirs:
        print(f"User: {user_dir.name}")
        shortcuts = steam.get_shortcuts(user_dir)
        
        if not shortcuts:
            print("  No shortcuts\n")
            continue
        
        print(f"  {len(shortcuts)} shortcut(s)\n")
        grid_path = user_dir / "config" / "grid"
        
        for name, exe, app_id in shortcuts:
            if args.game and args.game.lower() not in name.lower():
                continue
            
            print(f"  [{name}]")
            print(f"    App ID: {app_id}")
            
            if args.list:
                if grid_path.exists():
                    files = sorted(grid_path.glob(f"{app_id}*"))
                    if files:
                        print(f"    Files: {', '.join(f.name for f in files)}")
                print()
                continue
            
            # Search and download
            print(f"    Searching...")
            game_id = sgdb.search(name)
            if not game_id:
                print(f"    ✗ Not found\n")
                continue
            
            count = 0
            
            # Grid image (vertical/portrait)
            if image_types.get("grid", True):
                if url := sgdb.get_artwork(game_id, "grids"):
                    file = grid_path / f"{app_id}p.png"
                    if sgdb.download(url, file):
                        print(f"    ✓ Grid")
                        count += 1
            
            # Wide cover (horizontal capsule)
            if image_types.get("wide", True):
                if url := sgdb.get_artwork(game_id, "grids"):
                    file = grid_path / f"{app_id}.png"
                    if sgdb.download(url, file):
                        print(f"    ✓ Wide")
                        count += 1
            
            # Hero image (background)
            if image_types.get("hero", True):
                if url := sgdb.get_artwork(game_id, "heroes"):
                    file = grid_path / f"{app_id}_hero.png"
                    if sgdb.download(url, file):
                        print(f"    ✓ Hero")
                        count += 1
            
            # Logo image (overlay)
            if image_types.get("logo", True):
                if url := sgdb.get_artwork(game_id, "logos"):
                    file = grid_path / f"{app_id}_logo.png"
                    if sgdb.download(url, file):
                        print(f"    ✓ Logo")
                        count += 1
            
            if count > 0:
                total += 1
            print()
    
    if not args.list and total > 0:
        print(f"✓ Processed {total} game(s). Restart Steam to see changes!")
    
    return 0


if __name__ == "__main__":
    try:
        import requests
    except ImportError:
        print("Error: Install required dependency with: pip install requests")
        sys.exit(1)
    
    sys.exit(main())