import os
import sys
import glob
import subprocess
import platform
import json
from pathlib import Path

class CursorFinder:
    def __init__(self):
        self.system = platform.system().lower()
        self.cache_file = Path.home() / '.cursor_translator' / 'path_cache.json'
        self.cache_file.parent.mkdir(parents=True, exist_ok=True)

    def _load_cached_path(self):
        """캐시된 경로를 로드합니다."""
        if self.cache_file.exists():
            try:
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    cache = json.load(f)
                    if cache.get('path') and os.path.exists(cache['path']):
                        return cache['path']
            except Exception:
                pass
        return None

    def _save_cached_path(self, path):
        """경로를 캐시에 저장합니다."""
        try:
            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump({'path': path}, f, ensure_ascii=False)
        except Exception:
            pass

    def _is_valid_cursor_path(self, path):
        """Cursor 설치 경로가 유효한지 확인합니다."""
        if not path:
            return False
        
        path = Path(path)
        if self.system == 'windows':
            # Windows에서의 검증
            if not path.exists():
                return False
            workbench_path = path / 'resources' / 'app' / 'out' / 'vs' / 'workbench'
            return (workbench_path / 'workbench.desktop.main.js').exists()
        else:
            # Linux/macOS에서의 검증
            if not path.exists():
                return False
            workbench_path = path / 'resources' / 'app' / 'out' / 'vs' / 'workbench'
            return (workbench_path / 'workbench.desktop.main.js').exists()

    def _find_in_windows(self):
        """Windows에서 Cursor 설치 경로를 찾습니다."""
        possible_paths = []
        
        # 1. 기본 설치 경로 확인
        program_files = [
            os.environ.get('LOCALAPPDATA', ''),
            os.environ.get('PROGRAMFILES', ''),
            os.environ.get('PROGRAMFILES(X86)', '')
        ]
        
        for base in program_files:
            if base:
                cursor_path = os.path.join(base, 'Programs', 'cursor')
                if self._is_valid_cursor_path(cursor_path):
                    return cursor_path
                possible_paths.append(cursor_path)

        # 2. 사용자별 AppData 경로 확인
        appdata = os.environ.get('APPDATA', '')
        if appdata:
            local_appdata = os.path.join(os.path.dirname(appdata), 'Local')
            cursor_path = os.path.join(local_appdata, 'Programs', 'cursor')
            if self._is_valid_cursor_path(cursor_path):
                return cursor_path
            possible_paths.append(cursor_path)

        # 3. 시작 메뉴에서 검색
        try:
            start_menu = os.path.join(os.environ.get('APPDATA', ''), 'Microsoft', 'Windows', 'Start Menu', 'Programs')
            if os.path.exists(start_menu):
                for root, _, files in os.walk(start_menu):
                    for file in files:
                        if file.lower() == 'cursor.lnk':
                            possible_paths.append(os.path.dirname(os.path.join(root, file)))
        except Exception:
            pass

        # 4. 레지스트리에서 검색 (Windows 전용)
        try:
            import winreg
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Uninstall\Cursor") as key:
                install_location = winreg.QueryValueEx(key, "InstallLocation")[0]
                if self._is_valid_cursor_path(install_location):
                    return install_location
                possible_paths.append(install_location)
        except Exception:
            pass

        return None

    def _find_in_wsl(self):
        """WSL에서 Cursor 설치 경로를 찾습니다."""
        possible_paths = []
        
        # 1. /mnt/c/Users/ 아래의 모든 사용자 디렉토리 검색
        users_dir = '/mnt/c/Users'
        if os.path.exists(users_dir):
            for user in os.listdir(users_dir):
                user_path = os.path.join(users_dir, user)
                if os.path.isdir(user_path):
                    # AppData 경로 확인
                    appdata_path = os.path.join(user_path, 'AppData', 'Local', 'Programs', 'cursor')
                    if self._is_valid_cursor_path(appdata_path):
                        return appdata_path
                    possible_paths.append(appdata_path)

        # 2. workbench.desktop.main.js 파일 직접 검색
        try:
            find_cmd = ['find', '/mnt/c', '-name', 'workbench.desktop.main.js', '-type', 'f']
            result = subprocess.run(find_cmd, capture_output=True, text=True)
            if result.returncode == 0:
                for path in result.stdout.splitlines():
                    if 'workbench' in path:
                        cursor_path = path.split('/workbench')[0]
                        if self._is_valid_cursor_path(cursor_path):
                            return cursor_path
                        possible_paths.append(cursor_path)
        except Exception:
            pass

        return None

    def _find_in_linux(self):
        """Linux에서 Cursor 설치 경로를 찾습니다."""
        possible_paths = []
        
        # 1. 기본 설치 경로 확인
        default_paths = [
            '/opt/cursor',
            os.path.expanduser('~/.local/share/cursor'),
            '/usr/share/cursor',
            '/usr/local/share/cursor'
        ]
        
        for path in default_paths:
            if self._is_valid_cursor_path(path):
                return path
            possible_paths.append(path)

        # 2. workbench.desktop.main.js 파일 검색
        try:
            find_cmd = ['find', '/', '-name', 'workbench.desktop.main.js', '-type', 'f']
            result = subprocess.run(find_cmd, capture_output=True, text=True)
            if result.returncode == 0:
                for path in result.stdout.splitlines():
                    if 'workbench' in path:
                        cursor_path = path.split('/workbench')[0]
                        if self._is_valid_cursor_path(cursor_path):
                            return cursor_path
                        possible_paths.append(cursor_path)
        except Exception:
            pass

        return None

    def find_cursor_installation(self):
        """Cursor 설치 경로를 찾습니다."""
        # 1. 캐시된 경로 확인
        cached_path = self._load_cached_path()
        if cached_path:
            return cached_path

        # 2. 환경 변수 확인
        env_path = os.environ.get('CURSOR_PATH')
        if env_path and self._is_valid_cursor_path(env_path):
            self._save_cached_path(env_path)
            return env_path

        # 3. 시스템별 검색
        if self.system == 'windows':
            path = self._find_in_windows()
        elif 'microsoft-standard-wsl' in platform.uname().release.lower():
            path = self._find_in_wsl()
        else:
            path = self._find_in_linux()

        if path:
            self._save_cached_path(path)
            return path

        return None

def main():
    finder = CursorFinder()
    path = finder.find_cursor_installation()
    if path:
        print(f"Cursor 설치 경로: {path}")
    else:
        print("Cursor 설치 경로를 찾을 수 없습니다.")
        print("다음 방법을 시도해보세요:")
        print("1. --cursor-path 옵션으로 직접 경로 지정")
        print("2. CURSOR_PATH 환경 변수 설정")
        print("3. Cursor가 올바르게 설치되어 있는지 확인")

if __name__ == '__main__':
    main()

def find_main_js_file(cursor_path):
    """workbench.desktop.main.js 파일 찾기"""
    if not cursor_path:
        return None
    
    # 가장 일반적인 경로 확인
    js_path = cursor_path / 'resources' / 'app' / 'out' / 'vs' / 'workbench' / 'workbench.desktop.main.js'
    if js_path.exists():
        return js_path
    
    # 파일 검색
    for path in cursor_path.glob('**/*.js'):
        if path.name == 'workbench.desktop.main.js':
            return path
    
    return None

def find_settings_json():
    """Cursor 설정 파일 경로 찾기"""
    system = platform.system()
    
    # Windows
    if system == "Windows":
        return Path(os.environ.get('APPDATA')) / 'Cursor' / 'User' / 'settings.json'
    
    # macOS
    elif system == "Darwin":
        return Path(os.environ.get('HOME')) / 'Library' / 'Application Support' / 'Cursor' / 'User' / 'settings.json'
    
    # Linux 및 WSL
    elif system == "Linux":
        # WSL 여부 확인
        try:
            with open('/proc/version', 'r') as f:
                if 'Microsoft' in f.read():
                    # WSL일 경우 Windows 경로 사용
                    username = os.environ.get('USER')
                    return Path(f'/mnt/c/Users/{username}/AppData/Roaming/Cursor/User/settings.json')
        except:
            pass
        
        # 일반 Linux 경로
        return Path(os.environ.get('HOME')) / '.config' / 'Cursor' / 'User' / 'settings.json'
    
    return None
