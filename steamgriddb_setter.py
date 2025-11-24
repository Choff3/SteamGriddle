#!/usr/bin/env python3
"""
SteamGridDB Image Setter for Steam Shortcuts
Sets custom artwork for non-Steam games using SteamGridDB API
"""

import sys
import re
import requests
from pathlib import Path
from typing import List, Optional, Tuple
import argparse


class SteamGridDBAPI:
    """Handles all SteamGridDB API interactions"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://www.steamgriddb.com/api/v2"
        self.headers = {"Authorization": f"Bearer {api_key}"}
        
    def search_game(self, game_name: str) -> Optional[int]:
        """Search for a game and return its ID"""
        url = f"{self.base_url}/search/autocomplete/{game_name}"
        try:
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            data = response.json()
            
            if data.get("success") and data.get("data"):
                return data["data"][0]["id"]
        except Exception as e:
            print(f"      Error searching: {e}")
        return None
    
    def get_grid_image(self, game_id: int) -> Optional[str]:
        """Get grid image URL for a game"""
        url = f"{self.base_url}/grids/game/{game_id}"
        try:
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            data = response.json()
            
            if data.get("success") and data.get("data"):
                return data["data"][0]["url"]
        except Exception as e:
            print(f"      Error getting grid: {e}")
        return None
    
    def get_hero_image(self, game_id: int) -> Optional[str]:
        """Get hero/header image URL for a game"""
        url = f"{self.base_url}/heroes/game/{game_id}"
        try:
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            data = response.json()
            
            if data.get("success") and data.get("data"):
                return data["data"][0]["url"]
        except Exception as e:
            print(f"      Error getting hero: {e}")
        return None
    
    def get_logo_image(self, game_id: int) -> Optional[str]:
        """Get logo image URL for a game"""
        url = f"{self.base_url}/logos/game/{game_id}"
        try:
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            data = response.json()
            
            if data.get("success") and data.get("data"):
                return data["data"][0]["url"]
        except Exception as e:
            print(f"      Error getting logo: {e}")
        return None
    
    def download_image(self, url: str, output_path: Path) -> bool:
        """Download an image from URL to the specified path"""
        try:
            response = requests.get(url, stream=True)
            response.raise_for_status()
            
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            return True
        except Exception as e:
            print(f"      Error downloading: {e}")
            return False


class SteamShortcutManager:
    """Manages Steam shortcuts and grid artwork"""
    
    def __init__(self, steam_path: Optional[Path] = None):
        self.steam_path = steam_path or self.find_steam_path()
        if not self.steam_path:
            raise ValueError("Steam installation not found")
        
    def find_steam_path(self) -> Optional[Path]:
        """Find Steam installation path on Linux"""
        possible_paths = [
            Path.home() / ".steam" / "steam",
            Path.home() / ".local" / "share" / "Steam",
            Path("/usr/share/steam"),
        ]
        
        for path in possible_paths:
            if path.exists():
                return path
        return None
    
    def find_user_dirs(self) -> List[Path]:
        """Find all Steam user directories"""
        userdata_path = self.steam_path / "userdata"
        if not userdata_path.exists():
            return []
        
        return [d for d in userdata_path.iterdir() if d.is_dir() and d.name.isdigit()]
    
    def get_non_steam_games(self, user_dir: Path) -> List[Tuple[str, str, int, int]]:
        """
        Extract non-Steam game information from shortcuts.vdf
        Returns: List of (name, exe, app_id, grid_id) tuples
        
        Based on: https://stackoverflow.com/a/67406750
        Posted by kirksaunders, modified by community
        Retrieved 2024-11-24, License - CC BY-SA 4.0
        """
        shortcut_path = user_dir / "config" / "shortcuts.vdf"
        if not shortcut_path.is_file():
            return []
        
        try:
            shortcut_bytes = shortcut_path.read_bytes()
            
            # Regex pattern to extract shortcut information from binary VDF
            game_pattern = re.compile(
                rb"\x00\x02appid\x00(.{4})\x01appname\x00([^\x08]+?)\x00\x01exe\x00([^\x08]+?)\x00\x01.+?\x00tags\x00(?:\x01([^\x08]+?)|)\x08\x08",
                flags=re.DOTALL | re.IGNORECASE
            )
            
            games = []
            for game_match in game_pattern.findall(shortcut_bytes):
                # Extract app ID (4-byte little-endian unsigned integer)
                app_id = int.from_bytes(game_match[0], byteorder='little', signed=False)
                name = game_match[1].decode('utf-8')
                exe = game_match[2].decode('utf-8')
                
                # Calculate grid ID: (app_id << 32) | 0x02000000
                grid_id = (app_id << 32) | 0x02000000
                
                games.append((name, exe, app_id, grid_id))
            
            return games
            
        except Exception as e:
            print(f"  Error reading shortcuts: {e}")
            return []


def main():
    parser = argparse.ArgumentParser(
        description="Set SteamGridDB artwork for Steam shortcuts",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Set artwork for all non-Steam games
  %(prog)s --api-key YOUR_KEY
  
  # List shortcuts without downloading
  %(prog)s --api-key YOUR_KEY --list-shortcuts
  
  # Process only a specific game
  %(prog)s --api-key YOUR_KEY --game-name "Spider-Man"
        """
    )
    parser.add_argument(
        "--api-key",
        required=True,
        help="SteamGridDB API key (get from https://www.steamgriddb.com/profile/preferences/api)"
    )
    parser.add_argument(
        "--steam-path",
        type=Path,
        help="Override Steam installation path"
    )
    parser.add_argument(
        "--game-name",
        help="Process only this specific game (case-insensitive partial match)"
    )
    parser.add_argument(
        "--list-shortcuts",
        action="store_true",
        help="List all shortcuts and their IDs without downloading images"
    )
    
    args = parser.parse_args()
    
    # Initialize
    try:
        sgdb = SteamGridDBAPI(args.api_key)
        steam = SteamShortcutManager(args.steam_path)
    except ValueError as e:
        print(f"Error: {e}")
        return 1
    
    print(f"Steam path: {steam.steam_path}\n")
    
    # Process each user
    user_dirs = steam.find_user_dirs()
    if not user_dirs:
        print("No Steam user directories found")
        return 1
    
    total_processed = 0
    
    for user_dir in user_dirs:
        print(f"Processing user: {user_dir.name}")
        
        # Get non-Steam games
        games = steam.get_non_steam_games(user_dir)
        if not games:
            print("  No shortcuts found\n")
            continue
        
        print(f"  Found {len(games)} shortcut(s)\n")
        
        grid_path = user_dir / "config" / "grid"
        
        for name, exe, app_id, grid_id in games:
            # Filter by game name if specified
            if args.game_name and args.game_name.lower() not in name.lower():
                continue
            
            print(f"  [{name}]")
            print(f"    App ID: {app_id}")
            
            # If just listing, check for existing files
            if args.list_shortcuts:
                if grid_path.exists():
                    matching_files = list(grid_path.glob(f"{app_id}*"))
                    if matching_files:
                        print(f"    Existing files:")
                        for f in sorted(matching_files):
                            print(f"      - {f.name}")
                    else:
                        print(f"    No existing grid files")
                print()
                continue
            
            # Search on SteamGridDB
            print(f"    Searching SteamGridDB...")
            game_id = sgdb.search_game(name)
            if not game_id:
                print(f"    ✗ Not found on SteamGridDB\n")
                continue
            
            print(f"    Found (SGDB ID: {game_id})")
            
            # Get artwork URLs
            grid_url = sgdb.get_grid_image(game_id)
            hero_url = sgdb.get_hero_image(game_id)
            logo_url = sgdb.get_logo_image(game_id)
            
            if not grid_url:
                print(f"    ✗ No artwork available\n")
                continue
            
            # Download artwork
            success_count = 0
            
            # Grid image (library view)
            if grid_url:
                grid_file = grid_path / f"{app_id}p.png"
                print(f"    Downloading grid → {grid_file.name}")
                if sgdb.download_image(grid_url, grid_file):
                    print(f"      ✓ Saved")
                    success_count += 1
            
            # Hero image (big picture mode)
            if hero_url:
                hero_file = grid_path / f"{app_id}_hero.png"
                print(f"    Downloading hero → {hero_file.name}")
                if sgdb.download_image(hero_url, hero_file):
                    print(f"      ✓ Saved")
                    success_count += 1
            
            # Logo image (overlay on hero)
            if logo_url:
                logo_file = grid_path / f"{app_id}_logo.png"
                print(f"    Downloading logo → {logo_file.name}")
                if sgdb.download_image(logo_url, logo_file):
                    print(f"      ✓ Saved")
                    success_count += 1
            
            if success_count > 0:
                print(f"    ✓ Complete ({success_count} image(s))")
                total_processed += 1
            
            print()
    
    if not args.list_shortcuts:
        if total_processed > 0:
            print(f"✓ Successfully processed {total_processed} game(s)")
            print("  Restart Steam to see the changes!")
        else:
            print("No games were processed")
    
    return 0


if __name__ == "__main__":
    try:
        import requests
    except ImportError:
        print("Error: Missing required dependency 'requests'")
        print("\nInstall with: pip install requests")
        sys.exit(1)
    
    sys.exit(main())