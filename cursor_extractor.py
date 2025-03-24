import os
import re
import json
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class CursorExtractor:
    def __init__(self, js_file_path, strings_file=None):
        """
        Cursor IDE의 텍스트 추출기
        
        Args:
            js_file_path: workbench.desktop.main.js 파일 경로
            strings_file: 추출된 문자열을 저장할 파일 경로 (기본값: cursor_strings.txt)
        """
        self.js_file_path = Path(js_file_path)
        self.strings_file = strings_file or "cursor_strings.txt"
        
        if not self.js_file_path.exists():
            raise FileNotFoundError(f"파일을 찾을 수 없습니다: {js_file_path}")

    def extract_strings(self):
        """
        JS 파일에서 번역 가능한 문자열을 추출
        
        Returns:
            str: 추출된 문자열이 저장된 파일 경로
        """
        logger.info(f"JS 파일에서 문자열 추출 시작: {self.js_file_path}")
        
        # 다양한 패턴의 문자열 추출
        patterns = [
            r'["\']((?:\s*\{[^{}]*\}\s*[,]?)*\s*\{[^{}]*label[^{}]*["\']\s*:\s*["\'](.*?)["\'][^{}]*\}(?:\s*\{[^{}]*\}\s*[,]?)*)["\']\s*,',
            r'["\']((?:\s*\{[^{}]*\}\s*[,]?)*\s*\{[^{}]*title[^{}]*["\']\s*:\s*["\'](.*?)["\'][^{}]*\}(?:\s*\{[^{}]*\}\s*[,]?)*)["\']\s*,',
            r'[\'"]label[\'"]\s*:\s*[\'"]([^\'"]+)[\'"]',
            r'[\'"]categoryLabel[\'"]\s*:\s*[\'"]([^\'"]+)[\'"]',
            r'[\'"]placeholder[\'"]\s*:\s*[\'"]([^\'"]+)[\'"]',
            r'[\'"]detail[\'"]\s*:\s*[\'"]([^\'"]+)[\'"]',
            r'[\'"]title[\'"]\s*:\s*[\'"]([^\'"]+)[\'"]',
            r'[\'"]message[\'"]\s*:\s*[\'"]([^\'"]+)[\'"]',
            r'[\'"]buttonLabel[\'"]\s*:\s*[\'"]([^\'"]+)[\'"]',
            r'[\'"]failureMessage[\'"]\s*:\s*[\'"]([^\'"]+)[\'"]',
            r'[\'"]successMessage[\'"]\s*:\s*[\'"]([^\'"]+)[\'"]',
            r'[\'"]value[\'"]\s*:\s*[\'"]([^\'"]+)[\'"]',
            r'[\'"]aria-label[\'"]\s*:\s*[\'"]([^\'"]+)[\'"]',
            r'[\'"]name[\'"]\s*:\s*[\'"]([^\'"]+)[\'"]',
        ]
        
        extracted_strings = set()
        
        with open(self.js_file_path, 'r', encoding='utf-8', errors='ignore') as file:
            content = file.read()
            
            for pattern in patterns:
                matches = re.findall(pattern, content)
                if matches:
                    if isinstance(matches[0], tuple):
                        # 일부 패턴은 그룹을 두 개 가질 수 있음
                        for match in matches:
                            extracted_strings.add(match[-1])  # 마지막 그룹 사용
                    else:
                        extracted_strings.update(matches)
        
        # 불필요한 문자열 필터링
        filtered_strings = self._filter_strings(extracted_strings)
        
        # 정렬 및 저장
        sorted_strings = sorted(filtered_strings)
        
        with open(self.strings_file, 'w', encoding='utf-8') as file:
            for string in sorted_strings:
                file.write(f"{string}\n")
        
        logger.info(f"총 {len(sorted_strings)}개의 문자열을 추출하여 {self.strings_file}에 저장했습니다.")
        return self.strings_file

    def _filter_strings(self, strings):
        """문자열 필터링"""
        filtered = set()
        
        # 필터링 조건
        min_length = 2  # 최소 길이
        max_length = 500  # 최대 길이
        exclude_patterns = [
            r'^[0-9]+$',  # 숫자만
            r'^[a-zA-Z0-9]{1,3}$',  # 1-3자 영숫자
            r'^https?://',  # URL
            r'^www\.',  # URL
            r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$',  # 이메일
            r'^[a-zA-Z0-9_\-/\\]+$',  # 경로 및 파일 이름
        ]
        
        for s in strings:
            # 쉼표나 점만 있는 경우 건너뛰기
            if s.strip() in [',', '.', ':', ';']:
                continue
                
            # 길이 검사
            if len(s) < min_length or len(s) > max_length:
                continue
                
            # 패턴 검사
            if any(re.match(pattern, s) for pattern in exclude_patterns):
                continue
                
            filtered.add(s)
            
        return filtered

    def generate_translation_template(self, output_file=None):
        """번역 템플릿 생성"""
        output_file = output_file or "cursor_translations_template.json"
        
        if not os.path.exists(self.strings_file):
            logger.warning(f"문자열 파일이 없습니다: {self.strings_file}")
            self.extract_strings()
        
        template = {}
        
        with open(self.strings_file, 'r', encoding='utf-8') as file:
            for line in file:
                string = line.strip()
                if string:
                    template[string] = ""
        
        with open(output_file, 'w', encoding='utf-8') as file:
            json.dump(template, file, ensure_ascii=False, indent=2)
        
        logger.info(f"번역 템플릿이 생성되었습니다: {output_file}")
        return output_file

    def generate_sample_strings(self, output_file=None):
        """샘플 문자열 생성 (테스트 모드용)"""
        output_file = output_file or "cursor_strings.txt"
        
        # 일반적인 UI 요소에 대한 샘플 문자열
        sample_strings = [
            "Open File",
            "Save",
            "Save As...",
            "Close",
            "Close All",
            "Preferences",
            "Settings",
            "Cut",
            "Copy",
            "Paste",
            "Find",
            "Replace",
            "Go to Line",
            "Toggle Comment",
            "Indent",
            "Outdent",
            "Format Document",
            "Toggle Terminal",
            "Zoom In",
            "Zoom Out",
            "Full Screen",
            "Split Editor",
            "Toggle Sidebar",
            "Problems",
            "Output",
            "Debug Console",
            "Extensions",
            "Search",
            "Explorer",
            "Source Control",
            "Run and Debug",
            "Testing",
            "Command Palette",
            "Quick Open",
            "File",
            "Edit",
            "Selection",
            "View",
            "Go",
            "Run",
            "Terminal",
            "Help",
            "New File",
            "New Window",
            "Open Folder",
            "Add Folder to Workspace",
            "Save Workspace As...",
            "Keyboard Shortcuts",
            "Color Theme",
            "Welcome",
            "Interactive Playground",
            "Documentation",
            "Release Notes",
            "Check for Updates",
            "About"
        ]
        
        with open(output_file, 'w', encoding='utf-8') as file:
            for string in sample_strings:
                file.write(f"{string}\n")
        
        logger.info(f"샘플 문자열 파일이 생성되었습니다: {output_file}")
        return output_file


def main():
    import argparse
    from cursor_finder import CursorFinder, find_main_js_file
    
    parser = argparse.ArgumentParser(description='Cursor IDE의 텍스트 추출')
    parser.add_argument('--cursor-path', help='Cursor 설치 경로')
    parser.add_argument('--output', help='출력 파일 경로')
    parser.add_argument('--test-mode', action='store_true', help='테스트 모드')
    
    args = parser.parse_args()
    
    if args.test_mode:
        logger.info("테스트 모드로 실행합니다.")
        extractor = CursorExtractor("dummy_path")
        strings_file = extractor.generate_sample_strings()
        template_file = extractor.generate_translation_template()
        logger.info(f"샘플 데이터 생성 완료: {strings_file}, {template_file}")
        return
    
    cursor_path = args.cursor_path
    if not cursor_path:
        finder = CursorFinder()
        cursor_path = finder.find_cursor_installation()
    
    if not cursor_path:
        logger.error("Cursor 설치 경로를 찾을 수 없습니다.")
        return
    
    js_file = find_main_js_file(Path(cursor_path))
    if not js_file:
        logger.error("workbench.desktop.main.js 파일을 찾을 수 없습니다.")
        return
    
    output_file = args.output or "cursor_strings.txt"
    extractor = CursorExtractor(js_file, output_file)
    strings_file = extractor.extract_strings()
    template_file = extractor.generate_translation_template()
    
    logger.info(f"추출 완료: {strings_file}")
    logger.info(f"템플릿 생성 완료: {template_file}")


if __name__ == "__main__":
    main()
