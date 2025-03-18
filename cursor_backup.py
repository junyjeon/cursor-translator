import os
import shutil
import datetime
from pathlib import Path

def create_backup(file_path, backup_dir=None):
    """파일 백업 생성"""
    if not file_path or not os.path.exists(file_path):
        return None
    
    # 백업 디렉토리 생성
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    if not backup_dir:
        backup_dir = Path(f"cursor_backup_{timestamp}")
    
    os.makedirs(backup_dir, exist_ok=True)
    
    # 파일 복사
    backup_path = backup_dir / f"{os.path.basename(file_path)}.backup"
    shutil.copy2(file_path, backup_path)
    
    return backup_path

def backup_cursor_files(main_js_path, settings_path, output_dir=None):
    """Cursor 관련 파일 백업"""
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_dir = Path(output_dir) if output_dir else Path(f"cursor_backup_{timestamp}")
    os.makedirs(backup_dir, exist_ok=True)
    
    backup_info = {
        'timestamp': timestamp,
        'files': []
    }
    
    # main.js 백업
    if main_js_path and os.path.exists(main_js_path):
        js_backup = create_backup(main_js_path, backup_dir)
        if js_backup:
            backup_info['files'].append({
                'original': str(main_js_path),
                'backup': str(js_backup)
            })
    
    # settings.json 백업
    if settings_path and os.path.exists(settings_path):
        settings_backup = create_backup(settings_path, backup_dir)
        if settings_backup:
            backup_info['files'].append({
                'original': str(settings_path),
                'backup': str(settings_backup)
            })
    
    # README 파일 생성
    with open(backup_dir / "README.txt", "w", encoding="utf-8") as f:
        f.write(f"Cursor 설정 백업 ({datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')})\n\n")
        f.write("이 폴더에는 Cursor 설정 번역 전에 백업된 파일이 포함되어 있습니다.\n")
        f.write("문제가 발생할 경우 이 파일들을 원래 위치로 복원하세요.\n\n")
        f.write("백업된 파일:\n")
        
        for file_info in backup_info['files']:
            f.write(f"- {os.path.basename(file_info['original'])}\n")
            f.write(f"  원본 위치: {file_info['original']}\n")
            f.write(f"  백업 위치: {file_info['backup']}\n\n")
    
    return backup_dir if backup_info['files'] else None
