import streamlit as st
import time
from config import client

# Function to integrate LLM like GPT
def evaluate_lead(post_content, user_header, user_comment):
    if not isinstance(user_header, str) or not isinstance(user_comment, str):
        return "Not a Lead", "Invalid user information"

    all_messages = list()

    # Create system prompt
    system_prompt = f"""
    You are an intelligent assistant that helps evaluate LinkedIn's potential leads for a Dubai-based real estate company.
    I will provide you with the content of the LinkedIn post which will be about real estate and the commenters' user information.
    When provided with a user's information and the post's content, determine if they are a lead or not.
    You MUST respond with 'Lead' or 'Not a Lead', followed by a '#' and a concise reason for your decision.
    """

    all_messages.append({"role": "system", "content": system_prompt})

    # Get user input
    user_prompt = f"Post Content: {post_content}\nUser Information\nUser Header: {user_header}\nUser Comment: {user_comment}"
    all_messages.append({"role": "user", "content": user_prompt})

    try:
        # Call the API
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=all_messages,
            max_tokens=200,
        )

        # Extract the response
        result = response.choices[0].message.content
        is_lead = result.split('#')[0].strip()
        reason = result.split('#')[1].strip() if '#' in result else "No reason provided"

    except Exception as api_exception:
        return "Not a Lead", f"API call failed: {api_exception}"

    return is_lead, reason



# # Example user info
# post_content = """#Dubai is a popular destination for #investment due to its strong economy, diverse industries, and business-friendly environment. 
# #Dubai Creek Harbour: This district is located on the north bank of Dubai Creek and is designed to be the city's new downtown. It features a mix of residential, commercial, and retail spaces.
# #Dubai Hills Estate: This is a master-planned community that offers a wide range of properties, including villas, townhouses, and apartments. It is known for its lush greenery, parks, and recreational facilities.
# Dubai knocks every other global city off the podium for international real estate investors. The latest bulk of international real estate investors is from China, the UK, Canada, and India. 
# Vartur Real Estate's sincerity has been verified by our customers. We see our customers as friends and family members. For years, our only aim is to meet our customers with their dream house, lifestyle, and the right property they deserve. This is the secret of our success."""
# user_header = "Real Estate Agent @Vartur Dubai | International Relations"
# user_comment = "interested in purchasing luxury real estate in Dubai, has a budget of 5 million AED."
# is_lead, reason = evaluate_lead(post_content, user_header, user_comment)
# print(is_lead)
# print(reason)