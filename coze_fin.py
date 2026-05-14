import json
import os
from pathlib import Path

import requests
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[1] / ".env")
url = "https://8mbn769hk8.coze.site/stream_run"
headers = {
  "Authorization": f"Bearer {os.getenv('COZE_FINANCE_API_TOKEN')}",
  "Content-Type": "application/json",
  "Accept": "text/event-stream",
}
payload = json.loads(r'''{
  "content": {
    "query": {
      "prompt": [
        {
          "type": "text",
          "content": {
            "text": "请结合当前A股环境，分析洲明科技300232是否适合当前入仓。输出：结论、价格区间、仓位策略、核心风险、加仓触发条件。"
          }
        }
      ]
    }
  },
  "type": "query",
  "session_id": "HQarl1TSlF5Ovhyl7T4F9",
  "project_id": "7598933258117611561"
}''')
response = requests.post(url, headers=headers, json=payload, stream=True)
print("status:", response.status_code)
try:
  response.raise_for_status()
except Exception:
  print(response.text)
  raise
for line in response.iter_lines(decode_unicode=True):
  if line and line.startswith("data:"):
    data_text = line[5:].strip()
    try:
      parsed = json.loads(data_text)
      print(json.dumps(parsed, ensure_ascii=False, indent=2))
    except Exception:
      print(data_text)