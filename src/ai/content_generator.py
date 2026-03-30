"""
AI Content Generator Module
Generates personalized outreach email content using AI
Owner: Md Jamil Islam
"""
import logging
from typing import Optional, Dict

logger = logging.getLogger(__name__)


class ContentGenerator:
    """
    Uses OpenAI/Gemini to generate personalized email content for leads.
    """

    SYSTEM_PROMPT = """You are an expert digital marketing agency copywriter.
Write compelling, personalized cold outreach emails that:
- Are concise (under 150 words)
- Focus on the prospect's specific pain point
- Offer one clear value proposition
- Have a single, simple call to action
- Sound human and conversational, not salesy
- Are in English unless instructed otherwise
"""

    def __init__(self, openai_key: str = "", gemini_key: str = ""):
        self.openai_key = openai_key
        self.gemini_key = gemini_key
        self._openai_client = None
        self._gemini_model = None

        if openai_key:
            try:
                from openai import OpenAI
                self._openai_client = OpenAI(api_key=openai_key)
            except ImportError:
                logger.warning("OpenAI package not installed.")

        if gemini_key and not self._openai_client:
            try:
                import google.generativeai as genai
                genai.configure(api_key=gemini_key)
                self._gemini_model = genai.GenerativeModel("gemini-pro")
            except ImportError:
                logger.warning("Google Generative AI package not installed.")

    def generate_outreach_email(
        self,
        business_name: str,
        niche: str,
        location: str,
        pain_point: str = "no website",
        sender_name: str = "Md Jamil Islam"
    ) -> Dict[str, str]:
        """Generate a personalized outreach email."""
        prompt = f"""Write a cold outreach email for:
- Business: {business_name}
- Industry: {niche}
- Location: {location}
- Pain point: {pain_point}
- Sender: {sender_name} (digital marketing agency owner)

Return a JSON with keys: "subject", "body"
"""
        if self._openai_client:
            return self._generate_with_openai(prompt)
        elif self._gemini_model:
            return self._generate_with_gemini(prompt)
        else:
            return self._generate_template(business_name, niche, location, sender_name)

    def _generate_with_openai(self, prompt: str) -> Dict[str, str]:
        """Generate content using OpenAI."""
        import json
        try:
            response = self._openai_client.chat.completions.create(
                model="gpt-4-turbo-preview",
                messages=[
                    {"role": "system", "content": self.SYSTEM_PROMPT},
                    {"role": "user", "content": prompt},
                ],
                max_tokens=500,
                temperature=0.7,
                response_format={"type": "json_object"},
            )
            content = response.choices[0].message.content
            return json.loads(content)
        except Exception as e:
            logger.error(f"OpenAI generation failed: {e}")
            return {"subject": "", "body": ""}

    def _generate_with_gemini(self, prompt: str) -> Dict[str, str]:
        """Generate content using Google Gemini."""
        import json
        try:
            full_prompt = self.SYSTEM_PROMPT + "\n\n" + prompt + "\nReturn JSON only."
            response = self._gemini_model.generate_content(full_prompt)
            text = response.text.strip()
            # Extract JSON from response
            if "```json" in text:
                text = text.split("```json")[1].split("```")[0].strip()
            return json.loads(text)
        except Exception as e:
            logger.error(f"Gemini generation failed: {e}")
            return {"subject": "", "body": ""}

    def _generate_template(
        self,
        business_name: str,
        niche: str,
        location: str,
        sender_name: str
    ) -> Dict[str, str]:
        """Fallback template-based generation."""
        return {
            "subject": f"Quick question about {business_name}'s online presence",
            "body": f"""Hi {business_name} team,

I noticed your {niche} business in {location} and wanted to reach out.

Many {niche} businesses in {location} are missing out on new customers simply because they don't have a strong online presence. I help businesses like yours get more customers through professional websites and digital marketing.

Would you be open to a quick 15-minute call to discuss how I can help {business_name} get more customers?

Best regards,
{sender_name}
Digital Marketing Agency"""
        }

    def generate_follow_up(self, step: int, business_name: str, sender_name: str) -> Dict[str, str]:
        """Generate follow-up email content."""
        templates = [
            {
                "subject": f"Re: Quick question about {business_name}'s online presence",
                "body": f"Hi again,\n\nJust wanted to bump this up in case it got buried. Did you get a chance to see my previous email?\n\nI'd love to share how I helped a similar {business_name}-type business get 3x more customers in 60 days.\n\nBest,\n{sender_name}"
            },
            {
                "subject": f"Free website audit for {business_name}",
                "body": f"Hi,\n\nI did a quick audit of your online presence and found a few easy wins that could bring {business_name} significantly more customers.\n\nWould you like me to share the audit? No charge, no obligation.\n\nBest,\n{sender_name}"
            },
            {
                "subject": f"Last follow-up — {business_name}",
                "body": f"Hi,\n\nI don't want to keep bothering you, so this will be my last email.\n\nIf you ever want to grow {business_name}'s online presence, I'm here to help.\n\nAll the best,\n{sender_name}"
            },
        ]
        return templates[min(step, len(templates) - 1)]
