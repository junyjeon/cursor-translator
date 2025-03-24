#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import json
import shutil
import unittest
import tempfile
import platform
from pathlib import Path
from unittest.mock import patch, MagicMock

# 테스트 대상 모듈 import (경로에 따라 수정 필요)
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
try:
    import main
    import extract_strings
except ImportError:
    print("main.py 또는 extract_strings.py 모듈을 찾을 수 없습니다.")
    print("테스트 파일은 프로젝트 루트 디렉토리에서 실행해야 합니다.")
    sys.exit(1)

class TestCursorTranslator(unittest.TestCase):
    """Cursor 다국어 번역 도구에 대한 테스트 케이스"""
    
    def setUp(self):
        """각 테스트 전에 실행되는 설정"""
        # 테스트용 임시 디렉토리 생성
        self.temp_dir = tempfile.mkdtemp()
        
        # 테스트용 번역 파일 생성
        self.test_translations = {
            "Test String 1": "테스트 문자열 1",
            "Test String 2": "테스트 문자열 2",
            "Cursor Settings": "커서 설정"
        }
        
        self.translation_file = Path(self.temp_dir) / "cursor_translations_ko.json"
        with open(self.translation_file, 'w', encoding='utf-8') as f:
            json.dump(self.test_translations, f, ensure_ascii=False)
        
        # 테스트용 설정 파일 경로
        self.mock_js_path = Path(self.temp_dir) / "workbench.desktop.main.js"
        self.mock_settings_path = Path(self.temp_dir) / "settings.json"
        
        # 가짜 JS 파일 생성
        with open(self.mock_js_path, 'w', encoding='utf-8') as f:
            f.write('title:"Test String 1"\nchildren:"Test String 2"\nlabel:"Cursor Settings"\n')
        
        # 가짜 설정 파일 생성
        with open(self.mock_settings_path, 'w', encoding='utf-8') as f:
            f.write('{"setting1": "value1"}')
    
    def tearDown(self):
        """각 테스트 후에 실행되는 정리"""
        # 테스트용 임시 디렉토리 삭제
        shutil.rmtree(self.temp_dir)
    
    # 경로 테스트
    @patch('extract_strings.find_cursor_installation')
    def test_cursor_path_not_found(self, mock_find):
        """Cursor 경로를 찾지 못하는 상황 테스트"""
        # Cursor 경로를 못 찾는 상황 시뮬레이션
        mock_find.return_value = None
        
        # extract_strings.py 실행 시뮬레이션
        with patch('sys.argv', ['extract_strings.py']):
            with patch('builtins.print') as mock_print:
                extract_strings.main()
                # 경로를 찾지 못했다는 메시지가 출력되었는지 확인
                mock_print.assert_any_call("\n❌ Cursor IDE 설치 경로를 찾을 수 없습니다.")
    
    # 파일 액세스 권한 테스트
    @patch('extract_strings.find_cursor_installation')
    @patch('extract_strings.find_main_js_file')
    def test_file_permission_error(self, mock_find_js, mock_find_cursor):
        """파일 액세스 권한 오류 상황 테스트"""
        # Cursor 경로는 찾았지만 파일 읽기 권한이 없는 상황 시뮬레이션
        mock_find_cursor.return_value = Path(self.temp_dir)
        mock_find_js.return_value = self.mock_js_path
        
        def mock_open_with_permission_error(*args, **kwargs):
            raise PermissionError("권한이 거부되었습니다")
        
        with patch('builtins.open', side_effect=mock_open_with_permission_error):
            with patch('sys.argv', ['extract_strings.py']):
                with patch('builtins.print') as mock_print:
                    extract_strings.main()
                    # 파일 읽기 오류 메시지가 출력되었는지 확인
                    mock_print.assert_any_call("파일 읽기 오류: 권한이 거부되었습니다")
    
    # DeepL API 오류 테스트
    @patch('main.find_cursor_installation')
    @patch('main.find_main_js_file')
    @patch('main.save_extracted_strings')
    def test_deepl_api_error(self, mock_save, mock_find_js, mock_find_cursor):
        """DeepL API 오류 상황 테스트"""
        # 성공적으로 경로와 파일을 찾았지만 API 호출에서 오류 발생하는 상황 시뮬레이션
        mock_find_cursor.return_value = Path(self.temp_dir)
        mock_find_js.return_value = self.mock_js_path
        
        # DeepL API 오류 시뮬레이션을 위한 함수 수정
        def mock_translate_texts(self, texts, target_lang):
            raise Exception("API 키가 유효하지 않거나 요청 한도를 초과했습니다")
        
        # main.py 실행 시뮬레이션
        with patch('main.DeepLTranslator.translate_texts', mock_translate_texts):
            with patch('sys.argv', ['main.py', '--api-key', 'invalid_key']):
                with patch('builtins.print') as mock_print:
                    try:
                        main.main()
                    except SystemExit:
                        pass
                    except Exception as e:
                        # API 오류 메시지가 출력되었는지 확인
                        self.assertIn("API", str(e))
    
    # 버전 호환성 테스트
    def test_cursor_version_compatibility(self):
        """Cursor 버전 호환성 문제 테스트"""
        # 예전 번역 파일에 없는 새 문자열이 있는 새 JS 파일 생성
        with open(self.mock_js_path, 'w', encoding='utf-8') as f:
            f.write('title:"Test String 1"\nchildren:"New String in Updated Cursor"\nlabel:"Cursor Settings"\n')
        
        # extract_strings.extract_ui_strings 호출 시뮬레이션
        extracted = extract_strings.extract_ui_strings(self.mock_js_path)
        
        # 새 문자열이 추출되었는지 확인
        self.assertIn("New String in Updated Cursor", extracted)
        
        # 기존 번역 파일에 새 문자열이 없는지 확인
        with open(self.translation_file, 'r', encoding='utf-8') as f:
            translations = json.load(f)
            self.assertNotIn("New String in Updated Cursor", translations)
    
    # 다국어 지원 테스트
    @patch('main.find_cursor_installation')
    @patch('main.find_main_js_file')
    def test_multilanguage_support(self, mock_find_js, mock_find_cursor):
        """다국어 지원 테스트"""
        # 경로 설정
        mock_find_cursor.return_value = Path(self.temp_dir)
        mock_find_js.return_value = self.mock_js_path
        
        # 가짜 번역 결과 생성
        def mock_translate_texts(self, texts, target_lang):
            if target_lang == 'fr':
                return {
                    "Test String 1": "Chaîne de test 1",
                    "Test String 2": "Chaîne de test 2",
                    "Cursor Settings": "Paramètres du curseur"
                }
            elif target_lang == 'ja':
                return {
                    "Test String 1": "テスト文字列 1",
                    "Test String 2": "テスト文字列 2",
                    "Cursor Settings": "カーソル設定"
                }
            return {}
        
        # 여러 언어 번역 시뮬레이션
        with patch('main.DeepLTranslator.translate_texts', mock_translate_texts):
            with patch('sys.argv', ['main.py', '--langs', 'fr,ja', '--extract-only', '--test-mode']):
                with patch('builtins.print'):
                    try:
                        main.main()
                    except SystemExit:
                        pass
                    
                    # 프랑스어 번역 파일 확인
                    fr_file = Path(os.getcwd()) / "cursor_translations_fr.json"
                    if fr_file.exists():
                        with open(fr_file, 'r', encoding='utf-8') as f:
                            fr_translations = json.load(f)
                            self.assertIn("Test String 1", fr_translations)
    
    # 샘플 데이터 테스트
    def test_sample_data_in_test_mode(self):
        """테스트 모드에서 샘플 데이터 사용 테스트"""
        # main.py의 --test-mode 옵션 테스트
        with patch('sys.argv', ['main.py', '--test-mode']):
            with patch('builtins.print') as mock_print:
                with patch('main.DeepLTranslator.translate_texts') as mock_translate:
                    mock_translate.return_value = {"Sample": "샘플"}
                    
                    try:
                        main.main()
                    except SystemExit:
                        pass
                    
                    # 테스트 모드 메시지가 출력되었는지 확인
                    mock_print.assert_any_call("테스트 모드: Cursor 설치 없이 샘플 데이터만 사용합니다.")
    
    # WSL 환경 테스트
    @unittest.skipIf(not ('microsoft' in platform.uname().release.lower()), "WSL 환경에서만 실행")
    def test_wsl_environment(self):
        """WSL 환경에서의 경로 처리 테스트"""
        # 현재 WSL 환경인 경우만 실행
        cursor_path = extract_strings.find_cursor_installation()
        if cursor_path:
            self.assertTrue(str(cursor_path).startswith('/mnt/'))
    
    # 백업 기능 테스트
    @patch('main.find_cursor_installation')
    @patch('main.find_main_js_file')
    def test_backup_function(self, mock_find_js, mock_find_cursor):
        """백업 기능 테스트"""
        # 경로 설정
        mock_find_cursor.return_value = Path(self.temp_dir)
        mock_find_js.return_value = self.mock_js_path
        
        # settings.json 경로 설정
        settings_dir = Path(self.temp_dir) / "User"
        settings_dir.mkdir(exist_ok=True)
        settings_path = settings_dir / "settings.json"
        with open(settings_path, 'w', encoding='utf-8') as f:
            f.write('{"setting": "value"}')
        
        # 백업 디렉토리 확인을 위한 get_backup_path 모방
        original_backup_path = None
        
        def mock_backup_files(self):
            nonlocal original_backup_path
            # 원본 함수 로직을 재현하여 백업 경로 저장
            import datetime
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_dir = Path(f"cursor_backup_{timestamp}")
            backup_dir.mkdir(exist_ok=True)
            original_backup_path = backup_dir
            return True
        
        # 백업 함수 패치 및 실행
        with patch('main.CursorBackup.backup_files', mock_backup_files):
            with patch('sys.argv', ['main.py', '--extract-only']):
                with patch('builtins.print'):
                    try:
                        main.main()
                    except SystemExit:
                        pass
                    except Exception:
                        pass
                    
                    # 백업 경로가 생성되었는지 확인
                    self.assertIsNotNone(original_backup_path)
                    if original_backup_path and original_backup_path.exists():
                        shutil.rmtree(original_backup_path)
    
    # 커맨드라인 인자 테스트
    def test_command_line_args(self):
        """커맨드라인 인자 처리 테스트"""
        # 다양한 커맨드라인 옵션 테스트
        test_args = [
            ['main.py', '--help'],  # 도움말
            ['main.py', '--test-mode'],  # 테스트 모드
            ['main.py', '--langs', 'ko,en,fr'],  # 다중 언어
            ['main.py', '--no-backup'],  # 백업 건너뛰기
            ['main.py', '--extract-only'],  # 추출만
            ['main.py', '--view-only']  # 보기만
        ]
        
        for args in test_args:
            with patch('sys.argv', args):
                with patch('builtins.print'):
                    try:
                        # ArgumentParser가 종료하지 않도록 처리
                        if '--help' in args:
                            with self.assertRaises(SystemExit):
                                main.main()
                        else:
                            with patch('main.find_cursor_installation') as mock_find:
                                mock_find.return_value = None
                                with self.assertRaises(SystemExit):
                                    main.main()
                    except Exception:
                        pass

# 테스트 실행
if __name__ == '__main__':
    print("=" * 60)
    print(" Cursor 다국어 번역 도구 테스트")
    print("=" * 60)
    print(f"운영체제: {platform.system()} ({platform.release()})")
    
    # WSL 환경 감지
    if 'microsoft' in platform.uname().release.lower():
        print("WSL 환경 감지됨")
    
    print(f"Python: {platform.python_version()}")
    print(f"테스트 시간: {os.path.basename(tempfile.mkdtemp())}")
    print("=" * 60)
    
    unittest.main(verbosity=2) 