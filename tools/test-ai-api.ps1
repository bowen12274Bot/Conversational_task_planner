param(
    [string]$ApiUrl = "http://127.0.0.1:8000/api/ai-test",
    [string]$TaskType = "text_output",
    [string]$GroupName = "questioning_response",
    [string]$CapabilityLevel = "default",
    [string]$UserInput = "測試API連接，請只輸出成功兩字",
    [string]$OutputTarget = "只輸出成功"
)

$projectRoot = Split-Path -Parent $PSScriptRoot
$pythonExe = Join-Path $projectRoot ".venv\Scripts\python.exe"

if (-not (Test-Path $pythonExe)) {
    throw "Project venv Python not found: $pythonExe"
}

$env:AI_TEST_API_URL = $ApiUrl
$env:AI_TEST_TASK_TYPE = $TaskType
$env:AI_TEST_GROUP_NAME = $GroupName
$env:AI_TEST_CAPABILITY_LEVEL = $CapabilityLevel
$env:AI_TEST_USER_INPUT = $UserInput
$env:AI_TEST_OUTPUT_TARGET = $OutputTarget

@'
import json
import os

import httpx

payload = {
    "task_type": os.environ["AI_TEST_TASK_TYPE"],
    "group_name": os.environ["AI_TEST_GROUP_NAME"],
    "capability_level": os.environ["AI_TEST_CAPABILITY_LEVEL"],
    "input_data": {
        "user_input": os.environ["AI_TEST_USER_INPUT"],
    },
    "output_target": os.environ["AI_TEST_OUTPUT_TARGET"],
}

response = httpx.post(
    os.environ["AI_TEST_API_URL"],
    json=payload,
    timeout=30.0,
)
response.raise_for_status()
print(json.dumps(response.json(), ensure_ascii=False, indent=2))
'@ | & $pythonExe -
