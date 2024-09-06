from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Union, Optional
import os
from dotenv import load_dotenv
import google.generativeai as genai
import json

app = FastAPI()

# 환경 변수 로드
load_dotenv()
apikey = os.getenv("geminiapi")

# Gemini API 설정
genai.configure(api_key=apikey)

# 데이터 모델
class Choice(BaseModel):
    character: str
    choice_count: int

class Opt(BaseModel):
    opt_title: str

class StoryResponse(BaseModel):
    choice_number: int
    story: str
    opt1: List[str]
    opt2: List[str]

class FinalResponse(BaseModel):
    choice_number: int
    story: str
    opt1: List[str]
    opt2: List[str]
    final_scenario: Optional[str] = None
    historical_changes: Optional[str] = None
    comparison: Optional[str] = None

# 전역 변수로 채팅 세션 저장
chat_session = None

# stary_story로 chat session 시작
@app.post("/start_story")
async def start_story(choice: Choice):
    global chat_session
    generation_config = {
    "temperature": 1,
    "top_p": 0.95,
    "top_k": 64,
    "max_output_tokens": 8192,
    }
    model = genai.GenerativeModel(
        model_name="gemini-1.5-flash",
        generation_config=generation_config,
        # safety_settings = Adjust safety settings
        # See https://ai.google.dev/gemini-api/docs/safety-settings
        system_instruction=f"""
        당신은 대체 역사 시나리오 생성기입니다. 다음 두 역사적 인물 중 하나를 선택하여 그들의 삶에서 중요한 전환점이 될 수 있는 에피소드를 바탕으로 대체 역사 시나리오를 만들어주세요:
        1. 사도세자 (조선의 왕세자, 1735-1762)
        2. 스티브 잡스 (애플 공동 창업자, 1955-2011)

        선택한 인물에 대해 다음 정보를 고려하여 시나리오를 구성하세요:

        1. 역사적 배경: [인물이 살았던 시대와 사회적 상황]
        2. 주요 업적 또는 사건: [인물과 관련된 중요한 역사적 사건들]
        3. 성격 특성: [역사적 기록에 나타난 인물의 주요 성격 특성]
        4. 주요 갈등: [인물이 겪었던 주요 갈등이나 도전]

        예를 들어, 사도세자의 생애 중 임오화변 사건 직전의 시나리오나, 스티브 잡스의 애플 퇴출 직전의 상황에 대한 시나리오를 생성해보세요.

        첫 시나리오 생성의 choice_number는 "반드시" 0입니다.
        사용자는 총 {choice.choice_count}번의 선택을 할 것입니다. 각 선택마다 다음 JSON 형식으로 출력하세요:

        {{
        "choice_number": 현재 선택 번호,
        "story": "시나리오 설명 (200자 이내)",
        "opt1": ["선택지 1 제목", "선택지 1 설명 (70자 이내)"],
        "opt2": ["선택지 2 제목", "선택지 2 설명 (70자 이내)"]
        }}

        시나리오 설명은 다음 요소를 포함해야 합니다:
        1. 현재 역사적 상황에 대한 간략한 설명
        2. 인물이 직면한 주요 갈등이나 도전
        3. 결정을 내려야 하는 구체적인 상황
        4. 이 결정이 가져올 수 있는 잠재적 영향

        주의: {choice.choice_count}번째 선택이 끝나기 전까지는 최종 결과를 출력하지 마세요.

        {choice.choice_count}번째 선택 후에만 다음 형식의 JSON으로 최종 결과를 출력하세요:

        {{
        "choice_number": {choice.choice_count},
        "story": "최종 시나리오 설명 (200자 이내)",
        "opt1": ["", ""],
        "opt2": ["", ""],
        "final_scenario": "최종 상황 설명 (300자 이내)",
        "historical_changes": "대체 역사의 주요 변화와 결과 (200자 이내)",
        "comparison": "원래 역사와의 주요 차이점 (200자 이내)"
        }}

        최종 결과에서는 다음 사항을 반드시 포함해야 합니다:
        1. 선택에 따른 인물의 최종 운명
        2. 해당 인물의 선택이 역사에 미친 영향
        3. 실제 역사와 비교했을 때의 주요 차이점
        4. 가상의 대체 역사가 현대에 미칠 수 있는 영향

        각 선택지와 최종 결과는 인물의 성격과 역사적 맥락을 충실히 반영하여 현실감 있게 구성해주세요.
        """,
        )

    chat_session = model.start_chat()
    response = chat_session.send_message(f"{choice.character}의 초기 스토리 만들어줘")
    init_data = json.loads(response.text)
    return init_data

@app.post("/make_choice/{choice_number}", response_model=Union[StoryResponse, FinalResponse])
async def make_choice(opt: Opt, choice_number: int):
    global chat_session
    if not chat_session:
        raise HTTPException(status_code=400, detail="Story not started")
    
    response = chat_session.send_message(opt.opt_title)
    # print("Raw response:", response.text)

    try:
        story_data = json.loads(response.text)
    except json.JSONDecodeError as e:
        print(f"JSON decode error: {e}")
        # JSON 파싱 실패 시 응답 내용 전체를 story로 반환
        return StoryResponse(choice_number=choice_number, story=response.text, opt1=["Error", ""], opt2=["Error", ""])
    # story_data = json.loads(response.text)
    # print(story_data)
    if 'final_scenario' in story_data:
        return FinalResponse(**story_data)
    elif 'story' in story_data:
        return StoryResponse(**story_data)
    else:
        raise HTTPException(status_code=500, detail="Unexpected response format from AI")