import os
import sys
import shutil
import subprocess
from pathlib import Path

def build_exe():
    """PyInstaller를 사용하여 EXE 파일 생성"""
    print("=" * 60)
    print("Cursor 다국어 번역 도구 - EXE 빌드 스크립트")
    print("=" * 60)
    
    # 필요한 파일 존재 확인
    required_files = [
        "main.py", 
        "cursor_finder.py", 
        "cursor_backup.py", 
        "cursor_extractor.py", 
        "cursor_translator.py"
    ]
    
    missing_files = [f for f in required_files if not os.path.exists(f)]
    if missing_files:
        print(f"오류: 다음 필수 파일이 없습니다: {', '.join(missing_files)}")
        return False
    
    # PyInstaller 설치 확인 및 설치
    try:
        import PyInstaller
        print("PyInstaller 설치 확인됨")
    except ImportError:
        print("PyInstaller 설치 중...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])
            print("PyInstaller 설치 완료")
        except Exception as e:
            print(f"PyInstaller 설치 실패: {e}")
            return False
    
    # 필요한 의존성 설치
    print("\n필요한 라이브러리 설치 중...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "requests"])
        print("라이브러리 설치 완료")
    except Exception as e:
        print(f"라이브러리 설치 실패: {e}")
        return False
    
    # 빌드 디렉토리 생성
    build_dir = "build"
    if not os.path.exists(build_dir):
        os.makedirs(build_dir)
    
    # 아이콘 생성 (optional)
    icon_path = None
    try:
        # PIL 설치 확인
        try:
            from PIL import Image, ImageDraw
        except ImportError:
            print("Pillow 설치 중...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", "pillow"])
            from PIL import Image, ImageDraw
        
        print("\nPIL로 아이콘 생성 중...")
        icon_path = os.path.join(build_dir, "cursor_icon.ico")
        
        # 간단한 아이콘 생성
        img = Image.new('RGBA', (256, 256), color=(30, 30, 30, 255))
        draw = ImageDraw.Draw(img)
        
        # 'C' 문자 그리기
        draw.ellipse((48, 48, 208, 208), fill=(0, 120, 212, 255))
        draw.ellipse((78, 78, 178, 178), fill=(30, 30, 30, 255))
        draw.rectangle((128, 78, 198, 178), fill=(30, 30, 30, 255))
        
        # 저장
        img.save(icon_path, format='ICO')
        print(f"아이콘 생성 완료: {icon_path}")
    except Exception as e:
        print(f"아이콘 생성 실패 (무시됨): {e}")
        icon_path = None
    
    # spec 파일 생성
    print("\nPyInstaller spec 파일 생성 중...")
    spec_content = f'''# -*- mode: python ; coding: utf-8 -*-

import os

block_cipher = None

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={{}},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

# 번역 파일 추가
translation_files = []
for file in os.listdir('.'):
    if file.startswith('cursor_translations_') and file.endswith('.json'):
        translation_files.append((file, '.'))

a.datas.extend(translation_files)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='Cursor다국어번역도구',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    {f"icon='{icon_path}'," if icon_path else ""}
)
'''
    
    spec_path = os.path.join(build_dir, "cursor_translator.spec")
    with open(spec_path, "w", encoding="utf-8") as f:
        f.write(spec_content)
    
    # PyInstaller 실행
    print("\nEXE 파일 빌드 중... (이 작업은 몇 분 정도 소요될 수 있습니다)")
    try:
        subprocess.check_call([
            sys.executable, 
            "-m", 
            "PyInstaller", 
            "--clean",
            spec_path
        ])
        
        # 결과 파일 확인 및 복사
        dist_path = os.path.join("dist", "Cursor다국어번역도구.exe")
        if os.path.exists(dist_path):
            output_path = "Cursor다국어번역도구.exe"
            shutil.copy2(dist_path, output_path)
            print(f"\n빌드 성공! '{output_path}' 파일이 생성되었습니다.")
            
            # 사용법 안내
            print("\n사용 방법:")
            print("1. 생성된 EXE 파일을 더블클릭하여 실행하세요.")
            print("2. 도움말을 보려면 명령 프롬프트에서 다음과 같이 실행하세요:")
            print("   Cursor다국어번역도구.exe --help")
            print("\nDeepL API 키 없이도 기본 번역을 사용할 수 있습니다.")
            
            return True
        else:
            print("\n빌드 실패: EXE 파일을 찾을 수 없습니다.")
            return False
            
    except Exception as e:
        print(f"\nEXE 빌드 중 오류 발생: {e}")
        return False

if __name__ == "__main__":
    build_exe()