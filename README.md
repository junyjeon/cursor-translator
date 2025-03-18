# Cursor-Translator (커서 다국어 번역 도구)

Cursor IDE의 설정과 UI를 다국어로 번역해주는 도구입니다. 기본 영어 인터페이스를 다양한 언어로 사용할 수 있게 해줍니다.

## 기능

- Cursor IDE 설정 텍스트 자동 추출
- DeepL API를 통한 9개 언어 자동 번역 지원
- API 키 없이도 기본 번역 제공
- 파일 자동 백업으로 안전하게 사용
- WSL 환경 자동 감지 및 경로 처리

## 지원 언어

- 한국어(ko)
- 일본어(ja)
- 중국어(zh)
- 프랑스어(fr)
- 독일어(de)
- 스페인어(es)
- 이탈리아어(it)
- 포르투갈어(pt)
- 러시아어(ru)

## 설치 및 사용 방법

### 1. 저장소 클론

```bash
git clone https://github.com/사용자명/cursor-translator.git
cd cursor-translator
```

### 2. 필요한 라이브러리 설치

```bash
pip install requests
```

### 3. 프로그램 실행

기본 실행 (한국어 번역):
```bash
python main.py
```

특정 경로의 Cursor IDE 사용:
```bash
python main.py --cursor-path "C:\Path\To\Cursor"
```

여러 언어 번역 (DeepL API 키 사용):
```bash
python main.py --api-key YOUR_DEEPL_API_KEY --langs ko,ja,zh
```

Cursor가 설치되지 않은 환경에서 테스트:
```bash
python main.py --test-mode
```

기존 번역 파일만 확인:
```bash
python main.py --view-only
```

### 4. EXE 파일 생성 (Windows)

```bash
python build_exe.py
```

## 사용 팁

- 번역된 JSON 파일은 `cursor_translations_[언어코드].json` 형식으로 저장됩니다.
- 원본 텍스트는 `cursor_strings.txt`에 저장됩니다.
- 중요 파일은 자동으로 `cursor_backup_[날짜시간]` 폴더에 백업됩니다.

## 주의 사항

- 이 도구는 Cursor IDE 공식 제품이 아닙니다.
- DeepL API 키가 없어도 기본 제공되는 번역을 사용할 수 있지만, 전체 번역을 위해서는 API 키가 필요합니다.
- API 키는 [DeepL 개발자 페이지](https://www.deepl.com/pro#developer)에서 무료로 발급받을 수 있습니다.

## 라이선스

MIT License

## 기여하기

1. 이 저장소를 포크합니다.
2. 새 브랜치를 만듭니다 (`git checkout -b feature/amazing-feature`).
3. 변경 사항을 커밋합니다 (`git commit -m 'Add some amazing feature'`).
4. 브랜치에 푸시합니다 (`git push origin feature/amazing-feature`).
5. Pull Request를 작성합니다. 