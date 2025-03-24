import os
import json
import requests
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class DeepLTranslator:
    """DeepL API를 사용한 번역 클래스"""
    
    SAMPLE_TRANSLATIONS = {
        # 영어 -> 한국어 샘플 번역
        'ko': {
            'Open File': '파일 열기',
            'Save': '저장',
            'Save As...': '다른 이름으로 저장...',
            'Close': '닫기',
            'Close All': '모두 닫기',
            'Preferences': '환경설정',
            'Settings': '설정',
            'Cut': '잘라내기',
            'Copy': '복사',
            'Paste': '붙여넣기',
            'Find': '찾기',
            'Replace': '바꾸기',
            'Go to Line': '줄 이동',
            'Toggle Comment': '주석 전환',
            'Indent': '들여쓰기',
            'Outdent': '내어쓰기',
            'Format Document': '문서 포맷팅',
            'Toggle Terminal': '터미널 전환',
            'Zoom In': '확대',
            'Zoom Out': '축소',
            'Full Screen': '전체 화면',
            'Split Editor': '편집기 분할',
            'Toggle Sidebar': '사이드바 전환',
        },
        # 영어 -> 일본어 샘플 번역
        'ja': {
            'Open File': 'ファイルを開く',
            'Save': '保存',
            'Save As...': '名前を付けて保存...',
            'Close': '閉じる',
            'Close All': 'すべて閉じる',
            'Preferences': '環境設定',
            'Settings': '設定',
            'Cut': '切り取り',
            'Copy': 'コピー',
            'Paste': '貼り付け',
            'Find': '検索',
            'Replace': '置換',
            'Go to Line': '行へ移動',
            'Toggle Comment': 'コメントの切り替え',
            'Indent': 'インデント',
            'Outdent': 'アウトデント',
            'Format Document': 'ドキュメントのフォーマット',
            'Toggle Terminal': 'ターミナルの切り替え',
            'Zoom In': '拡大',
            'Zoom Out': '縮小',
            'Full Screen': '全画面表示',
            'Split Editor': 'エディタの分割',
            'Toggle Sidebar': 'サイドバーの切り替え',
        },
        # 영어 -> 중국어 샘플 번역
        'zh': {
            'Open File': '打开文件',
            'Save': '保存',
            'Save As...': '另存为...',
            'Close': '关闭',
            'Close All': '全部关闭',
            'Preferences': '首选项',
            'Settings': '设置',
            'Cut': '剪切',
            'Copy': '复制',
            'Paste': '粘贴',
            'Find': '查找',
            'Replace': '替换',
            'Go to Line': '转到行',
            'Toggle Comment': '切换注释',
            'Indent': '缩进',
            'Outdent': '减少缩进',
            'Format Document': '格式化文档',
            'Toggle Terminal': '切换终端',
            'Zoom In': '放大',
            'Zoom Out': '缩小',
            'Full Screen': '全屏',
            'Split Editor': '拆分编辑器',
            'Toggle Sidebar': '切换侧边栏',
        }
    }
    
    def __init__(self, api_key: Optional[str] = None):
        """
        DeepL 번역기 초기화
        
        Args:
            api_key: DeepL API 키 (선택사항)
        """
        self.api_key = api_key
        self.api_url = "https://api-free.deepl.com/v2/translate"
        self.has_valid_key = False
        
        if self.api_key:
            try:
                # API 키 유효성 테스트
                self.translate_text("test", target_lang="EN")
                self.has_valid_key = True
                logger.info("DeepL API 키가 유효합니다.")
            except Exception as e:
                logger.warning(f"DeepL API 키가 유효하지 않습니다: {str(e)}")
        else:
            logger.info("DeepL API 키가 제공되지 않았습니다. 샘플 번역만 사용 가능합니다.")
    
    def translate_text(self, text: str, target_lang: str) -> str:
        """
        단일 텍스트 번역
        
        Args:
            text: 번역할 텍스트
            target_lang: 대상 언어 코드 (예: EN, KO, JA)
            
        Returns:
            번역된 텍스트
        """
        if not text:
            return ""
            
        # 샘플 번역 확인
        if not self.api_key or not self.has_valid_key:
            lang_code = target_lang.lower()
            if lang_code in self.SAMPLE_TRANSLATIONS and text in self.SAMPLE_TRANSLATIONS[lang_code]:
                return self.SAMPLE_TRANSLATIONS[lang_code][text]
            return text  # 샘플 번역이 없으면 원본 반환
            
        # DeepL API 호출
        payload = {
            "auth_key": self.api_key,
            "text": text,
            "target_lang": target_lang.upper()
        }
        
        try:
            response = requests.post(self.api_url, data=payload)
            response.raise_for_status()
            
            result = response.json()
            if "translations" in result and result["translations"]:
                return result["translations"][0]["text"]
            return text
        except Exception as e:
            logger.error(f"번역 오류: {str(e)}")
            return text
    
    def batch_translate(self, texts: List[str], target_lang: str) -> List[str]:
        """
        텍스트 배치 번역
        
        Args:
            texts: 번역할 텍스트 목록
            target_lang: 대상 언어 코드
            
        Returns:
            번역된 텍스트 목록
        """
        if not texts:
            return []
            
        # 샘플 번역 확인
        if not self.api_key or not self.has_valid_key:
            results = []
            lang_code = target_lang.lower()
            for text in texts:
                if lang_code in self.SAMPLE_TRANSLATIONS and text in self.SAMPLE_TRANSLATIONS[lang_code]:
                    results.append(self.SAMPLE_TRANSLATIONS[lang_code][text])
                else:
                    results.append(text)  # 샘플 번역이 없으면 원본 반환
            return results
            
        # DeepL API 배치 요청
        payload = {
            "auth_key": self.api_key,
            "text": texts,
            "target_lang": target_lang.upper()
        }
        
        try:
            response = requests.post(self.api_url, data=payload)
            response.raise_for_status()
            
            result = response.json()
            if "translations" in result:
                return [t["text"] for t in result["translations"]]
            return texts
        except Exception as e:
            logger.error(f"배치 번역 오류: {str(e)}")
            return texts
    
    def translate_file(self, input_file: str, output_file: str, target_lang: str) -> Tuple[int, int]:
        """
        파일 내 텍스트 번역
        
        Args:
            input_file: 번역할 텍스트가 있는 파일 경로
            output_file: 번역 결과를 저장할 파일 경로
            target_lang: 대상 언어 코드
            
        Returns:
            (번역된 항목 수, 총 항목 수)
        """
        if not os.path.exists(input_file):
            logger.error(f"입력 파일이 존재하지 않습니다: {input_file}")
            return (0, 0)
            
        with open(input_file, 'r', encoding='utf-8') as f:
            texts = [line.strip() for line in f if line.strip()]
            
        translated = self.batch_translate(texts, target_lang)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            for text in translated:
                f.write(f"{text}\n")
                
        return (len(translated), len(texts))
    
    def update_translation_json(self, template_file: str, output_file: str, target_lang: str) -> Tuple[int, int]:
        """
        번역 JSON 파일 업데이트
        
        Args:
            template_file: 템플릿 JSON 파일 경로
            output_file: 출력 JSON 파일 경로
            target_lang: 대상 언어 코드
            
        Returns:
            (번역된 항목 수, 총 항목 수)
        """
        if not os.path.exists(template_file):
            logger.error(f"템플릿 파일이 존재하지 않습니다: {template_file}")
            return (0, 0)
            
        # 기존 번역 파일 로드 (있는 경우)
        existing_translations = {}
        if os.path.exists(output_file):
            try:
                with open(output_file, 'r', encoding='utf-8') as f:
                    existing_translations = json.load(f)
            except Exception as e:
                logger.warning(f"기존 번역 파일을 로드하는 중 오류 발생: {str(e)}")
                
        # 템플릿 로드
        with open(template_file, 'r', encoding='utf-8') as f:
            template = json.load(f)
            
        # 번역 필요한 항목 필터링
        to_translate = []
        keys_to_translate = []
        
        for key, value in template.items():
            # 이미 번역된 항목은 건너뛰기
            if key in existing_translations and existing_translations[key]:
                continue
                
            to_translate.append(key)
            keys_to_translate.append(key)
            
        # 번역 실행
        if to_translate:
            translated_texts = self.batch_translate(to_translate, target_lang)
            
            # 번역 결과 저장
            for i, key in enumerate(keys_to_translate):
                if i < len(translated_texts):
                    template[key] = translated_texts[i]
        
        # 기존 번역 추가
        for key, value in existing_translations.items():
            if key in template and value:
                template[key] = value
                
        # 결과 저장
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(template, f, ensure_ascii=False, indent=2)
            
        # 번역된 항목 수 계산
        translated_count = sum(1 for value in template.values() if value)
        return (translated_count, len(template))


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='DeepL API를 사용한 Cursor IDE 번역')
    parser.add_argument('--api-key', help='DeepL API 키')
    parser.add_argument('--target-lang', default='KO', help='대상 언어 코드 (예: KO, JA, ZH)')
    parser.add_argument('--template', default='cursor_translations_template.json', help='번역 템플릿 파일')
    parser.add_argument('--output', help='출력 파일')
    
    args = parser.parse_args()
    
    api_key = args.api_key or os.environ.get('DEEPL_API_KEY')
    translator = DeepLTranslator(api_key)
    
    template_file = args.template
    if not os.path.exists(template_file):
        logger.error(f"템플릿 파일이 존재하지 않습니다: {template_file}")
        return
    
    output_file = args.output or f"cursor_translations_{args.target_lang.lower()}.json"
    
    translated, total = translator.update_translation_json(template_file, output_file, args.target_lang)
    logger.info(f"번역 완료: {translated}/{total} 항목이 번역되었습니다.")
    logger.info(f"번역 파일이 저장되었습니다: {output_file}")


if __name__ == "__main__":
    main()
