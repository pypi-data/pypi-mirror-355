# 📘 Rubric MCP Server

학생 과제 루브릭을 자동 생성하고 피드백을 제공하는 **Model Context Protocol (MCP) 서버**입니다. FastAPI와 FastMCP 기반으로 구축되어 있으며, PyPI를 통해 설치하거나 `uvx` 명령어로 바로 실행할 수 있습니다.

---

## ✨ 주요 기능

- ✅ 학습 주제/목표/학년에 따라 루브릭 자동 생성
- ✅ 제출된 과제가 있으면 AI 기반 피드백도 자동 제공
- 📚 학생의 학습 목표와 수준을 고려한 **도서 추천 기능** 포함
- ⚡ FastMCP 프로토콜 기반으로 Claude/ChatGPT/Gemini 등과 연동 가능
- 🧩 MCP Tool로 통합되어 AI 워크플로우에 쉽게 삽입 가능

---

## 🧰 MCP 명령어 (`tool`)

### `generate_rubric_feedback`

| 입력 파라미터              | 타입       | 필수 여부 | 설명     |
| -------------------- | -------- | ----- | ------ |
| `topic`              | `string` | ✅     | 과제 주제  |
| `objective`          | `string` | ✅     | 학습 목표  |
| `grade_level`        | `string` | ✅     | 학년 정보  |
| `name`               | `string` | ❌     | 학생 이름  |
| `student_submission` | `string` | ❌     | 과제 제출물 |

---

## **출력:**

```json
{
  "rubric_standards": "과제 평가 기준",
  "grading_feedback": "학생 피드백 (선택적)"
}

---

## 📦 설치 방법

⚙️ MCP 플랫폼에서 사용 (uvx 권장)

MCP 설정 파일 (claude_desktop_config.json 등)에 아래 내용을 추가하세요:

{
  "mcpServers": {
    "rubric": {
      "command": "uvx",
      "args": ["rubric-mcp-server"],
      "env": {
        "OPENAI_API_KEY": "your-openai-key",
        "GOOGLE_API_KEY": "your-google-key",
        "MODEL_TYPE": "openai",              // 또는 gemini
        "MODEL_NAME": "gpt-4o-mini"          // 또는 gemini-2.0-flash 등
      }
    }
  }
}

---
## 📄 라이선스

MIT License © 2025 Jongbok Lee