def format_event(event_key, event_dict):
    if event_key == "ALL":
        return "🌍 Global Overview (All Events)"
    return event_dict.get(event_key, str(event_key))