import os
import platform
import subprocess
from pathlib import Path

def find_cursor_installation():
    """OS별 Cursor IDE 설치 경로 찾기"""
    system = platform.system()
    
    # Windows
    if system == "Windows":
        appdata = os.environ.get('LOCALAPPDATA')
        return Path(appdata) / 'Programs' / 'cursor'
    
    # macOS
    elif system == "Darwin":
        if os.path.exists('/Applications/Cursor.app'):
            return Path('/Applications/Cursor.app')
    
    # Linux & WSL
    elif system == "Linux":
        # WSL 감지
        is_wsl = False
        try:
            with open('/proc/version', 'r') as f:
                if 'Microsoft' in f.read():
                    is_wsl = True
        except:
            pass
        
        if is_wsl:
            # WSL에서 Windows 사용자 이름 찾기
            try:
                username = os.environ.get('USER')
                wsl_path = Path(f'/mnt/c/Users/{username}/AppData/Local/Programs/cursor')
                if wsl_path.exists():
                    return wsl_path
            except:
                pass
            
            # 대체 접근법: Windows 사용자명 확인
            try:
                whoami = subprocess.check_output(['cmd.exe', '/c', 'echo %USERNAME%'], text=True).strip()
                wsl_path = Path(f'/mnt/c/Users/{whoami}/AppData/Local/Programs/cursor')
                if wsl_path.exists():
                    return wsl_path
            except:
                pass
        
        # 일반 Linux 경로
        home = os.environ.get('HOME')
        linux_paths = [
            Path(home) / '.local' / 'share' / 'cursor',
            Path('/opt/cursor')
        ]
        for path in linux_paths:
            if path.exists():
                return path
    
    return None

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
