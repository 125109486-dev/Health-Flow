import pandas as pd

def apply_rule_engine(current, predicted):
    if current == 'Red' and predicted == 'Red':
        return 'URGENT REDIRECT', 'Trigger concierge alerts — surface nearest MIU and GP'
    if current == 'Amber' and predicted == 'Red':
        return 'EARLY WARNING', 'Notify concierge users now before status worsens'
    if current == 'Red' and predicted in ['Amber', 'Green']:
        return 'IMPROVING', 'Send concierge notifications that wait is dropping'
    if current == 'Amber' and predicted == 'Amber':
        return 'MONITOR', 'Flag for next 30-minute refresh cycle'
    if current == 'Green':
        return 'NO ACTION', 'Operating within normal capacity'
    return 'MONITOR', 'Insufficient data for full prediction'

def get_patient_pathway(status, waiting_24):
    if status == 'Red' and waiting_24 > 5:
        return 'Route to MIU or GP — A&E critically overcrowded'
    if status == 'Red':
        return 'Consider MIU if condition allows — A&E very busy'
    if status == 'Amber':
        return 'Check MIU availability — A&E busy'
    return 'A&E available — normal wait expected'

def run_prescriptive(df):
    df = df.copy()

    if 'predicted_traffic_light' not in df.columns:
        df['predicted_traffic_light'] = df['traffic_light_status']

    results = []
    for _, row in df.iterrows():
        action, detail = apply_rule_engine(
            row.get('traffic_light_status', 'Unknown'),
            row.get('predicted_traffic_light', 'Unknown')
        )
        pathway = get_patient_pathway(
            row.get('traffic_light_status', 'Unknown'),
            row.get('waiting_over_24hrs', 0)
        )
        results.append({
            'Hospital':       row.get('Hospital', row.get('hospital', '')),
            'Current Status': row.get('traffic_light_status', 'Unknown'),
            'Predicted':      row.get('predicted_traffic_light', 'Unknown'),
            'System Action':  action,
            'Action Detail':  detail,
            'Patient Pathway': pathway,
        })

    return pd.DataFrame(results)
