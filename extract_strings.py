#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import re
import json
import argparse
import platform
import subprocess
from pathlib import Path
from shutil import which

def find_cursor_installation():
    """Cursor IDE 설치 경로 찾기"""
    # 사용자가 지정한 경로가 있으면 사용
    user_path = os.environ.get('CURSOR_PATH')
    if user_path and Path(user_path).exists():
        return Path(user_path)
    
    # Windows
    if platform.system() == 'Windows':
        possible_paths = [
            Path(os.environ.get('LOCALAPPDATA', '')) / 'Programs' / 'cursor',
            Path(os.environ.get('PROGRAMFILES', '')) / 'cursor',
            Path(os.environ.get('PROGRAMFILES(X86)', '')) / 'cursor'
        ]
    # macOS
    elif platform.system() == 'Darwin':
        possible_paths = [
            Path('/Applications/Cursor.app/Contents/Resources/app')
        ]
    # WSL
    elif 'microsoft' in platform.uname().release.lower():
        # 일반적인 WSL 마운트 경로
        possible_paths = []
        
        # 모든 사용자 디렉토리 검색
        users_dir = Path('/mnt/c/Users')
        if users_dir.exists():
            try:
                # 모든 사용자 폴더 추가
                for user_dir in users_dir.iterdir():
                    if user_dir.is_dir():
                        cursor_path = user_dir / 'AppData' / 'Local' / 'Programs' / 'cursor'
                        possible_paths.append(cursor_path)
            except Exception as e:
                print(f"WSL 사용자 디렉토리 검색 중 오류: {e}")
        
        # 추가 일반 경로
        possible_paths.extend([
            Path('/mnt/c/Program Files/cursor'),
            Path('/mnt/c/Program Files (x86)/cursor')
        ])
        
        # 현재 사용자 추측 시도
        current_user = os.environ.get('USER')
        if current_user:
            possible_paths.insert(0, Path(f'/mnt/c/Users/{current_user}/AppData/Local/Programs/cursor'))
    # Linux
    else:
        possible_paths = [
            Path.home() / '.local' / 'share' / 'cursor',
            Path('/usr/share/cursor'),
            Path('/opt/cursor')
        ]

    # 경로 존재 확인
    for path in possible_paths:
        if path.exists():
            return path
    
    # 직접 경로 탐색
    # 주어진 경로가 .../workbench 형태이면 상위 디렉토리 추출
    test_paths = [
        '/mnt/c/Users/*/AppData/Local/Programs/cursor',
        '/mnt/c/Program Files*/cursor'
    ]
    
    found_paths = []
    for pattern in test_paths:
        try:
            import glob
            found_paths.extend(glob.glob(pattern))
        except:
            pass
    
    for path in found_paths:
        if Path(path).exists():
            return Path(path)
    
    # Cursor 설치 위치 자동 감지 시도
    print("Cursor IDE 설치 경로를 찾는 중...")
    
    if platform.system() == 'Windows':
        # Windows에서 레지스트리 확인
        try:
            import winreg
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r'SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\cursor.exe') as key:
                cursor_path = winreg.QueryValue(key, None)
                if cursor_path:
                    return Path(cursor_path).parent
        except:
            pass
    elif platform.system() == 'Darwin':
        # macOS에서 Spotlight 검색
        try:
            result = subprocess.check_output(['mdfind', 'kMDItemCFBundleIdentifier == "com.cursor.Cursor"']).decode().strip()
            if result:
                return Path(result) / 'Contents' / 'Resources' / 'app'
        except:
            pass
    
    # 검색 명령어 실행
    try:
        print("시스템에서 Cursor 파일 검색 중... (몇 분 걸릴 수 있습니다)")
        
        if platform.system() == 'Windows':
            search_command = ['where', '/r', 'C:', 'workbench.desktop.main.js']
        elif 'microsoft' in platform.uname().release.lower():
            # WSL에서는 사용자 홈 디렉토리 중심으로 검색 범위 축소
            search_paths = [
                '/mnt/c/Users',
                '/mnt/c/Program Files',
                '/mnt/c/Program Files (x86)'
            ]
            
            for search_path in search_paths:
                if Path(search_path).exists():
                    try:
                        search_command = ['find', search_path, '-name', 'workbench.desktop.main.js', '-type', 'f', '-not', '-path', "*/node_modules/*"]
                        result = subprocess.check_output(search_command, stderr=subprocess.DEVNULL, timeout=60).decode().strip()
                        if result:
                            first_result = result.split('\n')[0]
                            # workbench/workbench.desktop.main.js에서 cursor 폴더 찾기
                            parts = Path(first_result).parts
                            for i in range(len(parts) - 1, 0, -1):
                                if parts[i] == 'cursor':
                                    return Path('/'.join(parts[:i+1]))
                            # 아니면 4단계 상위 디렉토리 반환
                            return Path(first_result).parent.parent.parent.parent
                    except:
                        continue
        else:
            search_command = ['find', '/', '-name', 'workbench.desktop.main.js', '-type', 'f', '-not', '-path', "*/node_modules/*"]
            result = subprocess.check_output(search_command, stderr=subprocess.DEVNULL).decode().strip()
            if result:
                first_result = result.split('\n')[0]
                return Path(first_result).parent.parent.parent.parent  # workbench/workbench.desktop.main.js의 4단계 상위
    except:
        pass
    
    # 추가 검색: workbench.desktop.main.js 파일 직접 찾기
    if 'microsoft' in platform.uname().release.lower():
        try:
            result = subprocess.check_output(['locate', 'workbench.desktop.main.js'], stderr=subprocess.DEVNULL).decode().strip()
            if result:
                for path in result.split('\n'):
                    if 'cursor' in path and '/vs/workbench/' in path:
                        cursor_path = path
                        for i in range(6):  # cursor 폴더까지 상위로 올라가기
                            cursor_path = os.path.dirname(cursor_path)
                            if os.path.basename(cursor_path) == 'cursor':
                                return Path(cursor_path)
        except:
            pass
    
    return None

def find_main_js_file(cursor_path):
    """workbench.desktop.main.js 파일 찾기"""
    # 일반적인 경로 패턴
    common_paths = [
        'resources/app/out/vs/workbench/workbench.desktop.main.js',
        'out/vs/workbench/workbench.desktop.main.js',
        'vs/workbench/workbench.desktop.main.js'
    ]
    
    # 주요 경로 먼저 확인
    for rel_path in common_paths:
        full_path = cursor_path / rel_path
        if full_path.exists():
            return full_path
            
    # 재귀적으로 검색 (5단계 깊이 제한)
    def find_file(directory, filename, max_depth=5, current_depth=0):
        if current_depth > max_depth:
            return None
        
        try:
            for item in directory.iterdir():
                if item.is_file() and item.name == filename:
                    return item
                if item.is_dir():
                    result = find_file(item, filename, max_depth, current_depth + 1)
                    if result:
                        return result
        except:
            pass
        return None
    
    return find_file(cursor_path, 'workbench.desktop.main.js')

def extract_ui_strings(main_js_path):
    """workbench.desktop.main.js 파일에서 UI 문자열 추출"""
    if not main_js_path or not main_js_path.exists():
        print(f"Error: {main_js_path} 파일을 찾을 수 없습니다.")
        return []
    
    print(f"파일 분석 중: {main_js_path}")
    try:
        with open(main_js_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        print(f"파일 읽기 오류: {e}")
        try:
            # 다른 인코딩 시도
            with open(main_js_path, 'r', encoding='latin-1') as f:
                content = f.read()
        except Exception as e:
            print(f"파일 읽기 실패: {e}")
            return []
        
    # 문자열 패턴 검색 패턴들
    patterns = [
        # 문자열 할당 (예: children:"Settings")
        r'(?:title|label|description|children|text):"([^"\\]{3,})"',
        # 리터럴 문자열 (예: "Auto-scroll to bottom")
        r'return\s+"([^"\\]{3,})"',
        # children 함수 내부 문자열
        r'children:\(\)\s*=>\s*"([^"\\]{3,})"',
        # UI 컴포넌트에 전달되는 문자열
        r'D\([^,]+,\s*{[^}]*children:\s*"([^"\\]{3,})"'
    ]
    
    # 모든 문자열 추출
    extracted_strings = set()
    for pattern in patterns:
        matches = re.findall(pattern, content)
        for match in matches:
            # 영문자가 포함된 문자열만 추가
            if re.search(r'[a-zA-Z]', match) and len(match) > 3:
                # 코드로 보이는 문자열이나 짧은 문자열 제외
                if not re.search(r'^[\w\.\-]+$', match) and not re.search(r'^\d+$', match):
                    extracted_strings.add(match)
    
    print(f"{len(extracted_strings)}개의 UI 문자열 추출됨")
    return sorted(list(extracted_strings))

def load_existing_translations(translation_file):
    """기존 번역 파일 로드"""
    if translation_file.exists():
        try:
            with open(translation_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"번역 파일 로드 오류: {e}")
            try:
                # 다른 인코딩 시도
                with open(translation_file, 'r', encoding='latin-1') as f:
                    return json.load(f)
            except:
                pass
    return {}

def save_translations(translation_file, translations):
    """번역 파일 저장"""
    try:
        # 정렬된 형태로 저장
        sorted_translations = {k: translations[k] for k in sorted(translations.keys())}
        with open(translation_file, 'w', encoding='utf-8') as f:
            json.dump(sorted_translations, f, ensure_ascii=False, indent=2)
        print(f"번역 파일 저장됨: {translation_file}")
        return True
    except Exception as e:
        print(f"번역 파일 저장 오류: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(description='Cursor IDE UI 문자열 추출기')
    parser.add_argument('--cursor-path', help='Cursor 설치 경로 직접 지정')
    parser.add_argument('--output', default='cursor_strings.json', help='추출된 문자열 저장 파일')
    parser.add_argument('--translations', default='cursor_translations_ko.json', help='기존 번역 파일 경로')
    args = parser.parse_args()
    
    print("=" * 60)
    print(" Cursor UI 문자열 추출기")
    print("=" * 60)
    
    # 1. Cursor 경로 찾기
    cursor_path = Path(args.cursor_path) if args.cursor_path else find_cursor_installation()
    if not cursor_path:
        print("\n❌ Cursor IDE 설치 경로를 찾을 수 없습니다.")
        print("\n해결 방법:")
        print("1. Cursor가 설치되어 있는지 확인하세요.")
        print("2. '--cursor-path' 옵션으로 경로를 직접 지정하세요:")
        print("   예: python extract_strings.py --cursor-path \"C:\\경로\\cursor\"")
        print("3. 또는 CURSOR_PATH 환경 변수를 설정하세요.")
        return
    
    print(f"\n✅ Cursor 경로 찾음: {cursor_path}")
    
    # 2. workbench.desktop.main.js 파일 찾기
    main_js_path = find_main_js_file(cursor_path)
    if not main_js_path:
        print("\n❌ workbench.desktop.main.js 파일을 찾을 수 없습니다.")
        print("\n해결 방법:")
        print("1. Cursor가 정상적으로 설치되어 있는지 확인하세요.")
        print("2. '--cursor-path' 옵션으로 정확한 Cursor 설치 경로를 지정하세요.")
        return
    
    print(f"✅ 메인 JS 파일 찾음: {main_js_path}")
    
    # 3. UI 문자열 추출
    ui_strings = extract_ui_strings(main_js_path)
    if not ui_strings:
        print("\n❌ UI 문자열을 추출할 수 없습니다.")
        return
    
    print(f"✅ {len(ui_strings)}개의 UI 문자열 추출 완료")
    
    # 4. 결과 저장
    output_file = Path(args.output)
    result_dict = {s: "" for s in ui_strings}
    save_translations(output_file, result_dict)
    
    # 5. 기존 번역과 통합
    translation_file = Path(args.translations)
    if translation_file.exists():
        print(f"\n기존 번역 파일을 통합합니다: {translation_file}")
        existing_translations = load_existing_translations(translation_file)
        updated = False
        
        # 5.1 기존 번역에 새 문자열 추가
        new_strings = 0
        for string in ui_strings:
            if string not in existing_translations:
                existing_translations[string] = ""
                new_strings += 1
                updated = True
        
        # 5.2 기존 번역에 없는 추출된 문자열 제거
        keys_to_remove = []
        for key in existing_translations:
            if key not in ui_strings and existing_translations[key] == "":
                keys_to_remove.append(key)
        
        for key in keys_to_remove:
            del existing_translations[key]
            updated = True
        
        if updated:
            save_translations(translation_file, existing_translations)
            already_translated = len([k for k in existing_translations if k in ui_strings and existing_translations[k] != ''])
            print(f"\n✅ 번역 파일이 업데이트되었습니다: {translation_file}")
            print(f"  ➡️ 새로 추가된 문자열: {new_strings}개")
            print(f"  ➡️ 이미 번역된 문자열: {already_translated}개")
            print(f"  ➡️ 번역 필요한 문자열: {len(existing_translations) - already_translated}개")
        else:
            print("\n✅ 번역 파일에 변경 사항이 없습니다.")
    
    print("\n✅ 작업이 완료되었습니다!")
    print("=" * 60)
    print("다음 파일들이 생성되었습니다:")
    print(f"1. 원본 문자열 목록: {output_file} ({len(ui_strings)}개 항목)")
    print(f"2. 번역 파일: {translation_file}")
    print("=" * 60)
    print("\n다음 단계:")
    print("1. 번역 파일(cursor_translations_ko.json)에서 빈 문자열을 채워 번역을 완성하세요.")
    print("2. 번역 파일을 main.py에 사용하여 Cursor IDE에 적용하세요.")
    print("   예: python main.py --cursor-path \"경로\" --test-mode")

if __name__ == "__main__":
    main() 