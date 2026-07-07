import os
import json
import uvicorn
from fastapi import FastAPI, Request
from pydantic import BaseModel, ValidationError
from typing import Literal
import google.generativeai as genai
import dotenv

from mcp.server import Server, NotificationOptions
from mcp.server.models import InitializationOptions
import mcp.types as types
from mcp.server.sse import SseServerTransport

# Load environment variables
dotenv.load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    print("Warning: GEMINI_API_KEY is not set.")
else:
    genai.configure(api_key=api_key)

# Initialize FastAPI App
app = FastAPI(title="SecureLearnAgent MCP Server")

# Initialize MCP Server
server = Server("securelearn-mcp")

# Pydantic Schemas for Validation
class TopicResourcesInput(BaseModel):
    topic: str
    difficulty_level: Literal["beginner", "intermediate", "advanced"]

class GenerateQuizInput(BaseModel):
    topic: str
    num_questions: int

@server.list_tools()
async def handle_list_tools() -> list[types.Tool]:
    return [
        types.Tool(
            name="get_topic_resources",
            description="Returns curated learning resources for a cybersecurity topic",
            inputSchema={
                "type": "object",
                "properties": {
                    "topic": {
                        "type": "string",
                        "description": "Cybersecurity topic (max 100 characters)"
                    },
                    "difficulty_level": {
                        "type": "string",
                        "enum": ["beginner", "intermediate", "advanced"],
                        "description": "Difficulty level"
                    }
                },
                "required": ["topic", "difficulty_level"]
            }
        ),
        types.Tool(
            name="generate_quiz",
            description="Generates quiz questions on the given topic",
            inputSchema={
                "type": "object",
                "properties": {
                    "topic": {
                        "type": "string",
                        "description": "Cybersecurity topic (max 100 characters)"
                    },
                    "num_questions": {
                        "type": "integer",
                        "description": "Number of questions to generate (1-10)"
                    }
                },
                "required": ["topic", "num_questions"]
            }
        )
    ]

@server.call_tool()
async def handle_call_tool(name: str, arguments: dict | None) -> list[types.TextContent]:
    if arguments is None:
        arguments = {}

    model = genai.GenerativeModel('gemini-1.5-pro')

    if name == "get_topic_resources":
        # Input Validation
        try:
            input_data = TopicResourcesInput(**arguments)
            if not input_data.topic.strip() or len(input_data.topic) > 100:
                raise ValueError("topic must be a non-empty string under 100 characters")
        except (ValidationError, ValueError) as e:
            return [types.TextContent(type="text", text=json.dumps({"error": f"Input validation error: {e}"}))]

        prompt = f'''
        You are an expert Cybersecurity Education AI.
        Generate learning resources for the cybersecurity topic: "{input_data.topic}" at the "{input_data.difficulty_level}" level.
        Return ONLY a raw JSON object (without markdown wrappers like ```json) with this exact structure:
        {{
            "description": "Brief description of the topic",
            "key_concepts": ["concept1", "concept2"],
            "practice_platforms": ["platform1", "platform2"],
            "recommended_order": ["step1", "step2"]
        }}
        '''
        response = model.generate_content(prompt)
        text = response.text.strip()
        if text.startswith("```json"):
            text = text[7:-3].strip()
        elif text.startswith("```"):
            text = text[3:-3].strip()
            
        try:
            parsed = json.loads(text)
            return [types.TextContent(type="text", text=json.dumps(parsed, indent=2))]
        except Exception:
            return [types.TextContent(type="text", text=json.dumps({"error": "Failed to generate valid JSON", "raw_output": text}))]

    elif name == "generate_quiz":
        # Input Validation
        try:
            input_data = GenerateQuizInput(**arguments)
            if not input_data.topic.strip() or len(input_data.topic) > 100:
                raise ValueError("topic must be a non-empty string under 100 characters")
            if input_data.num_questions < 1 or input_data.num_questions > 10:
                raise ValueError("num_questions must be between 1 and 10")
        except (ValidationError, ValueError) as e:
            return [types.TextContent(type="text", text=json.dumps({"error": f"Input validation error: {e}"}))]

        prompt = f'''
        You are a Cybersecurity Instructor.
        Generate a multiple choice quiz about "{input_data.topic}" with exactly {input_data.num_questions} questions.
        Return ONLY a raw JSON object (without markdown wrappers like ```json) with this exact structure:
        {{
            "questions": [
                {{
                    "question": "Question text",
                    "options": {{
                        "A": "Option A text",
                        "B": "Option B text",
                        "C": "Option C text",
                        "D": "Option D text"
                    }},
                    "correct_answer": "A",
                    "explanation": "Why this option is correct"
                }}
            ]
        }}
        '''
        response = model.generate_content(prompt)
        text = response.text.strip()
        if text.startswith("```json"):
            text = text[7:-3].strip()
        elif text.startswith("```"):
            text = text[3:-3].strip()

        try:
            parsed = json.loads(text)
            return [types.TextContent(type="text", text=json.dumps(parsed, indent=2))]
        except Exception:
            return [types.TextContent(type="text", text=json.dumps({"error": "Failed to generate valid JSON", "raw_output": text}))]

    else:
        return [types.TextContent(type="text", text=json.dumps({"error": f"Unknown tool: {name}"}))]

# Set up SSE Transport endpoint (clients will POST messages to /messages)
sse = SseServerTransport("/messages")

@app.get("/sse")
async def handle_sse(request: Request):
    async with sse.connect_sse(request.scope, request.receive, request._send) as streams:
        await server.run(streams[0], streams[1], InitializationOptions(
            server_name="securelearn-mcp",
            server_version="1.0.0",
            capabilities=server.get_capabilities(
                notification_options=NotificationOptions(),
                experimental_capabilities={},
            ),
        ))

@app.post("/messages")
async def handle_messages(request: Request):
    await sse.handle_post_message(request.scope, request.receive, request._send)

if __name__ == "__main__":
    print("Starting SecureLearn MCP Server on http://localhost:8080")
    print("SSE Endpoint: http://localhost:8080/sse")
    uvicorn.run("mcp_server:app", host="0.0.0.0", port=8080, reload=True)
