"""
Research Automation Script
Automates market and competitor research for client reports.

Usage:
    python research_automation.py --client "Acme Agency" --topics "SEO trends,competitor analysis"
    python research_automation.py --client "Acme Agency" --config client_config.json
"""

import argparse
import json
import os
import time
from datetime import datetime
from typing import Optional

import requests
from dotenv import load_dotenv

load_dotenv()

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

PERPLEXITY_API_KEY = os.getenv("PERPLEXITY_API_KEY", "")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "../reports")


# ---------------------------------------------------------------------------
# Perplexity AI research
# ---------------------------------------------------------------------------

def research_with_perplexity(query: str, recency: str = "month") -> str:
    """Use Perplexity AI to research a topic and return a summary."""
    if not PERPLEXITY_API_KEY:
        print(f"[WARNING] PERPLEXITY_API_KEY not set. Returning placeholder for: {query}")
        return f"[Placeholder research result for: {query}]\n\nSet PERPLEXITY_API_KEY in .env to enable live research."

    url = "https://api.perplexity.ai/chat/completions"
    headers = {
        "Authorization": f"Bearer {PERPLEXITY_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": "sonar-medium-online",
        "messages": [
            {
                "role": "system",
                "content": (
                    "You are a professional business researcher. "
                    "Provide structured, actionable research summaries with key data points, "
                    "trends, and insights. Always include sources."
                ),
            },
            {"role": "user", "content": query},
        ],
        "max_tokens": 1500,
        "search_recency_filter": recency,
    }

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=60)
        response.raise_for_status()
        result = response.json()
        return result["choices"][0]["message"]["content"]
    except requests.RequestException as exc:
        print(f"[ERROR] Perplexity API request failed: {exc}")
        return f"[ERROR] Research failed for query: {query}"


def research_with_openai(query: str) -> str:
    """Fallback: Use OpenAI GPT for research if Perplexity is unavailable."""
    if not OPENAI_API_KEY:
        return f"[Placeholder] OpenAI research for: {query}"

    try:
        import openai
        client = openai.OpenAI(api_key=OPENAI_API_KEY)
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": "You are a professional business researcher. Provide structured, data-driven research summaries.",
                },
                {"role": "user", "content": query},
            ],
            max_tokens=1500,
        )
        return response.choices[0].message.content
    except Exception as exc:
        print(f"[ERROR] OpenAI request failed: {exc}")
        return f"[ERROR] Research failed for query: {query}"


def research_topic(query: str) -> str:
    """Research a topic, using Perplexity first, falling back to OpenAI."""
    if PERPLEXITY_API_KEY:
        return research_with_perplexity(query)
    return research_with_openai(query)


# ---------------------------------------------------------------------------
# Report sections
# ---------------------------------------------------------------------------

RESEARCH_PROMPTS = {
    "industry_overview": (
        "Provide a comprehensive industry overview for {industry} in {year}. "
        "Include: market size, growth rate, key players, major trends, and opportunities for small agencies."
    ),
    "competitor_analysis": (
        "Research the top 5 competitors of {company} in {industry}. "
        "For each competitor include: services offered, pricing (if public), strengths, weaknesses, "
        "and opportunities for differentiation."
    ),
    "target_audience": (
        "Analyze the target audience for a {industry} company. "
        "Include: demographics, pain points, buying behavior, preferred channels, "
        "and decision-making process."
    ),
    "keyword_opportunities": (
        "Research the top keyword opportunities for a {industry} agency in {location}. "
        "Include: high-volume low-competition keywords, question-based keywords, "
        "and local SEO opportunities."
    ),
    "content_strategy": (
        "Develop a content strategy research brief for {company} in {industry}. "
        "Include: top performing content formats, trending topics, content gaps in the market, "
        "and recommended publishing frequency."
    ),
}


def generate_report_section(section: str, context: dict) -> str:
    """Generate a single section of a research report."""
    prompt_template = RESEARCH_PROMPTS.get(section, "Research {section} for {company}")
    prompt = prompt_template.format(
        company=context.get("company", "the company"),
        industry=context.get("industry", "marketing"),
        location=context.get("location", "United States"),
        year=datetime.now().year,
        section=section,
    )

    print(f"  [INFO] Researching: {section}...")
    result = research_topic(prompt)
    time.sleep(1)  # rate limiting
    return result


# ---------------------------------------------------------------------------
# Report assembly
# ---------------------------------------------------------------------------

def generate_full_report(
    client_name: str,
    company: str,
    industry: str,
    location: str,
    topics: list[str],
) -> str:
    """Generate a complete research report for a client."""
    context = {
        "company": company,
        "industry": industry,
        "location": location,
    }

    report_lines = [
        f"# Research Report: {company}",
        f"**Prepared for:** {client_name}",
        f"**Date:** {datetime.now().strftime('%B %d, %Y')}",
        f"**Industry:** {industry}",
        f"**Focus Area:** {', '.join(topics)}",
        "",
        "---",
        "",
        "## Executive Summary",
        "",
        f"This report provides comprehensive research on {company} and the {industry} landscape. "
        f"Key findings and actionable insights are highlighted throughout.",
        "",
        "---",
        "",
    ]

    for topic in topics:
        if topic in RESEARCH_PROMPTS:
            section_title = topic.replace("_", " ").title()
            report_lines.append(f"## {section_title}")
            report_lines.append("")
            content = generate_report_section(topic, context)
            report_lines.append(content)
            report_lines.append("")
            report_lines.append("---")
            report_lines.append("")

    report_lines += [
        "## Recommendations",
        "",
        f"Based on the research above, here are the top 5 recommendations for {client_name}:",
        "",
        "1. **[To be customized based on findings]**",
        "2. **[To be customized based on findings]**",
        "3. **[To be customized based on findings]**",
        "4. **[To be customized based on findings]**",
        "5. **[To be customized based on findings]**",
        "",
        "---",
        "",
        "*Report generated by Agency Research Automation System*",
    ]

    return "\n".join(report_lines)


def save_report(report: str, client_name: str, output_dir: str) -> str:
    """Save report to a markdown file."""
    os.makedirs(output_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_name = client_name.lower().replace(" ", "_").replace("/", "-")
    filename = f"{safe_name}_report_{timestamp}.md"
    filepath = os.path.join(output_dir, filename)

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(report)

    print(f"[OK] Report saved to {filepath}")
    return filepath


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Automate research report generation")
    parser.add_argument("--client", required=True, help="Client/agency name")
    parser.add_argument("--company", default="", help="Target company to research (default: same as client)")
    parser.add_argument("--industry", default="marketing", help="Industry focus")
    parser.add_argument("--location", default="United States", help="Geographic focus")
    parser.add_argument(
        "--topics",
        default="industry_overview,competitor_analysis,target_audience",
        help="Comma-separated research topics: " + ", ".join(RESEARCH_PROMPTS.keys()),
    )
    parser.add_argument("--output", default=OUTPUT_DIR, help="Output directory for reports")
    args = parser.parse_args()

    company = args.company or args.client
    topics = [t.strip() for t in args.topics.split(",")]

    print(f"[INFO] Generating research report for: {args.client}")
    print(f"[INFO] Topics: {', '.join(topics)}")

    report = generate_full_report(
        client_name=args.client,
        company=company,
        industry=args.industry,
        location=args.location,
        topics=topics,
    )

    output_path = save_report(report, args.client, args.output)
    print(f"[DONE] Report generation complete: {output_path}")


if __name__ == "__main__":
    main()
