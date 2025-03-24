# Cursor 번역기 (Cursor Translator)

Cursor IDE를 다양한 언어로 번역하기 위한 도구입니다. 이 도구를 사용하면 Cursor IDE의 UI를 한국어나 다른 언어로 쉽게 변경할 수 있습니다.

## 특징

- WSL, Windows, macOS, Linux 환경 자동 감지
- DeepL API를 사용한 고품질 번역 (API 키 선택 사항)
- 사용자 친화적인 GUI 인터페이스
- 자동 백업 및 복원 기능
- 다양한 언어 지원 (한국어, 일본어, 중국어 등)
- 테스트 모드 (실제 Cursor 설치 없이도 작동)

## 설치 방법

### 요구 사항

- Python 3.6 이상
- DeepL API 키 (선택 사항)

### 설치

```bash
# 저장소 클론
git clone https://github.com/yourusername/cursor-translator.git
cd cursor-translator

# 필요한 패키지 설치
pip install -r requirements.txt
```

## 사용 방법

### GUI 모드

```bash
python cursor_translator_app.py
```

### 명령줄 모드

#### 텍스트 추출 및 번역 템플릿 생성

```bash
python main.py --extract --target-lang ko
```

#### 번역 적용

```bash
python main.py --translate --target-lang ko
```

#### 백업 목록 보기

```bash
python main.py --list-backups
```

#### 백업에서 복원

```bash
python main.py --restore --backup-index 1
```

#### 테스트 모드 (Cursor 설치 없이 실행)

```bash
python main.py --test-mode
```

### DeepL API 키 사용

API 키는 다음 방법으로 제공할 수 있습니다:

1. 명령줄 인수로 전달:
```bash
python main.py --api-key YOUR_API_KEY
```

2. 환경 변수 설정:
```bash
export DEEPL_API_KEY=YOUR_API_KEY
python main.py
```

3. GUI에서 입력

## 주요 옵션

- `--cursor-path`: Cursor 설치 경로를 직접 지정
- `--api-key`: DeepL API 키
- `--target-lang`: 대상 언어 코드 (기본값: ko)
- `--test-mode`: 테스트 모드 활성화
- `--extract`: 텍스트 추출 모드
- `--translate`: 번역 적용 모드
- `--restore`: 백업에서 복원 모드
- `--list-backups`: 백업 목록 표시
- `--no-backup`: 백업 건너뛰기
- `--backup-index`: 복원할 백업 인덱스

## 프로젝트 구조

```
cursor-translator/
│
├── main.py                  # 메인 스크립트
├── cursor_translator_app.py # GUI 애플리케이션
├── cursor_finder.py         # Cursor 설치 경로 찾기
├── cursor_extractor.py      # 텍스트 추출
├── cursor_translator.py     # 번역 기능
│
├── cursor_translations_ko.json   # 한국어 번역 파일
├── cursor_translations_ja.json   # 일본어 번역 파일
├── cursor_translations_zh.json   # 중국어 번역 파일
│
├── requirements.txt         # 의존성 목록
└── README.md                # 프로젝트 설명
```

## 주의사항

- 번역 적용 전 항상 백업이 자동으로 생성됩니다.
- 문제가 발생할 경우 `--restore` 옵션으로 원본 파일을 복원할 수 있습니다.
- DeepL API 키는 선택 사항이며, 키가 없으면 샘플 번역과 기존 번역만 사용됩니다.

## 라이선스

MIT

## 기여

버그 신고, 기능 제안, PR은 언제나 환영합니다. 