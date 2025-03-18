import re
import json
from pathlib import Path

def extract_ui_strings(js_file_path):
    """JS 파일에서 UI 관련 문자열 추출"""
    if not js_file_path or not Path(js_file_path).exists():
        return []
    
    with open(js_file_path, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()
    
    # 설정 관련 문자열 추출을 위한 패턴
    patterns = [
        # 설정 항목 및 설명
        r'(?<=")(A powerful [^"]+)(?=")',
        r'(?<=")(If on, none of your code[^"]+)(?=")',
        r'(?<=")(Enable or disable [^"]+)(?=")',
        r'(?<=")(Auto-scroll to [^"]+)(?=")',
        r'(?<=")(Allow Agent to [^"]+)(?=")',
        
        # UI 요소
        r'(?<=")(Cursor Settings[^"]+)(?=")',
        r'(?<=")(Account[^"]+)(?=")',
        r'(?<=")(Features[^"]+)(?=")',
        r'(?<=")(Models[^"]+)(?=")',
        r'(?<=")(Rules[^"]+)(?=")',
        r'(?<=")(General[^"]+)(?=")',
        r'(?<=")(VS Code [^"]+)(?=")',
        r'(?<=")(Appearance[^"]+)(?=")',
        r'(?<=")(Cursor Tab[^"]+)(?=")',
        r'(?<=")(Chat[^"]+)(?=")',
        
        # 문장 패턴 (모든 설명 텍스트 포함)
        r'(?<=")((?:[A-Z][^"\.]+\.)+)(?=")'
    ]
    
    extracted_texts = []
    for pattern in patterns:
        matches = re.findall(pattern, content)
        extracted_texts.extend(matches)
    
    # 중복 제거 및 정렬
    extracted_texts = sorted(list(set(extracted_texts)))
    
    return extracted_texts

def save_extracted_strings(texts, output_file):
    """추출된 문자열을 파일로 저장"""
    with open(output_file, 'w', encoding='utf-8') as f:
        for text in texts:
            f.write(f"{text}\n")

def load_previous_translations(file_path):
    """이전 번역 파일 로드"""
    if not Path(file_path).exists():
        return {}
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return {}

def get_new_strings_for_translation(current_strings, prev_translations):
    """이전에 번역되지 않은 새 문자열만 필터링"""
    return [s for s in current_strings if s not in prev_translations]
