from openai import OpenAI
import logging
from .config import client

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def evaluate_lead(user_header, user_comment):
    """
    Evaluate if a comment is from a potential lead using OpenAI's GPT.
    
    Args:
        user_header (str): The user's LinkedIn header/title
        user_comment (str): The user's comment content
    
    Returns:
        tuple: (decision, reason) where decision is "Lead" or "Not a Lead"
    """
    if not isinstance(user_header, str) or not isinstance(user_comment, str):
        return "Not a Lead", "Invalid input data"

    try:
        # Create the messages for the API
        messages = [
            {
                "role": "system",
                "content": """You are an expert real estate lead qualifier for a Dubai-based real estate company.
                Analyze the LinkedIn user's profile and comment to determine if they're a potential lead.
                Consider factors like:
                - Interest in real estate
                - Investment potential
                - Location relevance
                - Professional background
                Respond with exactly 'Lead' or 'Not a Lead', followed by '#' and a brief reason."""
            },
            {
                "role": "user",
                "content": f"User Header: {user_header}\nComment: {user_comment}"
            }
        ]

        # Call the OpenAI API
        response = client.chat.completions.create(
            model="gpt-4",  # or your preferred model
            messages=messages,
            max_tokens=100,
            temperature=0.3
        )

        # Parse the response
        result = response.choices[0].message.content.strip()
        
        # Split into decision and reason
        parts = result.split('#')
        is_lead = parts[0].strip()
        reason = parts[1].strip() if len(parts) > 1 else "No reason provided"

        return is_lead, reason

    except Exception as e:
        logger.error(f"Error in lead evaluation: {str(e)}")
        return "Not a Lead", f"Error in evaluation: {str(e)}"