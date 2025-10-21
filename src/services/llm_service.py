"""
LLM Service for Conversational Prompt Building

This service uses Gemini 2.5 Flash to:
- Analyze user input and extract structured data
- Auto-fill missing fields intelligently
- Guide conversational flow
"""

import json
import google.generativeai as genai
from typing import Dict, Any, List, Optional, Tuple
from src.utils.logger import get_logger
from src.utils.json_schema import (
    get_base_prompt_schema,
    get_missing_fields,
    compile_final_prompt
)

logger = get_logger(__name__)


class LLMService:
    """Service for LLM-powered prompt building using Gemini 2.5 Flash."""

    def __init__(self, api_key: str, model_name: str = "gemini-2.0-flash-exp"):
        """
        Initialize the LLM service.

        Args:
            api_key: Google AI API key
            model_name: Name of the Gemini model to use
        """
        self.api_key = api_key
        self.model_name = model_name
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(model_name)
        logger.info(f"LLM Service initialized with model: {model_name}")

    def analyze_input(
        self,
        user_message: str,
        conversation_history: List[Dict[str, str]],
        current_prompt: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Analyze user input and extract structured data to update the prompt.

        Args:
            user_message: The user's latest message
            conversation_history: Previous conversation messages
            current_prompt: Current state of the prompt JSON

        Returns:
            Dictionary of field updates {field_path: value}
        """
        try:
            # Build conversation context
            context = self._build_context(conversation_history)

            # Create analysis prompt
            analysis_prompt = f"""You are an AI assistant helping users create image generation prompts.

Current prompt state (JSON):
{json.dumps(current_prompt, indent=2)}

Conversation history:
{context}

User's latest message: "{user_message}"

IMPORTANT: Extract ONLY the information that the user EXPLICITLY mentioned in their message.
Do NOT infer, assume, or make up information that wasn't directly stated.
Be conservative - if the user didn't clearly specify something, don't extract it.

Analyze the user's message and extract any information that can fill fields in the JSON schema.
Output ONLY a valid JSON object mapping field paths to their values.

Use dot notation for nested fields, e.g., "prompt.elements.mood": "cozy"

For list fields (like color_palette, genre, techniques), output the value as a list.

Example:
- If user says "modern logo with blue colors" → extract: title (if mentioned), colors, style
- If user says "cozy feeling" → extract: mood only
- If user says "coffee shop" → extract: subject or title only

Output only the JSON object with EXPLICITLY mentioned fields, nothing else."""

            response = self.model.generate_content(
                analysis_prompt,
                generation_config={
                    "temperature": 0.7,
                    "max_output_tokens": 500,
                }
            )

            # Extract and parse response
            response_text = self._get_response_text(response)

            # Try to extract JSON from response
            updates = self._extract_json(response_text)

            logger.info(f"Extracted {len(updates)} field updates from user input")
            return updates

        except Exception as e:
            logger.error(f"Error analyzing input: {str(e)}")
            return {}

    def autofill_missing_fields(
        self,
        current_prompt: Dict[str, Any],
        user_intent: str = ""
    ) -> Dict[str, Any]:
        """
        Use LLM to intelligently fill missing fields based on existing data.

        Args:
            current_prompt: Current state of the prompt
            user_intent: Overall user intent/description (optional)

        Returns:
            Complete prompt with auto-filled fields
        """
        try:
            missing = get_missing_fields(current_prompt)

            if not missing:
                logger.info("No missing fields to autofill")
                return current_prompt

            autofill_prompt = f"""You are helping complete an image generation prompt.

Current partial prompt (JSON):
{json.dumps(current_prompt, indent=2)}

User's overall intent: {user_intent if user_intent else "Create a professional logo/image"}

Missing required fields: {', '.join(missing)}

Fill in ALL missing fields with reasonable, creative defaults based on the existing content.
Be consistent with the style and mood already specified.

Output ONLY the complete JSON object with all fields filled.
Do not add explanations, just the JSON."""

            response = self.model.generate_content(
                autofill_prompt,
                generation_config={
                    "temperature": 0.8,
                    "max_output_tokens": 1000,
                }
            )

            response_text = self._get_response_text(response)
            completed_prompt = self._extract_json(response_text)

            if completed_prompt:
                logger.info("Successfully auto-filled missing fields")
                return completed_prompt
            else:
                logger.warning("Failed to parse auto-filled prompt, returning original")
                return current_prompt

        except Exception as e:
            logger.error(f"Error auto-filling fields: {str(e)}")
            return current_prompt

    def generate_next_question(
        self,
        current_prompt: Dict[str, Any],
        conversation_history: List[Dict[str, str]]
    ) -> str:
        """
        Generate the next question to ask the user based on missing fields.

        Args:
            current_prompt: Current state of the prompt
            conversation_history: Previous conversation messages

        Returns:
            Next question to ask the user
        """
        try:
            missing = get_missing_fields(current_prompt)
            context = self._build_context(conversation_history)

            if not missing:
                return "Great! I have all the information I need. Would you like me to generate the image now, or would you like to refine anything?"

            question_prompt = f"""You are a friendly AI assistant helping users create image prompts through conversation.

Current prompt state:
{json.dumps(current_prompt, indent=2)}

Conversation so far:
{context}

Missing required fields: {', '.join(missing)}

Your task:
1. Choose ONE missing field that makes the most sense to ask about next
2. Generate a natural, friendly question to ask the user about that field
3. Keep it conversational and encouraging
4. Provide 2-3 specific examples to help guide them

Format: Ask the question naturally, then mention examples.

Example good questions:
- "What kind of mood or feeling should this convey? For example, it could be playful, elegant, bold, or minimalist."
- "Could you describe the environment or background? Like an outdoor scene, studio setting, abstract background, or something else?"
- "What art form works best for your vision? Such as digital illustration, photography, 3D render, or watercolor painting?"

Output only your question with examples, nothing else."""

            response = self.model.generate_content(
                question_prompt,
                generation_config={
                    "temperature": 0.9,
                    "max_output_tokens": 150,
                }
            )

            question = self._get_response_text(response).strip()
            logger.info(f"Generated next question for missing field")
            return question

        except Exception as e:
            logger.error(f"Error generating question: {str(e)}")
            # Fallback questions
            missing = get_missing_fields(current_prompt)
            if "title" in missing or "name" in missing:
                return "What would you like to name this project or logo?"
            elif "mood" in missing or "feeling" in missing:
                return "What kind of feeling or mood should this convey? (e.g., modern, playful, elegant, bold)"
            elif "color" in missing:
                return "What colors would you like to use? You can specify color names or hex codes."
            else:
                return "Can you tell me more about what you're envisioning?"

    def refine_prompt_text(
        self,
        current_prompt: Dict[str, Any],
        user_refinement: str
    ) -> str:
        """
        Refine the final text prompt based on user feedback.

        Args:
            current_prompt: Current prompt JSON
            user_refinement: User's refinement request

        Returns:
            Refined text prompt
        """
        try:
            base_text = compile_final_prompt(current_prompt)

            refine_prompt = f"""Current image generation prompt:
{base_text}

User wants to refine it: "{user_refinement}"

Generate an improved version of the prompt incorporating the user's feedback.
Keep it clear, descriptive, and optimized for image generation.

Output only the refined prompt text, nothing else."""

            response = self.model.generate_content(
                refine_prompt,
                generation_config={
                    "temperature": 0.8,
                    "max_output_tokens": 300,
                }
            )

            refined = self._get_response_text(response).strip()
            logger.info("Successfully refined prompt text")
            return refined

        except Exception as e:
            logger.error(f"Error refining prompt: {str(e)}")
            return compile_final_prompt(current_prompt)

    def _build_context(self, conversation_history: List[Dict[str, str]]) -> str:
        """Build conversation context string from history."""
        if not conversation_history:
            return "No previous conversation."

        context_parts = []
        for msg in conversation_history[-5:]:  # Last 5 messages
            role = msg.get("role", "user")
            content = msg.get("content", "")
            context_parts.append(f"{role.capitalize()}: {content}")

        return "\n".join(context_parts)

    def _get_response_text(self, response) -> str:
        """Safely extract text from Gemini response."""
        try:
            if hasattr(response, 'text'):
                return response.text
            elif hasattr(response, 'parts'):
                return ''.join(part.text for part in response.parts if hasattr(part, 'text'))
            elif isinstance(response, str):
                return response
            else:
                return str(response)
        except Exception as e:
            logger.error(f"Error extracting response text: {str(e)}")
            return ""

    def _extract_json(self, text: str) -> Dict[str, Any]:
        """Extract JSON from text that may contain markdown or other formatting."""
        try:
            # Try direct parse first
            return json.loads(text)
        except json.JSONDecodeError:
            # Try to find JSON in markdown code blocks
            if "```json" in text:
                start = text.find("```json") + 7
                end = text.find("```", start)
                json_text = text[start:end].strip()
                try:
                    return json.loads(json_text)
                except json.JSONDecodeError:
                    pass

            # Try to find any JSON object
            start = text.find("{")
            end = text.rfind("}") + 1
            if start >= 0 and end > start:
                try:
                    return json.loads(text[start:end])
                except json.JSONDecodeError:
                    pass

            logger.warning("Could not extract valid JSON from response")
            return {}
