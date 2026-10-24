import json
import pandas as pd
from ai_helper import ask_gemma

def rasha_parse_intent(user_note):
    """
    Takes raw user text, formats it for your ask_gemma function, 
    and converts the raw string response into a reliable Python dictionary.
    """
    structured_instructions = f"""
    You are a strict data-extraction engine for a travel spreadsheet app.
    Analyze this raw user note: "{user_note}"
    
    Find a real or highly realistic local venue that fits their request perfectly.
    You must respond ONLY with a single, raw JSON object. Do not include markdown wraps or backticks like ```json.
    
    Use this exact JSON format layout:
    {{
        "venue_name": "Name of the business",
        "price_tier": "Use exactly £, ££, or £££",
        "estimated_cost": 15,
        "opening_hours": "e.g., 12:00 PM - 11:00 PM",
        "street_address": "Full street address of the location",
        "latitude": 51.5074,
        "longitude": -0.1278
    }}
    """
    raw_ai_text = ask_gemma(structured_instructions)
    
    try:
        clean_text = raw_ai_text.strip().replace("```json", "").replace("```", "").strip()
        return json.loads(clean_text)
    except Exception:
        # Fallback shield to ensure the application never crashes
        return {
            "venue_name": "Selected Spot",
            "price_tier": "££",
            "estimated_cost": 25,
            "opening_hours": "12:00 PM - 10:00 PM",
            "street_address": "London, UK",
            "latitude": 51.5074,
            "longitude": -0.1278
        }

def your_add_and_sort_itinerary(current_df, ai_payload, time_input, raw_note):
    """
    Appends the parsed AI record into your core table layout matrix 
    and automatically re-sorts rows chronologically from morning to night.
    """
    new_row = {
        "Time Slot": time_input,
        "My Raw Note": raw_note,
        "Venue Name": ai_payload.get("venue_name"),
        "Price": ai_payload.get("price_tier"),
        "Cost (£)": ai_payload.get("estimated_cost"),
        "Hours": ai_payload.get("opening_hours"),
        "Address": ai_payload.get("street_address"),
        "latitude": ai_payload.get("latitude"),
        "longitude": ai_payload.get("longitude")
    }
    
    # Append the row
    updated_df = pd.concat([current_df, pd.DataFrame([new_row])], ignore_index=True)
    
    # Intelligent Timeline Sort: Convert strings like "07:00 PM" temporarily to sort them cleanly
    try:
        updated_df['sort_time'] = pd.to_datetime(updated_df['Time Slot'], format='%I:%M %p', errors='coerce')
        updated_df = updated_df.sort_values(by='sort_time').drop(columns=['sort_time'])
    except Exception:
        pass
        
    return updated_df.reset_index(drop=True)
