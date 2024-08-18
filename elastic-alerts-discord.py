import time
import json

from os import environ
from datetime import datetime, timedelta, timezone
from elasticsearch import Elasticsearch
from discord_webhook import DiscordWebhook, DiscordEmbed

# Define the Elasticsearch URLs, username, and password

es_url = environ.get("ES_URL")
es_user = environ.get("ES_USER")
es_password = environ.get("ES_PASSWORD")

# Define the Discord webhook URL

discord_webhook_url = environ.get("DISCORD_WEBHOOK_URL")
icon_url = environ.get("ICON_URL")

# Check if any of the required environment variables are missing
if not es_url or not es_user or not es_password or not discord_webhook_url or not icon_url:
    print("Error: Missing required environment variables")
    exit(1)

# Connect to Elasticsearch
es = Elasticsearch(
    hosts=es_url, 
    basic_auth=(es_user, es_password), 
    verify_certs=False,
    ssl_show_warn=False
)

# Define the index you want to query
index_name = "alerts_index"


def process_alert(context):
    alert_content = {}

    # Process the alert context
    for key, value in context.items():
        if key.startswith("display_"):
            # Use the key without 'display_' as the new key in the dictionary
            new_key = key.replace('display_', '')
            alert_content[new_key] = value

    # Return the dictionary
    return alert_content

def send_to_discord(rule_name, rule_description, rule_url, alert_content):
    # Send the alert to Discord
    
    webhook = DiscordWebhook(discord_webhook_url)

    embed = DiscordEmbed(title=rule_name, description=rule_description, color="03b2f8")
    embed.set_author(name="New detection!", url=rule_url, icon_url=icon_url)

    embed.set_footer(text="Click on the title to check the details")
    embed.set_timestamp()

    for key, value in alert_content.items():
        embed.add_embed_field(name=key, value=value)

    webhook.add_embed(embed)

    response = webhook.execute()

# Function to fetch documents from the last 5 minutes
def fetch_documents(es, index_name):
    # Get the current time and the time 5 minutes ago
    now = datetime.now(timezone.utc)
    lookback_time = now - timedelta(minutes=5)

    # Create the query to get documents within the last 5 minutes
    query = {
        "query": {
            "range": {
                "@timestamp": {  # Assuming you have a timestamp field named '@timestamp'
                    "gte": lookback_time,
                    "lte": now
                }
            }
        }
    }

    # Fetch documents
    response = es.search(index=index_name, body=query)
    
    # Process and print the results

    documents = response['hits']['hits']
    if documents:
        print(f"Fetched {len(documents)} documents:")

        for doc in documents:
            alert = doc['_source']

        # Process the alert
        # every alerts having a display_ prefix will be processed

        context = json.loads(alert['context'])
        
        alert_content = process_alert(context)

        # Send to Discord
        
        send_to_discord(alert['rule_name'], alert['rule_description'], alert['rule_url'], alert_content)
        print("Alert sent to Discord")
    else:
        print("No alerts found")

if __name__ == "__main__":
    while True:
        try:
            fetch_documents(es, index_name)
        except Exception as e:
            print(f"An error occurred: {e}")

        # Wait for 5 minutes before running again
        time.sleep(300)
