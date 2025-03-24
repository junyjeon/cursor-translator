import sys
import os
import json
from pathlib import Path
from PyQt5.QtWidgets import (QApplication, QMainWindow, QPushButton, QLabel, 
                           QVBoxLayout, QHBoxLayout, QWidget, QComboBox, 
                           QTextEdit, QFileDialog, QProgressBar, QMessageBox,
                           QTabWidget, QLineEdit, QCheckBox, QGroupBox, QGridLayout)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QIcon, QFont

# 커서 파인더 클래스 임포트
from cursor_finder import CursorFinder, find_main_js_file

# 이 파일 없으면 import 오류 날 수 있으므로 주석 처리
# 실제 코드 통합 시 import 활성화
# from cursor_translator import DeepLTranslator

class WorkerThread(QThread):
    update_progress = pyqtSignal(int)
    update_status = pyqtSignal(str)
    finished = pyqtSignal(bool, str)

    def __init__(self, function, *args, **kwargs):
        super().__init__()
        self.function = function
        self.args = args
        self.kwargs = kwargs

    def run(self):
        try:
            result = self.function(*self.args, **self.kwargs)
            self.finished.emit(True, "작업이 완료되었습니다.")
        except Exception as e:
            self.finished.emit(False, str(e))


class CursorTranslatorApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()
        self.cursor_path = None
        self.languages = {
            "한국어": "ko",
            "영어": "en",
            "일본어": "ja",
            "중국어 (간체)": "zh",
            "중국어 (번체)": "zh-TW",
            "프랑스어": "fr",
            "독일어": "de",
            "스페인어": "es",
            "러시아어": "ru",
            "이탈리아어": "it",
            "포르투갈어": "pt"
        }
        self.load_saved_settings()
        self.find_cursor_installation()

    def initUI(self):
        self.setWindowTitle('Cursor 번역기')
        self.setGeometry(100, 100, 800, 600)
        
        # 메인 위젯과 레이아웃 설정
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QVBoxLayout(main_widget)
        
        # 탭 위젯 생성
        self.tabs = QTabWidget()
        main_layout.addWidget(self.tabs)
        
        # 번역 탭
        self.translation_tab = QWidget()
        self.tabs.addTab(self.translation_tab, "번역")
        
        # 설정 탭
        self.settings_tab = QWidget()
        self.tabs.addTab(self.settings_tab, "설정")
        
        # 정보 탭
        self.about_tab = QWidget()
        self.tabs.addTab(self.about_tab, "정보")
        
        # 각 탭의 UI 설정
        self.setup_translation_tab()
        self.setup_settings_tab()
        self.setup_about_tab()
        
        # 상태 표시줄
        self.statusBar().showMessage('준비')

    def setup_translation_tab(self):
        layout = QVBoxLayout(self.translation_tab)
        
        # Cursor 경로 그룹
        path_group = QGroupBox("Cursor 설치 경로")
        path_layout = QHBoxLayout()
        
        self.path_label = QLabel("경로를 찾는 중...")
        path_layout.addWidget(self.path_label)
        
        self.find_path_btn = QPushButton("경로 찾기")
        self.find_path_btn.clicked.connect(self.find_cursor_installation)
        path_layout.addWidget(self.find_path_btn)
        
        self.browse_path_btn = QPushButton("경로 선택")
        self.browse_path_btn.clicked.connect(self.browse_cursor_path)
        path_layout.addWidget(self.browse_path_btn)
        
        path_group.setLayout(path_layout)
        layout.addWidget(path_group)
        
        # 언어 선택 그룹
        lang_group = QGroupBox("언어 설정")
        lang_layout = QHBoxLayout()
        
        lang_layout.addWidget(QLabel("번역할 언어:"))
        self.lang_combo = QComboBox()
        for lang in self.languages.keys():
            self.lang_combo.addItem(lang)
        lang_layout.addWidget(self.lang_combo)
        
        self.update_btn = QPushButton("번역 업데이트")
        self.update_btn.clicked.connect(self.update_translations)
        lang_layout.addWidget(self.update_btn)
        
        lang_group.setLayout(lang_layout)
        layout.addWidget(lang_group)
        
        # DeepL API 키 그룹
        api_group = QGroupBox("DeepL API 키 (선택사항)")
        api_layout = QHBoxLayout()
        
        self.api_key_input = QLineEdit()
        self.api_key_input.setPlaceholderText("DeepL API 키 (없으면 샘플 번역만 사용)")
        self.api_key_input.setEchoMode(QLineEdit.Password)
        api_layout.addWidget(self.api_key_input)
        
        self.show_key_checkbox = QCheckBox("API 키 표시")
        self.show_key_checkbox.stateChanged.connect(self.toggle_api_key_visibility)
        api_layout.addWidget(self.show_key_checkbox)
        
        api_group.setLayout(api_layout)
        layout.addWidget(api_group)
        
        # 진행상황 그룹
        progress_group = QGroupBox("진행상황")
        progress_layout = QVBoxLayout()
        
        self.progress_bar = QProgressBar()
        progress_layout.addWidget(self.progress_bar)
        
        self.status_label = QLabel("준비됨")
        progress_layout.addWidget(self.status_label)
        
        progress_group.setLayout(progress_layout)
        layout.addWidget(progress_group)
        
        # 명령 버튼 그룹
        button_layout = QHBoxLayout()
        
        self.extract_btn = QPushButton("텍스트 추출")
        self.extract_btn.clicked.connect(self.extract_strings)
        button_layout.addWidget(self.extract_btn)
        
        self.apply_btn = QPushButton("번역 적용")
        self.apply_btn.clicked.connect(self.apply_translations)
        button_layout.addWidget(self.apply_btn)
        
        self.backup_btn = QPushButton("백업")
        self.backup_btn.clicked.connect(self.backup_files)
        button_layout.addWidget(self.backup_btn)
        
        self.restore_btn = QPushButton("복원")
        self.restore_btn.clicked.connect(self.restore_backup)
        button_layout.addWidget(self.restore_btn)
        
        layout.addLayout(button_layout)

    def setup_settings_tab(self):
        layout = QVBoxLayout(self.settings_tab)
        
        # 자동 백업 설정
        backup_group = QGroupBox("백업 설정")
        backup_layout = QVBoxLayout()
        
        self.auto_backup_checkbox = QCheckBox("번역 적용 전 자동 백업")
        self.auto_backup_checkbox.setChecked(True)
        backup_layout.addWidget(self.auto_backup_checkbox)
        
        backup_dir_layout = QHBoxLayout()
        backup_dir_layout.addWidget(QLabel("백업 디렉토리:"))
        
        self.backup_dir_input = QLineEdit()
        self.backup_dir_input.setText(str(Path.home() / ".cursor_translator" / "backups"))
        backup_dir_layout.addWidget(self.backup_dir_input)
        
        self.browse_backup_btn = QPushButton("찾아보기")
        self.browse_backup_btn.clicked.connect(self.browse_backup_dir)
        backup_dir_layout.addWidget(self.browse_backup_btn)
        
        backup_layout.addLayout(backup_dir_layout)
        backup_group.setLayout(backup_layout)
        layout.addWidget(backup_group)
        
        # 고급 설정
        advanced_group = QGroupBox("고급 설정")
        advanced_layout = QVBoxLayout()
        
        self.test_mode_checkbox = QCheckBox("테스트 모드 (Cursor 없이 테스트)")
        advanced_layout.addWidget(self.test_mode_checkbox)
        
        self.save_untranslated_checkbox = QCheckBox("번역되지 않은 문자열 저장")
        self.save_untranslated_checkbox.setChecked(True)
        advanced_layout.addWidget(self.save_untranslated_checkbox)
        
        advanced_group.setLayout(advanced_layout)
        layout.addWidget(advanced_group)
        
        # 설정 저장/불러오기 버튼
        button_layout = QHBoxLayout()
        self.save_settings_btn = QPushButton("설정 저장")
        self.save_settings_btn.clicked.connect(self.save_settings)
        button_layout.addWidget(self.save_settings_btn)
        
        self.load_settings_btn = QPushButton("설정 불러오기")
        self.load_settings_btn.clicked.connect(self.load_settings)
        button_layout.addWidget(self.load_settings_btn)
        
        layout.addLayout(button_layout)
        layout.addStretch()

    def setup_about_tab(self):
        layout = QVBoxLayout(self.about_tab)
        
        # 앱 정보
        title_label = QLabel("Cursor 번역기")
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setFont(QFont('Arial', 16, QFont.Bold))
        layout.addWidget(title_label)
        
        version_label = QLabel("버전 1.0.0")
        version_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(version_label)
        
        desc_label = QLabel("Cursor IDE를 다양한 언어로 번역하기 위한 도구입니다.")
        desc_label.setAlignment(Qt.AlignCenter)
        desc_label.setWordWrap(True)
        layout.addWidget(desc_label)
        
        # 저작권 정보
        copyright_label = QLabel("© 2023 Cursor 번역 프로젝트")
        copyright_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(copyright_label)
        
        # GitHub 링크
        github_label = QLabel("<a href='https://github.com/yourusername/cursor-translator'>GitHub 저장소 방문</a>")
        github_label.setAlignment(Qt.AlignCenter)
        github_label.setOpenExternalLinks(True)
        layout.addWidget(github_label)
        
        layout.addStretch()

    def find_cursor_installation(self):
        self.status_label.setText("Cursor 설치 경로 검색 중...")
        
        # 별도 스레드에서 실행
        self.worker = WorkerThread(self._find_cursor_path)
        self.worker.finished.connect(self.on_path_search_finished)
        self.worker.start()

    def _find_cursor_path(self):
        finder = CursorFinder()
        return finder.find_cursor_installation()

    def on_path_search_finished(self, success, message):
        if success and message:
            self.cursor_path = message
            self.path_label.setText(str(message))
            self.status_label.setText("Cursor 설치 경로를 찾았습니다.")
        else:
            self.path_label.setText("경로를 찾을 수 없습니다. 수동으로 선택해주세요.")
            self.status_label.setText("자동 검색 실패. 수동 선택이 필요합니다.")

    def browse_cursor_path(self):
        dir_path = QFileDialog.getExistingDirectory(self, "Cursor 설치 디렉토리 선택")
        if dir_path:
            self.cursor_path = dir_path
            self.path_label.setText(dir_path)
            self.status_label.setText("Cursor 설치 경로가 선택되었습니다.")

    def browse_backup_dir(self):
        dir_path = QFileDialog.getExistingDirectory(self, "백업 디렉토리 선택")
        if dir_path:
            self.backup_dir_input.setText(dir_path)

    def toggle_api_key_visibility(self, state):
        if state == Qt.Checked:
            self.api_key_input.setEchoMode(QLineEdit.Normal)
        else:
            self.api_key_input.setEchoMode(QLineEdit.Password)

    def extract_strings(self):
        if not self.cursor_path and not self.test_mode_checkbox.isChecked():
            QMessageBox.warning(self, "경로 오류", "Cursor 설치 경로를 찾을 수 없습니다.")
            return
        
        self.status_label.setText("텍스트 추출 중...")
        self.progress_bar.setValue(0)
        
        # 여기에 실제 텍스트 추출 코드 추가
        # 현재는 예시 기능만 구현
        QMessageBox.information(self, "준비 중", "텍스트 추출 기능이 준비 중입니다.")
        self.status_label.setText("준비됨")

    def update_translations(self):
        lang_code = self.languages[self.lang_combo.currentText()]
        api_key = self.api_key_input.text().strip()
        
        if not api_key:
            response = QMessageBox.question(
                self, 
                "API 키 없음", 
                "DeepL API 키 없이 진행하면 샘플 번역만 사용됩니다. 계속하시겠습니까?",
                QMessageBox.Yes | QMessageBox.No
            )
            if response == QMessageBox.No:
                return
        
        self.status_label.setText(f"{self.lang_combo.currentText()} 번역 업데이트 중...")
        self.progress_bar.setValue(0)
        
        # 여기에 실제 번역 업데이트 코드 추가
        # 현재는 예시 기능만 구현
        QMessageBox.information(self, "준비 중", "번역 업데이트 기능이 준비 중입니다.")
        self.status_label.setText("준비됨")

    def apply_translations(self):
        if not self.cursor_path and not self.test_mode_checkbox.isChecked():
            QMessageBox.warning(self, "경로 오류", "Cursor 설치 경로를 찾을 수 없습니다.")
            return
        
        # 자동 백업 확인
        if self.auto_backup_checkbox.isChecked():
            self.backup_files()
        
        lang_code = self.languages[self.lang_combo.currentText()]
        
        self.status_label.setText(f"{self.lang_combo.currentText()} 번역 적용 중...")
        self.progress_bar.setValue(0)
        
        # 여기에 실제 번역 적용 코드 추가
        # 현재는 예시 기능만 구현
        QMessageBox.information(self, "준비 중", "번역 적용 기능이 준비 중입니다.")
        self.status_label.setText("준비됨")

    def backup_files(self):
        if not self.cursor_path and not self.test_mode_checkbox.isChecked():
            QMessageBox.warning(self, "경로 오류", "Cursor 설치 경로를 찾을 수 없습니다.")
            return
        
        backup_dir = self.backup_dir_input.text()
        
        self.status_label.setText("파일 백업 중...")
        self.progress_bar.setValue(0)
        
        # 여기에 실제 백업 코드 추가
        # 현재는 예시 기능만 구현
        QMessageBox.information(self, "준비 중", "백업 기능이 준비 중입니다.")
        self.status_label.setText("준비됨")

    def restore_backup(self):
        backup_dir = self.backup_dir_input.text()
        
        self.status_label.setText("백업 복원 중...")
        self.progress_bar.setValue(0)
        
        # 여기에 실제 복원 코드 추가
        # 현재는 예시 기능만 구현
        QMessageBox.information(self, "준비 중", "복원 기능이 준비 중입니다.")
        self.status_label.setText("준비됨")

    def save_settings(self):
        settings_path = Path.home() / '.cursor_translator' / 'settings.json'
        settings_path.parent.mkdir(parents=True, exist_ok=True)
        
        settings = {
            'cursor_path': self.cursor_path,
            'backup_dir': self.backup_dir_input.text(),
            'language': self.lang_combo.currentText(),
            'auto_backup': self.auto_backup_checkbox.isChecked(),
            'test_mode': self.test_mode_checkbox.isChecked(),
            'save_untranslated': self.save_untranslated_checkbox.isChecked(),
            'api_key': self.api_key_input.text() if self.api_key_input.text() else ''
        }
        
        try:
            with open(settings_path, 'w', encoding='utf-8') as f:
                json.dump(settings, f, ensure_ascii=False, indent=2)
            self.status_label.setText("설정이 저장되었습니다.")
        except Exception as e:
            self.status_label.setText(f"설정 저장 오류: {str(e)}")

    def load_settings(self):
        """현재 설정 파일 로드"""
        settings_path = QFileDialog.getOpenFileName(self, "설정 파일 선택", str(Path.home()), "JSON 파일 (*.json)")[0]
        if settings_path:
            try:
                with open(settings_path, 'r', encoding='utf-8') as f:
                    settings = json.load(f)
                
                self.apply_loaded_settings(settings)
                self.status_label.setText("설정을 불러왔습니다.")
            except Exception as e:
                self.status_label.setText(f"설정 로드 오류: {str(e)}")

    def load_saved_settings(self):
        """저장된 설정 자동 로드"""
        settings_path = Path.home() / '.cursor_translator' / 'settings.json'
        
        if settings_path.exists():
            try:
                with open(settings_path, 'r', encoding='utf-8') as f:
                    settings = json.load(f)
                
                self.apply_loaded_settings(settings)
            except Exception:
                # 오류 발생 시 기본 설정 사용
                pass

    def apply_loaded_settings(self, settings):
        """로드된 설정 적용"""
        if 'cursor_path' in settings and settings['cursor_path']:
            self.cursor_path = settings['cursor_path']
            self.path_label.setText(self.cursor_path)
        
        if 'backup_dir' in settings:
            self.backup_dir_input.setText(settings['backup_dir'])
        
        if 'language' in settings:
            index = self.lang_combo.findText(settings['language'])
            if index >= 0:
                self.lang_combo.setCurrentIndex(index)
        
        if 'auto_backup' in settings:
            self.auto_backup_checkbox.setChecked(settings['auto_backup'])
        
        if 'test_mode' in settings:
            self.test_mode_checkbox.setChecked(settings['test_mode'])
        
        if 'save_untranslated' in settings:
            self.save_untranslated_checkbox.setChecked(settings['save_untranslated'])
        
        if 'api_key' in settings and settings['api_key']:
            self.api_key_input.setText(settings['api_key'])


def main():
    app = QApplication(sys.argv)
    ex = CursorTranslatorApp()
    ex.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main() 