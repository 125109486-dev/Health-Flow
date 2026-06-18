def get_system_advice(status):
    if status == "Green":
        return {
            "message": "Low demand expected across the system.",
            "advice": [
                "GP services are appropriate for non-urgent issues.",
                "A&E likely to have normal waiting times.",
                "Urgent Care Centres available if needed."
            ]
        }

    elif status == "Amber":
        return {
            "message": "Moderate pressure on emergency services.",
            "advice": [
                "Expect some delays at A&E.",
                "Consider GP or GP out-of-hours for non-emergencies.",
                "Urgent Care Centres may be faster."
            ]
        }

    else:  # Red
        return {
            "message": "High pressure across emergency departments.",
            "advice": [
                "Long waiting times likely at A&E.",
                "Use GP or urgent care if condition is not urgent.",
                "Emergency symptoms still require A&E or emergency services."
            ]
        }

