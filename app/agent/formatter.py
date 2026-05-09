"""
Response formatter node.

Adds citations, confidence scores, and consistent structure to agent responses.
Also extracts source documents for frontend display.
"""

from app.agent.state import AgentState
from app.utils.confidence import estimate_confidence_score
from typing import Dict, Any, List
import re


async def formatter_node(state: AgentState) -> Dict[str, Any]:
    """
    Format the final response with citations and metadata.
    
    Takes the raw response from any agent and:
    1. Extracts source citations from context (if available)
    2. Calculates confidence score
    3. Adds consistent formatting
    4. Prepares sources list for frontend
    """
    print(f"[Formatter] Formatting response for {state['intent']} agent")
    
    response_text = state.get("response", "")
    context = state.get("context", [])
    intent = state.get("intent", "unknown")
    
    # Different formatting based on intent type
    if intent == "rag_qa":
        formatted_response, sources = format_qa_response(response_text, context)
        confidence = calculate_confidence_qa(response_text, context)
    elif intent == "quiz":
        formatted_response, sources = format_quiz_response(response_text)
        confidence = 0.95  # Quiz generation is deterministic
    elif intent == "summary":
        formatted_response, sources = format_summary_response(response_text, context)
        confidence = estimate_confidence_score(response_text, context)
    else:
        formatted_response = response_text
        sources = []
        confidence = 0.5
    
    # Add confidence badge and metadata
    confidence_indicator = get_confidence_indicator(confidence)
    final_response = f"{formatted_response}\n\n---\n*{confidence_indicator}*"
    
    return {
        "response": final_response,
        "evaluation": {
            "score": confidence,
            "intent": intent,
            "has_sources": len(sources) > 0
        }
    }


def format_qa_response(response: str, context: List[Dict]) -> tuple[str, List[Dict]]:
    """Format Q&A responses with source citations."""
    if not context:
        return response, []
    
    sources = []
    unique_sources = {}
    
    # Extract unique sources from context chunks
    for idx, chunk in enumerate(context[:5]):  # Limit to top 5 sources
        metadata = chunk.get("metadata", {})
        source_name = metadata.get("source", metadata.get("doc_id", f"Source {idx+1}"))
        
        if source_name not in unique_sources:
            unique_sources[source_name] = {
                "id": len(unique_sources) + 1,
                "name": source_name,
                "page": metadata.get("page", "N/A"),
                "relevance_score": chunk.get("score", 0.5)
            }
    
    # Build sources section
    sources_list = []
    for source in unique_sources.values():
        sources_list.append(f"[{source['id']}] {source['name']} (page {source['page']})")
        sources.append({
            "citation": source['id'],
            "filename": source['name'],
            "page": source['page']
        })
    
    # Add citations to response if they exist in brackets already
    # This is simple - assumes agent already added [1], [2] etc.
    if sources_list:
        response = response + "\n\n**Sources:**\n" + "\n".join(sources_list)
    
    return response, sources


def format_quiz_response(response: str) -> tuple[str, List]:
    """Format quiz responses with clear structure."""
    # Ensure quiz has clear question numbering
    lines = response.split('\n')
    formatted_lines = []
    question_count = 0
    
    for line in lines:
        # Detect question patterns (1., Q1., Question 1:, etc.)
        if re.match(r'^(\d+\.|Q\d+|Question\s+\d+)', line.strip(), re.IGNORECASE):
            question_count += 1
            formatted_lines.append(f"\n**Q{question_count}.** {line}")
        else:
            formatted_lines.append(line)
    
    # Add header if not present
    if "quiz" not in response.lower()[:100]:
        formatted_lines.insert(0, "## 📝 Generated Quiz\n")
    
    return '\n'.join(formatted_lines), []


def format_summary_response(response: str, context: List[Dict]) -> tuple[str, List]:
    """Format summary responses with topic headers."""
    sources = []
    if context:
        # Extract main source for summary attribution
        main_source = context[0].get("metadata", {}).get("source", "Uploaded notes")
        response = f"📚 **Summary based on:** {main_source}\n\n{response}"
        sources.append({"type": "summary_source", "source": main_source})
    
    return response, sources


def calculate_confidence_qa(response: str, context: List[Dict]) -> float:
    """Calculate confidence score for Q&A responses."""
    if not context:
        return 0.3  # Low confidence - no sources found
    
    # Average relevance score of top chunks
    avg_score = sum(chunk.get("score", 0.5) for chunk in context[:3]) / min(3, len(context))
    
    # Adjust based on response length and quality indicators
    response_indicators = 0.0
    if len(response) > 100:
        response_indicators += 0.1
    if "i cannot find" in response.lower() or "not in your notes" in response.lower():
        response_indicators -= 0.3
    if any(citation in response for citation in ["[1]", "[2]", "[3]"]):
        response_indicators += 0.1
    
    confidence = min(0.95, max(0.1, avg_score + response_indicators))
    return round(confidence, 2)


def get_confidence_indicator(confidence: float) -> str:
    """Return emoji/text indicator for confidence score."""
    if confidence >= 0.8:
        return f"✅ High confidence ({int(confidence*100)}%)"
    elif confidence >= 0.6:
        return f"📘 Medium confidence ({int(confidence*100)}%)"
    elif confidence >= 0.4:
        return f"⚠️ Low confidence ({int(confidence*100)}%) - verify with notes"
    else:
        return f"❓ Very low confidence - I couldn't find good matches in your notes"