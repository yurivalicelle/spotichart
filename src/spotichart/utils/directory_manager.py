from pathlib import Path
import os
import shutil

class DirectoryManager:
    @staticmethod
    def ensure_directory_exists(path: Path, create: bool = False) -> bool:
        if path.exists():
            return True
        if create:
            path.mkdir(parents=True, exist_ok=True)
            return True
        return False

    @staticmethod
    def setup_app_directories(app_name: str):
        home = Path.home()
        base_dir = home / f'.{app_name}'
        cache_dir = base_dir / 'cache'
        logs_dir = base_dir / 'logs'
        
        base_dir.mkdir(exist_ok=True)
        cache_dir.mkdir(exist_ok=True)
        logs_dir.mkdir(exist_ok=True)
        
        return {'base': base_dir, 'cache': cache_dir, 'logs': logs_dir}

    @staticmethod
    def clean_directory(path: Path, keep_structure: bool = True):
        if not path.exists():
            return
        if keep_structure:
            for item in path.iterdir():
                if item.is_file():
                    item.unlink()
                elif item.is_dir():
                    shutil.rmtree(item)
        else:
            shutil.rmtree(path)

    @staticmethod
    def is_writable(path: Path) -> bool:
        return os.access(path, os.W_OK)

    @staticmethod
    def get_directory_size(path: Path) -> int:
        total_size = 0
        for dirpath, _, filenames in os.walk(path):
            for f in filenames:
                fp = os.path.join(dirpath, f)
                if not os.path.islink(fp):
                    total_size += os.path.getsize(fp)
        return total_size
