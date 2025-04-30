from telethon import TelegramClient, events
from telethon.tl.types import Channel
import re
import os
import asyncio
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Telegram API credentials
API_ID = int(os.getenv('API_ID'))
API_HASH = os.getenv('API_HASH')
PHONE_NUMBER = os.getenv('PHONE_NUMBER')

# Channel IDs/usernames
SOURCE_CHANNEL = os.getenv('SOURCE_CHANNEL')  # Channel you want to monitor
DESTINATION_CHANNEL = os.getenv('DESTINATION_CHANNEL')  # Your own channel

# Create the client
client = TelegramClient('job_forwarder', API_ID, API_HASH)

@client.on(events.NewMessage(chats=SOURCE_CHANNEL))
async def handler(event):
    message = event.message
    message_text = message.text or message.message
    
    if message_text:
        # Check if this looks like a job posting (contains words like "hiring", "job", "apply", etc.)
        job_indicators = ["hiring", "job", "apply", "position", "vacancy", "remote", "location", "career"]
        is_job_post = any(indicator.lower() in message_text.lower() for indicator in job_indicators)
        
        if is_job_post:
            # Define patterns to identify unwanted links
            unwanted_patterns = [
                r'(https?://(www\.)?(whatsapp|wa\.me|t\.me|telegram)\.[\w/.]+)',  # WhatsApp and Telegram links
                r'(👉.*?)(https?://\S+)',  # Links after emoji pointers
                r'(channel|group|community|follow).*?(https?://\S+)',  # Links described as channels/groups
                r'(join|subscribe).*?(https?://\S+)'  # Join/subscribe links
            ]
            
            # Keep track of lines to remove
            lines_to_remove = []
            
            # Process message line by line
            lines = message_text.split('\n')
            filtered_lines = []
            
            for line in lines:
                should_remove = False
                
                # Check if line contains unwanted links
                for pattern in unwanted_patterns:
                    if re.search(pattern, line, re.IGNORECASE):
                        should_remove = True
                        break
                
                # Check if line is an instruction to join/follow
                if any(phrase in line.lower() for phrase in ["join our", "follow us", "subscribe to", "join the", "join now"]):
                    should_remove = True
                
                if not should_remove:
                    filtered_lines.append(line)
            
            # Reconstruct the filtered message
            filtered_message = '\n'.join(filtered_lines)
            
            # Final cleanup - remove extra newlines
            filtered_message = re.sub(r'\n\s*\n\s*\n+', '\n\n', filtered_message)
            
            # Only forward if there's meaningful content left
            if len(filtered_message.strip()) > 10:  # Arbitrary minimum length
                try:
                    await client.send_message(DESTINATION_CHANNEL, filtered_message)
                    print(f"Forwarded job posting: {filtered_message[:50]}...")
                except Exception as e:
                    print(f"Error forwarding message: {str(e)}")
            else:
                print("Filtered message too short, not forwarding")

async def main():
    print("Starting the job forwarding automation...")
    
    # Connect to Telegram
    await client.start(phone=PHONE_NUMBER)
    print("Connected to Telegram!")
    
    # Get information about the source channel
    try:
        source_entity = await client.get_entity(SOURCE_CHANNEL)
        print(f"Successfully connected to source channel: {source_entity.title if hasattr(source_entity, 'title') else SOURCE_CHANNEL}")
    except Exception as e:
        print(f"Error accessing source channel: {str(e)}")
        return
    
    # Get information about the destination channel
    try:
        dest_entity = await client.get_entity(DESTINATION_CHANNEL)
        print(f"Successfully connected to destination channel: {dest_entity.title if hasattr(dest_entity, 'title') else DESTINATION_CHANNEL}")
    except Exception as e:
        print(f"Error accessing destination channel: {str(e)}")
        return
    
    print("Bot is now running! Press Ctrl+C to stop.")
    
    # Run the client until disconnected
    await client.run_until_disconnected()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Bot stopped by user")
    except Exception as e:
        print(f"Unexpected error: {str(e)}")
