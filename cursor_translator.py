import os
import json
import requests
from pathlib import Path

class DeepLTranslator:
    """DeepL API를 사용한 번역 클래스"""
    
    def __init__(self, api_key=None):
        self.api_key = api_key
        self.base_url = "https://api-free.deepl.com/v2/translate"
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
    
    def translate_texts(self, texts, target_lang='ko'):
        """텍스트 목록 번역"""
        if not texts:
            return {}
        
        if not self.api_key:
            print(f"DeepL API 키가 없습니다. 샘플 또는 이전 번역을 사용합니다.")
            return self._get_sample_translations(texts, target_lang)
        
        translations = {}
        chunk_size = 50  # API 한 번에 보낼 최대 텍스트 수
        
        for i in range(0, len(texts), chunk_size):
            chunk = texts[i:i + chunk_size]
            
            params = {
                "auth_key": self.api_key,
                "text": chunk,
                "target_lang": target_lang.upper()
            }
            
            try:
                response = requests.post(self.base_url, data=params)
                response.raise_for_status()
                result = response.json()
                
                for j, translation in enumerate(result["translations"]):
                    original = chunk[j]
                    translated = translation["text"]
                    translations[original] = translated
                
                print(f"번역 진행 중: {i+len(chunk)}/{len(texts)}")
            except Exception as e:
                print(f"번역 중 오류 발생: {e}")
        
        return translations
    
    def _get_sample_translations(self, texts, target_lang):
        """API 키 없을 때 샘플 번역 또는 기존 번역 파일 사용"""
        # 1. 기존 번역 파일 확인
        existing_file = Path(f"cursor_translations_{target_lang}.json")
        if existing_file.exists():
            try:
                with open(existing_file, 'r', encoding='utf-8') as f:
                    existing_translations = json.load(f)
                    # 기존 번역에 있는 것만 반환
                    return {text: existing_translations.get(text) for text in texts if text in existing_translations}
            except Exception as e:
                print(f"기존 번역 파일 로드 실패: {e}")
        
        # 2. 기본 샘플 번역 (한국어만 제공)
        if target_lang == 'ko':
            return {
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
                "Chat": "채팅",
                "Tab to import necessary dependencies": "탭으로 필요한 종속성 가져오기",
                "Command allowlist": "명령 허용 목록",
                "Delete file protection": "파일 삭제 보호",
                "Privacy mode": "개인 정보 보호 모드",
                "Enable auto-run mode": "자동 실행 모드 활성화"
            }
        
        # 3. 다른 언어는 빈 번역 딕셔너리 반환
        return {}

def save_translations(translations, file_path):
    """번역 결과를 JSON 파일로 저장"""
    if not translations:
        print(f"저장할 번역 데이터가 없습니다: {file_path}")
        return False
        
    os.makedirs(os.path.dirname(file_path) if os.path.dirname(file_path) else '.', exist_ok=True)
    
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(translations, f, ensure_ascii=False, indent=2)
    return True

def update_translations(existing_file, new_translations):
    """기존 번역 파일에 새 번역 추가"""
    if not new_translations:
        return 0
        
    existing = {}
    if Path(existing_file).exists():
        with open(existing_file, 'r', encoding='utf-8') as f:
            existing = json.load(f)
    
    # 새 번역으로 업데이트 (None이 아닌 값만)
    update_count = 0
    for key, value in new_translations.items():
        if value is not None and (key not in existing or existing[key] != value):
            existing[key] = value
            update_count += 1
    
    if update_count > 0:
        # 저장
        with open(existing_file, 'w', encoding='utf-8') as f:
            json.dump(existing, f, ensure_ascii=False, indent=2)
    
    return update_count

def load_translations(lang_code):
    """특정 언어의 번역 파일 로드"""
    translation_file = Path(f"cursor_translations_{lang_code}.json")
    if not translation_file.exists():
        return {}
        
    try:
        with open(translation_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"번역 파일 로드 실패: {e}")
        return {}
