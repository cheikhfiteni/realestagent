import base64

import httpx
from app.config import GPT_MODEL, CLAUDE_MODEL, CRITERIA, USE_CLAUDE, QUERY_CONFIG
from app.db.database import get_unevaluated_listings
from app.models.models import Listing
import json
from dotenv import load_dotenv
from pydantic import BaseModel

import anthropic
import openai

load_dotenv(override=True)

BATCH_SIZE = 5

PRICE_COST_BOUND = 1.25
BEDROOM_PREFERENCE_MULTIPLIER = 1.5
BATHROOM_PREFERENCE_MULTIPLIER = 1.5
class ResponseSchema(BaseModel):
    score: int
    reasoning_trace: str

SYSTEM_PROMPT = """
You are an expert real estate agent. You are given a listing and asked to evaluate it based on a set of hueristics. Evaluate the listing based on the following criteria: \n
{criteria} \n \n
The photos and description are provided below. Where the photos and description do not provide enough information, you should use your best judgement. Where 
the photos and description do not agree, defer to your interpretation of the photos, and make a special note in the trace. Do not make up information. Note anything 
that seems unusual or noteworthy about the listing, and especially something very good or bad beyond the explicit criteria. Pay particular attention to a floor plan
and room arrangement, and consider the affects of that with its surroundings if one is provided.
Listing Photos:
{listing_photos}
Listing Description:
{listing_description}
"""

ANTHROPIC_CLIENT = anthropic.Anthropic()
OPENAI_CLIENT = openai.OpenAI()

def _get_image_contents(image_urls: list[str]) -> list[str]:
    """Get base64 encoded images."""
    return [base64.standard_b64encode(httpx.get(url).content).decode("utf-8") for url in image_urls]

def _format_image_contents_anthropic(image_contents: list[str]) -> list[dict]:
    """Format image contents for Claude."""
    formatted_contents = []
    for i, content in enumerate(image_contents, 1):
        formatted_contents.extend([
            {
                "type": "text", 
                "text": f"Image {i}:"
            },
            {
                "type": "image",
                "source": {
                    "type": "base64",
                    "media_type": "image/jpeg",
                    "data": content
                }
            }
        ])
    formatted_contents.append({
        "type": "text",
        "text": """Please evaluate this listing based on the criteria. Output in JSON format with keys: 
        “reasoning_trace” (string), and “score” (int)."""
    })
    return formatted_contents

def _format_image_contents_openai(image_urls: list[str], detail: str = "auto") -> list[dict]:
    """Format image contents for OpenAI."""
    formatted_contents = []
    formatted_contents.append({
        "type": "text",
        "text": "Please evaluate this listing based on the criteria:"
    })
    for url in image_urls:
        formatted_contents.append({
            "type": "image_url",
            "image_url": {
                "url": url,
                "detail": detail
            }
        })
    return formatted_contents

def _evaluate_with_gpt4v(listing: Listing, criteria: str) -> tuple[int, str]:
    """Evaluate listing using GPT-4V."""
    try:
        image_urls = json.loads(listing.image_urls)
        if not image_urls:
            return 0, "No images available"

        formatted_contents = _format_image_contents_openai(image_urls)

        # Format system prompt with listing details
        prompt = SYSTEM_PROMPT.format(
            criteria=criteria,
            listing_photos="[Images provided in message]",
            listing_description=listing.description
        )

        completions = OPENAI_CLIENT.beta.chat.completions.parse(
            model=GPT_MODEL,
            messages= [
                {
                    "role": "system",
                    "content": prompt
                },
                {
                    "role": "user",
                    "content": formatted_contents
                }
            ],
            response_format=ResponseSchema
        )

        response = completions.choices[0].message.parsed
        print(response)

        return response.score, response.reasoning_trace

    except Exception as e:
        return 0, f"Error evaluating with GPT-4V: {str(e)}"

def _evaluate_with_claude(listing: Listing, criteria: str) -> tuple[int, str]:
    """Evaluate listing using Claude 3.5."""
    try:
        image_urls = json.loads(listing.image_urls)
        if not image_urls:
            return 0, "No images available"

        image_contents = _get_image_contents(image_urls)
        formatted_contents = _format_image_contents_anthropic(image_contents)

        response = ANTHROPIC_CLIENT.messages.create(
            model=CLAUDE_MODEL,
            max_tokens=4096,
            system=SYSTEM_PROMPT.format(
                criteria=criteria,
                listing_photos="[Images provided in message]",
                listing_description=listing.description
            ),
            messages=[{
                "role": "user",
                "content": formatted_contents
            }]
        )

        response_text = response.content[0].text
        response = ResponseSchema.model_validate_json(response_text)
        return response.score, response.reasoning_trace

    except Exception as e:
        return 0, f"Error evaluating with Claude: {str(e)}"

def evaluate_listing_aesthetics(listing: Listing) -> tuple[int, str]:
    """Evaluate listing aesthetics using configured model."""

    if CLAUDE_MODEL and USE_CLAUDE:
        return _evaluate_with_claude(listing, CRITERIA)
    elif GPT_MODEL:
        return _evaluate_with_gpt4v(listing, CRITERIA)
    else:
        return 0, "No evaluation model configured"

# something to experiment with later, right now we prefilter with the craiglist query.
# this would allow us to explicitly note "better than" realities in the main lisiting (price/sqft, extra rooms, etc.)
def evaluate_listing_hueristics(listing: Listing) -> tuple[int, str]:
    """Evaluate a single listing and return score and trace."""
    score = 0
    trace = []
    
    # Price evaluation
    if QUERY_CONFIG.target_price_bedroom:
        if listing.price < QUERY_CONFIG.target_price_bedroom:
            score += 10
            trace.append(f"Good price under ${QUERY_CONFIG.target_price_bedroom}")
        elif listing.price < QUERY_CONFIG.target_price_bedroom * PRICE_COST_BOUND:
            score += 5
            trace.append(f"Moderate price under ${QUERY_CONFIG.target_price_bedroom * PRICE_COST_BOUND}")
        
    # Square footage evaluation
    if QUERY_CONFIG.min_square_feet:
        if listing.square_footage > QUERY_CONFIG.min_square_feet * PRICE_COST_BOUND:
            score += 10
            trace.append(f"Good size at {listing.square_footage}sqft")
        elif listing.square_footage > QUERY_CONFIG.min_square_feet:
            score += 5
            trace.append(f"Moderate size at {listing.square_footage}sqft")
        
    # Bedrooms evaluation
    if QUERY_CONFIG.min_bedrooms:
        if listing.bedrooms >= QUERY_CONFIG.min_bedrooms:
            score += 5 + (listing.bedrooms - QUERY_CONFIG.min_bedrooms) * BEDROOM_PREFERENCE_MULTIPLIER
            trace.append(f"Good number of bedrooms: {listing.bedrooms}")
        elif listing.bedrooms == QUERY_CONFIG.min_bedrooms:
            score += 5
            trace.append(f"Moderate number of bedrooms: {listing.bedrooms}")
        
    # Bathrooms evaluation
    if QUERY_CONFIG.min_bathrooms:
        if listing.bathrooms >= QUERY_CONFIG.min_bathrooms:
            score += 5 + (listing.bathrooms - QUERY_CONFIG.min_bathrooms) * BATHROOM_PREFERENCE_MULTIPLIER
            trace.append(f"Good number of bathrooms: {listing.bathrooms}")
        elif listing.bathrooms == QUERY_CONFIG.min_bathrooms:
            score += 5
            trace.append(f"Moderate number of bathrooms: {listing.bathrooms}")

    return score, " | ".join(trace)

def evaluate_unevaluated_listings():
    """Evaluate listings that haven't been scored yet."""
    
    try:
        session, unevaluated_listings = get_unevaluated_listings()
        
        current_batch = []
        for listing in unevaluated_listings:
            hueristic_score, hueristic_trace = evaluate_listing_hueristics(listing)
            aesthetic_score, aesthetic_trace = evaluate_listing_aesthetics(listing)
            listing.score = hueristic_score + aesthetic_score
            listing.trace = hueristic_trace + " | " + aesthetic_trace
            current_batch.append(listing)

            print(f"Evaluated {listing.title} with score {listing.score}")
            print(listing.link)
            print(f"Trace: {listing.trace}")
            
            if len(current_batch) >= BATCH_SIZE:
                print(f"Committed batch of {len(current_batch)} evaluations")
                current_batch = []
                session.commit()

        # Commit any remaining
        if current_batch:
            session.commit()
            print(f"Committed final batch of {len(current_batch)} evaluations")
            
    finally:
        session.close()

if __name__ == "__main__":
    evaluate_unevaluated_listings()

