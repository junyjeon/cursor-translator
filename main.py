import os
import re
import json
import shutil
import requests
import datetime
from pathlib import Path
import argparse
import sys

# 모듈 임포트
from cursor_finder import find_cursor_installation, find_main_js_file, find_settings_json
from cursor_backup import backup_cursor_files
from cursor_extractor import extract_ui_strings, save_extracted_strings, load_previous_translations, get_new_strings_for_translation
from cursor_translator import DeepLTranslator, save_translations, update_translations, load_translations

class CursorTranslator:
    def __init__(self, deepl_api_key=None, cursor_path=None):
        self.deepl_api_key = deepl_api_key
        self.cursor_path = cursor_path or self._find_cursor_path()
        self.main_js_path = self._find_main_js()
        self.translations = {}
        self.supported_languages = {
            'ko': '한국어',
            'ja': '일본어',
            'zh': '중국어',
            'fr': '프랑스어',
            'de': '독일어',
            'es': '스페인어',
            'it': '이탈리아어',
            'pt': '포르투갈어',
            'ru': '러시아어'
        }
    
    def _find_cursor_path(self):
        """자동으로 Cursor 설치 경로 찾기"""
        if os.name == 'nt':  # Windows
            appdata = os.environ.get('LOCALAPPDATA')
            return os.path.join(appdata, 'Programs', 'cursor')
        elif os.name == 'posix':  # Mac/Linux
            if os.path.exists('/Applications/Cursor.app'):
                return '/Applications/Cursor.app'
            # WSL에서 Windows 경로 접근
            username = os.environ.get('USER')
            return f'/mnt/c/Users/{username}/AppData/Local/Programs/cursor'
        return None
    
    def _find_main_js(self):
        """workbench.desktop.main.js 파일 찾기"""
        if not self.cursor_path:
            raise ValueError("Cursor 설치 경로를 찾을 수 없습니다.")
        
        js_path = os.path.join(self.cursor_path, 'resources', 'app', 'out', 'vs', 'workbench', 'workbench.desktop.main.js')
        if os.path.exists(js_path):
            return js_path
        
        # 파일을 찾을 수 없으면 검색
        for root, _, files in os.walk(self.cursor_path):
            for file in files:
                if file == 'workbench.desktop.main.js':
                    return os.path.join(root, file)
        
        raise FileNotFoundError("workbench.desktop.main.js 파일을 찾을 수 없습니다.")
    
    def backup_files(self):
        """중요 파일 백업"""
        if not self.main_js_path:
            print("백업할 파일을 찾을 수 없습니다.")
            return False
        
        backup_dir = Path("cursor_backup_" + datetime.datetime.now().strftime("%Y%m%d_%H%M%S"))
        backup_dir.mkdir(exist_ok=True)
        
        try:
            # main.js 파일 백업
            js_backup_path = backup_dir / "workbench.desktop.main.js.backup"
            shutil.copy2(self.main_js_path, js_backup_path)
            
            # settings.json 백업 (있는 경우)
            if os.name == 'nt':  # Windows
                settings_path = os.path.expanduser("~\\AppData\\Roaming\\Cursor\\User\\settings.json")
            else:  # Mac/Linux
                settings_path = os.path.expanduser("~/.config/Cursor/User/settings.json")
                if not os.path.exists(settings_path):  # MacOS 대체 경로
                    settings_path = os.path.expanduser("~/Library/Application Support/Cursor/User/settings.json")
            
            if os.path.exists(settings_path):
                settings_backup_path = backup_dir / "settings.json.backup"
                shutil.copy2(settings_path, settings_backup_path)
                print(f"설정 파일 백업 완료: {settings_backup_path}")
            
            print(f"백업 완료: {backup_dir}")
            with open(backup_dir / "README.txt", "w", encoding="utf-8") as f:
                f.write(f"""Cursor 파일 백업 ({datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')})

이 폴더에는 Cursor 설정 번역 프로그램 사용 전에 자동으로 백업된 파일들이 있습니다.
문제가 발생할 경우 이 파일들을 원래 위치로 복원할 수 있습니다.

백업된 파일:
- workbench.desktop.main.js: Cursor UI 파일
- settings.json: 사용자 설정 파일 (있는 경우)

복원 방법은 README를 참조하세요.
""")
            
            return backup_dir
        except Exception as e:
            print(f"백업 중 오류 발생: {e}")
            return False
    
    def extract_text(self):
        """JS 파일에서 UI 텍스트 추출"""
        print(f"텍스트 추출 중: {self.main_js_path}")
        
        with open(self.main_js_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        
        # 설정 관련 문자열 추출을 위한 패턴
        # 더 정교한 패턴이 필요할 수 있음
        settings_patterns = [
            r'(?<=")(A powerful Copilot replacement[^"]+)(?=")',
            r'(?<=")(If on, none of your code[^"]+)(?=")',
            r'(?<=")(Enable or disable Cursor[^"]+)(?=")',
            r'(?<=")(Auto-scroll to bottom[^"]+)(?=")',
            r'(?<=")(Allow Agent to run tools[^"]+)(?=")',
            r'(?<=")(Tab to import necessary[^"]+)(?=")',
            r'(?<=")(Cursor Tab suggestions[^"]+)(?=")',
            r'(?<=")(Command allowlist[^"]+)(?=")',
            r'(?<=")(Delete file protection[^"]+)(?=")',
            r'(?<=")(Privacy mode[^"]+)(?=")',
            r'(?<=")(Enable auto-run mode[^"]+)(?=")',
            # 더 많은 패턴 추가 가능
        ]
        
        extracted_texts = []
        for pattern in settings_patterns:
            matches = re.findall(pattern, content)
            extracted_texts.extend(matches)
        
        # 일반적인 UI 요소를 위한 추가 패턴
        ui_patterns = [
            r'(?<=")(Cursor Settings[^"]+)(?=")',
            r'(?<=")(Account[^"]+)(?=")',
            r'(?<=")(Features[^"]+)(?=")',
            r'(?<=")(Models[^"]+)(?=")',
            r'(?<=")(Rules[^"]+)(?=")',
            r'(?<=")(General[^"]+)(?=")',
            r'(?<=")(VS Code Import[^"]+)(?=")',
            r'(?<=")(Appearance[^"]+)(?=")',
            r'(?<=")(Cursor Tab[^"]+)(?=")',
            r'(?<=")(Chat[^"]+)(?=")',
        ]
        
        for pattern in ui_patterns:
            matches = re.findall(pattern, content)
            extracted_texts.extend(matches)
        
        # 문장 형태의 텍스트 추출 (더 많은 설정 설명을 얻기 위해)
        sentence_pattern = r'(?<=")((?:[A-Z][^"\.]+\.)+)(?=")'
        sentences = re.findall(sentence_pattern, content)
        extracted_texts.extend(sentences)
        
        # 중복 제거 및 정렬
        extracted_texts = sorted(list(set(extracted_texts)))
        print(f"{len(extracted_texts)}개의 텍스트 추출됨")
        
        # 결과 파일로 저장
        with open('cursor_strings.txt', 'w', encoding='utf-8') as f:
            for text in extracted_texts:
                f.write(f"{text}\n")
        
        return extracted_texts
    
    def translate_texts(self, texts, target_lang='ko'):
        """DeepL API를 사용하여 텍스트 번역"""
        if not texts:
            print("번역할 텍스트가 없습니다.")
            return {}
        
        if not self.deepl_api_key:
            print("DeepL API 키가 없습니다. 샘플 번역 데이터를 생성합니다.")
            # 샘플 번역 데이터 생성
            sample_translations = {}
            if target_lang == 'ko':
                sample_translations = {
                    "A powerful Copilot replacement that can suggest changes across multiple lines.": "여러 줄에 걸쳐 변경 사항을 제안할 수 있는 강력한 Copilot 대체품입니다.",
                    "If on, none of your code will be stored by us.": "켜면 귀하의 코드는 저희 측에 저장되지 않습니다.",
                    "Enable or disable Cursor Tab suggestions in comments": "주석에서 Cursor Tab 제안 활성화 또는 비활성화",
                    "Auto-scroll to bottom": "자동으로 맨 아래로 스크롤",
                    "Allow Agent to run tools without asking for confirmation": "확인 요청 없이 에이전트가 도구를 실행하도록 허용",
                    "Cursor Settings": "Cursor 설정",
                    "Account": "계정",
                    "Features": "기능",
                    "Models": "모델",
                    "Rules": "규칙",
                    "General": "일반",
                    "VS Code Import": "VS Code 가져오기",
                    "Appearance": "외관",
                    "Cursor Tab": "Cursor 탭",
                    "Chat": "채팅"
                }
            return sample_translations
        
        print(f"{target_lang}로 {len(texts)}개 텍스트 번역 중...")
        translations = {}
        
        # DeepL API 엔드포인트
        url = "https://api-free.deepl.com/v2/translate"  # 무료 API 사용, 유료는 다른 URL
        
        # 한 번에 너무 많은 텍스트를 보내지 않도록 분할
        chunk_size = 50
        for i in range(0, len(texts), chunk_size):
            chunk = texts[i:i + chunk_size]
            
            params = {
                "auth_key": self.deepl_api_key,
                "text": chunk,
                "target_lang": target_lang.upper()
            }
            
            try:
                response = requests.post(url, data=params)
                response.raise_for_status()
                result = response.json()
                
                for j, translation in enumerate(result["translations"]):
                    original = chunk[j]
                    translated = translation["text"]
                    translations[original] = translated
                
                print(f"진행 중: {i+len(chunk)}/{len(texts)}")
            except Exception as e:
                print(f"번역 중 오류 발생: {e}")
        
        # 번역 결과 저장
        with open(f'cursor_translations_{target_lang}.json', 'w', encoding='utf-8') as f:
            json.dump(translations, f, ensure_ascii=False, indent=2)
        
        return translations
    
    def create_translation_app(self):
        """번역된 Cursor 설정을 보여주는 앱 생성"""
        app_code = '''
import os
import sys
import json
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import datetime

class CursorTranslationApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Cursor 다국어 설정")
        self.root.geometry("900x700")
        
        # 지원 언어
        self.languages = {
            'ko': '한국어',
            'ja': '일본어',
            'zh': '중국어',
            'fr': '프랑스어',
            'de': '독일어',
            'es': '스페인어',
            'it': '이탈리아어',
            'pt': '포르투갈어',
            'ru': '러시아어'
        }
        
        # 번역 데이터 로드
        self.translations = {}
        self.load_available_translations()
        
        # UI 구성
        self.create_widgets()
'''
        
        with open('cursor_translator_app.py', 'w', encoding='utf-8') as f:
            f.write(app_code)

def main():
    parser = argparse.ArgumentParser(description='Cursor IDE 다국어 번역 도구')
    parser.add_argument('--api-key', help='DeepL API 키 (없으면 기존 번역 또는 샘플 사용)')
    parser.add_argument('--langs', default='ko', help='번역할 언어 코드 (쉼표로 구분, 기본값: ko)')
    parser.add_argument('--no-backup', action='store_true', help='백업 건너뛰기')
    parser.add_argument('--cursor-path', help='Cursor 설치 경로 수동 지정')
    parser.add_argument('--extract-only', action='store_true', help='텍스트만 추출하고 번역은 건너뛰기')
    parser.add_argument('--view-only', action='store_true', help='기존 번역만 표시 (추출/번역 건너뛰기)')
    parser.add_argument('--test-mode', action='store_true', help='Cursor 설치 없이 샘플 데이터로 테스트')
    args = parser.parse_args()
    
    # 기존 번역 파일만 볼 경우
    if args.view_only:
        print("기존 번역 파일 확인 중...")
        languages = [lang.strip() for lang in args.langs.split(',')]
        
        for lang in languages:
            translations = load_translations(lang)
            if translations:
                print(f"[{lang}] {len(translations)}개 번역 항목 찾음")
            else:
                print(f"[{lang}] 번역 파일이 없거나 비어 있습니다.")
        
        print("\n번역 파일은 'cursor_translations_[언어코드].json' 형식으로 저장되어 있습니다.")
        return
    
    # 1. Cursor 관련 파일 경로 찾기
    print("1. Cursor IDE 경로 찾는 중...")
    cursor_path = Path(args.cursor_path) if args.cursor_path else find_cursor_installation()
    
    # 테스트 모드 확인
    if not cursor_path and args.test_mode:
        print("테스트 모드: Cursor 설치 없이 샘플 데이터만 사용합니다.")
        # 샘플 번역 생성
        sample_texts = [
            "A powerful Copilot replacement that can suggest changes across multiple lines.",
            "If on, none of your code will be stored by us.",
            "Enable or disable Cursor Tab suggestions in comments",
            "Auto-scroll to bottom",
            "Allow Agent to run tools without asking for confirmation",
            "Cursor Settings",
            "Account",
            "Features",
            "Models",
            "Rules",
            "General",
            "VS Code Import",
            "Appearance",
            "Cursor Tab",
            "Chat"
        ]
        
        # 샘플 문자열 저장
        strings_file = Path("cursor_strings.txt")
        save_extracted_strings(sample_texts, strings_file)
        print(f"   - 샘플 문자열 저장됨: {strings_file}")
        
        # 번역 처리로 건너뛰기
        print("\n2. 샘플 문자열 번역 중...")
        translator = DeepLTranslator(args.api_key)
        
        # 번역할 언어 목록
        languages = [lang.strip() for lang in args.langs.split(',') if lang.strip() in translator.supported_languages]
        
        for lang in languages:
            print(f"\n   - {translator.supported_languages.get(lang, lang)} 번역 시작...")
            new_translations = translator.translate_texts(sample_texts, lang)
            
            if new_translations:
                # 번역 결과 저장
                translations_file = Path(f"cursor_translations_{lang}.json")
                update_translations(translations_file, new_translations)
                print(f"     - {len(new_translations)}개 문자열 번역 완료: {translations_file}")
        
        print("\n테스트 모드 작업이 완료되었습니다!")
        print("생성된 번역 파일을 확인하세요.")
        return
    
    if not cursor_path:
        print("Cursor IDE 설치 경로를 찾을 수 없습니다.")
        print("수동으로 경로를 지정하려면 --cursor-path 옵션을 사용하세요.")
        print("또는 --test-mode 옵션을 사용하여 Cursor 설치 없이 샘플 데이터로 테스트할 수 있습니다.")
        sys.exit(1)
    
    # 2. 필요한 파일 찾기
    main_js_path = find_main_js_file(cursor_path)
    settings_path = find_settings_json()
    
    if not main_js_path:
        print("workbench.desktop.main.js 파일을 찾을 수 없습니다.")
        sys.exit(1)
    
    print(f"   - main.js 경로: {main_js_path}")
    print(f"   - settings.json 경로: {settings_path if settings_path and settings_path.exists() else '찾을 수 없음'}")
    
    # 3. 파일 백업
    if not args.no_backup:
        print("\n2. 중요 파일 백업 중...")
        backup_dir = backup_cursor_files(main_js_path, settings_path)
        if backup_dir:
            print(f"   - 백업 완료: {backup_dir}")
        else:
            print("   - 백업 실패 또는 파일 없음")
    
    # 4. UI 문자열 추출
    print("\n3. UI 문자열 추출 중...")
    extracted_strings = extract_ui_strings(main_js_path)
    
    if not extracted_strings:
        print("   - 추출할 UI 문자열이 없습니다.")
        sys.exit(1)
    
    print(f"   - {len(extracted_strings)}개 문자열 추출됨")
    
    # 추출된 문자열 저장
    strings_file = Path("cursor_strings.txt")
    save_extracted_strings(extracted_strings, strings_file)
    print(f"   - 추출된 문자열 저장됨: {strings_file}")
    
    # 추출만 원하는 경우 종료
    if args.extract_only:
        print("\n문자열 추출이 완료되었습니다. 추출된 문자열은 cursor_strings.txt 파일에서 확인하세요.")
        return
    
    # 5. 번역 처리
    print("\n4. 문자열 번역 중...")
    translator = DeepLTranslator(args.api_key)
    
    # 번역할 언어 목록
    languages = [lang.strip() for lang in args.langs.split(',') if lang.strip() in translator.supported_languages]
    
    if not languages:
        print("   - 지원되는 언어가 지정되지 않았습니다.")
        print(f"   - 지원 언어: {', '.join(translator.supported_languages.keys())}")
        sys.exit(1)
    
    for lang in languages:
        print(f"\n   - {translator.supported_languages.get(lang, lang)} 번역 시작...")
        
        # 이전 번역 로드
        translations_file = Path(f"cursor_translations_{lang}.json")
        prev_translations = load_previous_translations(translations_file)
        
        # 새로운 문자열만 필터링
        new_strings = get_new_strings_for_translation(extracted_strings, prev_translations)
        
        if not new_strings:
            print(f"     - 모든 문자열이 이미 번역되어 있습니다.")
            continue
        
        print(f"     - {len(new_strings)}개 새 문자열 번역 중...")
        
        # 번역 처리
        new_translations = translator.translate_texts(new_strings, lang)
        
        if not new_translations:
            if not args.api_key:
                print(f"     - DeepL API 키가 없어 샘플 또는 기존 번역만 사용합니다.")
            else:
                print(f"     - 번역 실패 또는 결과 없음")
            continue
        
        # 번역 결과 업데이트 및 저장
        updated = update_translations(translations_file, new_translations)
        print(f"     - {updated}개 문자열 번역 완료: {translations_file}")
    
    print("\n작업이 완료되었습니다!")
    print("번역 파일을 확인하고 필요에 따라 수정하세요.")
    print("\n사용 방법:")
    print("- 번역 파일: cursor_translations_[언어코드].json")
    print("- 추출된 문자열: cursor_strings.txt")
    
    # API 키가 없는 경우 안내 메시지
    if not args.api_key:
        print("\n참고: DeepL API 키가 제공되지 않아 샘플 또는 기존 번역만 사용했습니다.")
        print("정확한 번역을 위해 DeepL API 키를 사용할 수 있습니다: https://www.deepl.com/pro#developer")

def show_usage():
    """사용법 표시"""
    print("Cursor IDE 다국어 번역 도구 사용법:")
    print("\n기본 사용법:")
    print("  python main.py")
    print("\n옵션:")
    print("  --api-key KEY      : DeepL API 키 (새 번역 생성 시 필요)")
    print("  --langs LANGS      : 번역할 언어 코드 (쉼표로 구분, 기본값: ko)")
    print("  --no-backup        : 백업 건너뛰기")
    print("  --cursor-path PATH : Cursor 설치 경로 수동 지정")
    print("  --extract-only     : 텍스트만 추출하고 번역은 건너뛰기")
    print("  --view-only        : 기존 번역만 표시 (추출/번역 건너뛰기)")
    print("\n지원 언어:")
    print("  ko: 한국어, ja: 일본어, zh: 중국어, fr: 프랑스어, de: 독일어,")
    print("  es: 스페인어, it: 이탈리아어, pt: 포르투갈어, ru: 러시아어")
    print("\n예시:")
    print("  # 설치된 Cursor에서 한국어 번역 파일 생성 (API 키 사용)")
    print("  python main.py --api-key YOUR_DEEPL_API_KEY")
    print("\n  # 여러 언어 번역 생성")
    print("  python main.py --api-key YOUR_DEEPL_API_KEY --langs ko,ja,zh")
    print("\n  # 텍스트만 추출")
    print("  python main.py --extract-only")
    print("\n  # 기존 번역 파일 확인")
    print("  python main.py --view-only")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] in ('-h', '--help'):
        show_usage()
    else:
        main()
