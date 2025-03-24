import os
import re
import json
import shutil
import requests
import datetime
from pathlib import Path
import argparse
import sys
import logging

# 모듈 경로 추가
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 모듈 임포트
from cursor_finder import CursorFinder, find_main_js_file, find_settings_json
from cursor_backup import backup_cursor_files
from cursor_extractor import CursorExtractor, extract_ui_strings, save_extracted_strings, load_previous_translations, get_new_strings_for_translation
from cursor_translator import DeepLTranslator, save_translations, update_translations, load_translations

# 로깅 설정
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

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

def create_backup(cursor_path, js_file_path):
    """원본 파일 백업"""
    if not cursor_path or not js_file_path or not os.path.exists(js_file_path):
        logger.error("백업을 위한 파일 경로가 유효하지 않습니다.")
        return None
        
    # 백업 디렉토리 생성
    backup_dir = Path.home() / '.cursor_translator' / 'backups'
    backup_dir.mkdir(parents=True, exist_ok=True)
    
    # 타임스탬프로 백업 파일 이름 생성
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file = backup_dir / f"workbench.desktop.main.js.{timestamp}"
    
    try:
        shutil.copy2(js_file_path, backup_file)
        logger.info(f"원본 파일 백업 완료: {backup_file}")
        return backup_file
    except Exception as e:
        logger.error(f"백업 생성 중 오류 발생: {e}")
        return None

def restore_backup(backup_file, js_file_path):
    """백업에서 복원"""
    if not backup_file or not js_file_path:
        logger.error("복원을 위한 파일 경로가 유효하지 않습니다.")
        return False
        
    try:
        shutil.copy2(backup_file, js_file_path)
        logger.info(f"백업에서 복원 완료: {js_file_path}")
        return True
    except Exception as e:
        logger.error(f"복원 중 오류 발생: {e}")
        return False

def apply_translations(js_file_path, translation_file, backup=True):
    """번역 적용"""
    if not js_file_path or not os.path.exists(js_file_path):
        logger.error(f"JS 파일이 존재하지 않습니다: {js_file_path}")
        return False
        
    if not translation_file or not os.path.exists(translation_file):
        logger.error(f"번역 파일이 존재하지 않습니다: {translation_file}")
        return False
    
    # 번역 파일 로드
    try:
        with open(translation_file, 'r', encoding='utf-8') as f:
            translations = json.load(f)
    except Exception as e:
        logger.error(f"번역 파일 로드 중 오류 발생: {e}")
        return False
    
    # 원본 파일 로드
    try:
        with open(js_file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
    except Exception as e:
        logger.error(f"JS 파일 로드 중 오류 발생: {e}")
        return False
    
    # 백업 생성
    if backup:
        cursor_path = js_file_path.parents[4]  # 'resources/app/out/vs/workbench' 상위 디렉토리
        create_backup(cursor_path, js_file_path)
    
    # 번역 적용 (정규식으로 찾아 바꾸기)
    modified_content = content
    replacements = 0
    
    # 번역 사전 정렬 (길이가 긴 텍스트부터 처리)
    sorted_translations = sorted(translations.items(), key=lambda x: len(x[0]), reverse=True)
    
    for original, translated in sorted_translations:
        if not translated:  # 번역이 없는 항목은 건너뛰기
            continue
            
        # 원본이 너무 짧으면 건너뛰기 (오탐지 방지)
        if len(original) < 3:
            continue
        
        # 치환 패턴 생성
        patterns = [
            f'"{original}"',  # "텍스트"
            f"'{original}'",  # '텍스트'
        ]
        
        for pattern in patterns:
            # 치환할 번역문 생성
            if "'" in pattern:
                replacement = f"'{translated}'"
            else:
                replacement = f'"{translated}"'
                
            # 치환 횟수 카운트
            old_content = modified_content
            modified_content = modified_content.replace(pattern, replacement)
            if old_content != modified_content:
                replacements += 1
    
    # 변경된 내용 저장
    if replacements > 0:
        try:
            with open(js_file_path, 'w', encoding='utf-8') as f:
                f.write(modified_content)
            logger.info(f"번역 적용 완료: {replacements}개 항목 적용됨")
            return True
        except Exception as e:
            logger.error(f"변경된 내용 저장 중 오류 발생: {e}")
            return False
    else:
        logger.warning("적용된 번역이 없습니다.")
        return False

def extract_and_translate(cursor_path, target_lang, api_key=None, test_mode=False):
    """텍스트 추출 및 번역"""
    if test_mode:
        # 테스트 모드: 샘플 데이터 생성
        logger.info("테스트 모드로 실행합니다.")
        extractor = CursorExtractor("dummy_path")
        strings_file = extractor.generate_sample_strings()
        template_file = extractor.generate_translation_template()
    else:
        # 실제 데이터 추출
        if not cursor_path:
            logger.error("Cursor 설치 경로가 지정되지 않았습니다.")
            return False
            
        js_file_path = find_main_js_file(Path(cursor_path))
        if not js_file_path:
            logger.error("workbench.desktop.main.js 파일을 찾을 수 없습니다.")
            return False
            
        extractor = CursorExtractor(js_file_path)
        strings_file = extractor.extract_strings()
        template_file = extractor.generate_translation_template()
    
    # 번역 실행
    output_file = f"cursor_translations_{target_lang.lower()}.json"
    translator = DeepLTranslator(api_key)
    
    translated, total = translator.update_translation_json(template_file, output_file, target_lang)
    logger.info(f"번역 완료: {translated}/{total} 항목이 번역되었습니다.")
    logger.info(f"번역 파일이 저장되었습니다: {output_file}")
    
    return True

def list_backups():
    """백업 목록 표시"""
    backup_dir = Path.home() / '.cursor_translator' / 'backups'
    
    if not backup_dir.exists():
        logger.info("백업 디렉토리가 없습니다.")
        return []
    
    backups = list(backup_dir.glob("workbench.desktop.main.js.*"))
    backups.sort(reverse=True)  # 최신 백업이 먼저 오도록 정렬
    
    if not backups:
        logger.info("백업 파일이 없습니다.")
    else:
        logger.info(f"총 {len(backups)}개의 백업 파일:")
        for i, backup in enumerate(backups):
            timestamp = backup.name.split('.')[-1]
            try:
                date = datetime.strptime(timestamp, "%Y%m%d_%H%M%S").strftime("%Y-%m-%d %H:%M:%S")
                logger.info(f"{i+1}. {date} - {backup}")
            except:
                logger.info(f"{i+1}. {backup}")
    
    return backups

def main():
    parser = argparse.ArgumentParser(description='Cursor IDE 다국어 번역 도구')
    
    # 기본 옵션
    parser.add_argument('--cursor-path', help='Cursor 설치 경로')
    parser.add_argument('--api-key', help='DeepL API 키')
    parser.add_argument('--target-lang', default='ko', help='대상 언어 코드 (기본값: ko)')
    parser.add_argument('--test-mode', action='store_true', help='테스트 모드')
    
    # 동작 모드
    mode_group = parser.add_mutually_exclusive_group()
    mode_group.add_argument('--extract', action='store_true', help='텍스트 추출')
    mode_group.add_argument('--translate', action='store_true', help='번역 적용')
    mode_group.add_argument('--restore', action='store_true', help='백업에서 복원')
    mode_group.add_argument('--list-backups', action='store_true', help='백업 목록 표시')
    
    # 백업 관련 옵션
    parser.add_argument('--no-backup', action='store_true', help='백업 건너뛰기')
    parser.add_argument('--backup-index', type=int, help='복원할 백업 인덱스 (--list-backups로 확인)')
    
    args = parser.parse_args()
    
    # API 키는 환경 변수에서도 가져올 수 있음
    api_key = args.api_key or os.environ.get('DEEPL_API_KEY')
    
    # Cursor 경로 찾기
    cursor_path = args.cursor_path
    if not cursor_path and not args.test_mode:
        finder = CursorFinder()
        cursor_path = finder.find_cursor_installation()
        if cursor_path:
            logger.info(f"Cursor 설치 경로: {cursor_path}")
        else:
            logger.warning("Cursor 설치 경로를 찾을 수 없습니다. --cursor-path 옵션으로 직접 지정하세요.")
            if not args.list_backups:  # 백업 목록 표시는 Cursor 경로가 필요 없음
                return
    
    # 명령 처리
    if args.list_backups:
        list_backups()
        return
        
    elif args.restore:
        backups = list_backups()
        if not backups:
            return
        
        backup_index = args.backup_index
        if backup_index is None:
            backup_index = int(input("복원할 백업 번호를 입력하세요: "))
        
        if 1 <= backup_index <= len(backups):
            selected_backup = backups[backup_index - 1]
            
            if not cursor_path:
                logger.error("복원을 위해 Cursor 설치 경로가 필요합니다.")
                return
                
            js_file_path = find_main_js_file(Path(cursor_path))
            if not js_file_path:
                logger.error("workbench.desktop.main.js 파일을 찾을 수 없습니다.")
                return
                
            restore_backup(selected_backup, js_file_path)
        else:
            logger.error(f"유효하지 않은 백업 인덱스: {backup_index}")
        return
        
    elif args.extract:
        extract_and_translate(cursor_path, args.target_lang, api_key, args.test_mode)
        return
        
    elif args.translate:
        if not cursor_path and not args.test_mode:
            logger.error("번역 적용을 위해 Cursor 설치 경로가 필요합니다.")
            return
            
        translation_file = f"cursor_translations_{args.target_lang.lower()}.json"
        if not os.path.exists(translation_file):
            logger.error(f"번역 파일이 존재하지 않습니다: {translation_file}")
            logger.info("먼저 --extract 옵션으로 번역 파일을 생성하세요.")
            return
        
        if args.test_mode:
            logger.info(f"테스트 모드: 번역 파일 {translation_file}의 내용 확인")
            with open(translation_file, 'r', encoding='utf-8') as f:
                translations = json.load(f)
            logger.info(f"총 {len(translations)}개 항목, 번역된 항목: {sum(1 for v in translations.values() if v)}")
            return
            
        js_file_path = find_main_js_file(Path(cursor_path))
        if not js_file_path:
            logger.error("workbench.desktop.main.js 파일을 찾을 수 없습니다.")
            return
            
        apply_translations(js_file_path, translation_file, not args.no_backup)
        return
    
    # 기본 동작: 추출 및 번역 
    extract_and_translate(cursor_path, args.target_lang, api_key, args.test_mode)

if __name__ == "__main__":
        main()
