"""Google Gemini AI client implementation with full conversation and streaming support"""

import threading
from typing import Any, Dict, List, Optional

import google.generativeai as genai

from ..settings import settings
from .interface import AIClient


class GeminiClient(AIClient):
    """Google Gemini AI client with advanced conversation and streaming capabilities"""

    def __init__(self, api_key: str):
        self.api_key = api_key
        self._model: Optional[genai.GenerativeModel] = None
        self._error: Optional[str] = None
        self.model_name = "gemini-2.0-flash-exp"
        self._initialize()

    def _initialize(self):
        """Initialize the Gemini client"""
        try:
            genai.configure(api_key=self.api_key)
            self._model = genai.GenerativeModel(self.model_name)
        except Exception as e:
            self._error = f"Failed to initialize Gemini: {str(e)}"

    def is_available(self) -> bool:
        """Check if the Gemini client is available"""
        return self._model is not None and self._error is None

    def get_error(self) -> str:
        """Get initialization error"""
        return self._error or ""

    def get_model_name(self) -> str:
        """Get model identifier"""
        return self.model_name

    def get_display_name(self) -> str:
        """Get human-readable name"""
        return "Gemini 2.0 Flash"

    def _build_conversation_context(
        self, conversation_history: List[Dict[str, Any]], current_prompt: str
    ) -> str:
        """Build full conversation context for AI"""
        context_messages = []

        for msg in conversation_history:
            role = msg.get("role", "")
            content = msg.get("content", "")

            if role == "claude":
                context_messages.append(f"Claude: {content}")
            elif role == "assistant":
                model = msg.get("model", "AI")
                context_messages.append(f"{model}: {content}")
            elif role in ["user", "human"]:
                context_messages.append(f"Human: {content}")

        # Add current message
        context_messages.append(f"Claude: {current_prompt}")
        return "\n".join(context_messages)

    def _create_conversation_prompt(self, context_messages: str) -> str:
        """Create the full prompt for conversation mode"""
        ai_name = self.get_display_name()
        return f"""You are {ai_name}, participating in a live three-way conversation with Claude Code (an AI programming assistant) and a human developer. This is a real-time collaborative environment where all participants can see the conversation as it unfolds.

**Important Context:**
- You are {ai_name}, Claude is your AI peer, and there's a human developer observing/participating
- The human can interrupt at any time by pressing Esc to add their input
- This conversation is being streamed live to a text file that the human is watching
- All conversation history is preserved in JSON format for reference
- Treat this as a professional, collaborative technical discussion

**Conversation History:**
{context_messages}

**Your Response Guidelines:**
- Respond naturally as {ai_name} in this three-way collaboration
- Build on previous context and maintain conversation flow
- If the human user has interjected, acknowledge their input
- Feel free to ask questions or seek clarification from either Claude or the human
- Share your unique perspective and expertise
- Keep responses engaging and substantive

Please respond as {ai_name}, maintaining the collaborative tone and building on the conversation context:"""

    def _create_code_review_prompt(self, code: str, focus: str) -> str:
        """Create prompt for code review"""
        return f"""You are an expert software engineer providing a comprehensive code review. I need your detailed analysis of this code with a focus on {focus}.

**Code to Review:**
```
{code}
```

**Review Instructions:**
Please provide specific, actionable feedback organized by these categories:

1. **Potential Issues or Bugs:** Identify any logical errors, edge cases, or potential runtime failures
2. **Security Concerns:** Flag any security vulnerabilities, data exposure risks, or unsafe practices
3. **Performance Optimizations:** Suggest improvements for speed, memory usage, or scalability
4. **Best Practices:** Recommend adherence to coding standards, design patterns, and industry conventions
5. **Code Clarity and Maintainability:** Assess readability, documentation, and long-term maintainability

For each issue identified, please provide:
- Clear explanation of the problem
- Specific line references where applicable
- Concrete suggestions for improvement
- Example code snippets when helpful

Focus your analysis on the {focus} aspects, but don't hesitate to mention other critical issues you notice."""

    def _create_brainstorm_prompt(self, topic: str, context: str) -> str:
        """Create prompt for brainstorming"""
        context_section = (
            context
            if context
            else "No additional context provided - please ask clarifying questions if needed."
        )

        return f"""You are a creative problem-solving partner collaborating with Claude Code (an AI programming assistant) and a human developer. We need your innovative thinking and technical expertise.

**Brainstorming Topic:** {topic}

**Context & Background:**
{context_section}

**Your Role:**
You are an expert in software architecture, design patterns, and innovative problem-solving. Approach this brainstorming session as a senior engineer who thinks creatively about technical challenges.

**Brainstorming Instructions:**
1. **Understanding**: First, demonstrate that you understand the problem/topic by summarizing it in your own words
2. **Creative Ideas**: Generate 3-5 innovative approaches or solutions, ranging from conventional to unconventional
3. **Technical Considerations**: For each idea, briefly discuss:
   - Implementation complexity (Low/Medium/High)
   - Potential benefits and drawbacks
   - Technical requirements or dependencies
4. **Questions & Exploration**: Ask insightful questions that might lead to better solutions
5. **Recommendations**: Suggest which approach(es) you'd prioritize and why

**Output Style:**
- Be conversational and collaborative
- Think out loud - share your reasoning process
- Build on ideas progressively
- Don't be afraid to suggest bold or unconventional approaches
- Ask follow-up questions to deepen the discussion

Remember: This is a three-way collaboration between you, Claude, and the human developer. Feel free to address both of us and encourage continued discussion."""

    def generate_content(
        self, prompt: str, temperature: Optional[float] = None, stream: bool = False
    ) -> Any:
        """Generate content using Gemini model"""
        if not self.is_available():
            raise RuntimeError(f"Gemini not available: {self.get_error()}")

        if temperature is None:
            temperature = settings.default_temperature

        generation_config = genai.GenerationConfig(
            temperature=temperature,
            max_output_tokens=8192,
        )

        if not self._model:
            raise ValueError("Model not initialized")
        return self._model.generate_content(
            prompt, generation_config=generation_config, stream=stream
        )

    def call_simple(self, prompt: str, temperature: Optional[float] = None) -> str:
        """Simple Gemini call without conversation context"""
        try:
            response = self.generate_content(prompt, temperature)
            return response.text
        except Exception as e:
            return f"Error calling Gemini: {str(e)}"

    def call_with_conversation(
        self,
        prompt: str,
        conversation_history: List[Dict[str, Any]],
        temperature: Optional[float] = None,
    ) -> str:
        """Call Gemini with full conversation context"""
        try:
            # Build conversation context
            context_messages = self._build_conversation_context(
                conversation_history, prompt
            )
            full_prompt = self._create_conversation_prompt(context_messages)

            response = self.generate_content(full_prompt, temperature)
            return response.text

        except Exception as e:
            return f"Error calling Gemini: {str(e)}"

    def call_with_streaming(
        self,
        prompt: str,
        conversation_history: List[Dict[str, Any]],
        streaming_file: str,
        temperature: Optional[float] = None,
    ) -> str:
        """Call Gemini with streaming output to file"""
        try:
            # Build conversation context
            context_messages = self._build_conversation_context(
                conversation_history, prompt
            )
            full_prompt = self._create_conversation_prompt(context_messages)

            # Initialize streaming file
            with open(streaming_file, "a", encoding="utf-8") as f:
                f.write("LIVE CONVERSATION:\n\n")
                f.write(f"CLAUDE:\n{prompt}\n\n")
                f.write("GEMINI:\n")
                f.flush()

            # Generate with streaming
            response = self.generate_content(full_prompt, temperature, stream=True)

            # Collect streaming chunks
            full_response_text = ""
            with open(streaming_file, "a", encoding="utf-8") as f:
                for chunk in response:
                    if chunk.text:
                        f.write(chunk.text)
                        f.flush()
                        full_response_text += chunk.text

            # Signal completion
            with open(streaming_file, "a", encoding="utf-8") as f:
                f.write("\n\n--- RESPONSE COMPLETE ---\n")

            return full_response_text

        except Exception as e:
            # Write error to streaming file
            try:
                with open(streaming_file, "a", encoding="utf-8") as f:
                    f.write(f"\n\nERROR: {str(e)}\n")
            except Exception:
                pass
            return f"Error calling Gemini: {str(e)}"

    def review_code(self, code: str, focus: str = "general") -> str:
        """Perform code review with Gemini"""
        prompt = self._create_code_review_prompt(code, focus)
        return self.call_simple(prompt, self.get_recommended_temperature("code_review"))

    def brainstorm(self, topic: str, context: str = "") -> str:
        """Brainstorm with Gemini"""
        prompt = self._create_brainstorm_prompt(topic, context)
        return self.call_simple(prompt, self.get_recommended_temperature("brainstorm"))

    def process_in_background(
        self,
        prompt: str,
        conversation_history: List[Dict[str, Any]],
        streaming_file: str,
        temperature: Optional[float] = None,
    ) -> None:
        """Process Gemini call in background thread with streaming"""

        def background_task():
            self.call_with_streaming(
                prompt, conversation_history, streaming_file, temperature
            )

        thread = threading.Thread(target=background_task)
        thread.daemon = True
        thread.start()
