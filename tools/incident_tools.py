import pandas as pd

def search_similar_incidents(task_id, error_summary):
    try:
        df = pd.read_csv("data/incidents.csv")
        matched = df[df['description'].str.contains(task_id, case=False, na=False)]

        if matched.empty:
            matched = df[df['description'].str.contains(error_summary[:50], case=False, na=False)]

        if matched.empty:
            return f"No similar incidents found for task {task_id}."

        incidents = []
        for _, row in matched.iterrows():
            incidents.append(f"Date: {row['date']}, Summary: {row['description']}")

        return "\n".join(incidents)

    except Exception as e:
        return f"Incident lookup failed: {str(e)}"
