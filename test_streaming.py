#!/usr/bin/env python3
"""
Test script to visualize streaming responses in real-time
"""
import requests
import json
import sys
import time

def test_streaming():
    url = "https://koozie-agent-service-127756525541.us-central1.run.app/chat"
    
    # Get message from command line or use default
    message = sys.argv[1] if len(sys.argv) > 1 else "Tell me about Koozie Group's product categories."
    
    payload = {"message": message}
    
    print("🚀 Starting streaming request...")
    print(f"📝 Question: {message}")
    print("\n" + "="*80)
    print("📡 STREAMING RESPONSE (tokens appear as they're generated):")
    print("="*80 + "\n")
    
    try:
        response = requests.post(
            url,
            json=payload,
            headers={"Content-Type": "application/json"},
            stream=True
        )
        
        response.raise_for_status()
        
        full_text = ""
        chunk_count = 0
        
        # Process Server-Sent Events
        for line in response.iter_lines():
            if line:
                line_str = line.decode('utf-8')
                if line_str.startswith('data: '):
                    data_str = line_str[6:]  # Remove 'data: ' prefix
                    try:
                        data = json.loads(data_str)
                        if 'text' in data:
                            chunk_text = data['text']
                            if chunk_text:  # Only print non-empty chunks
                                chunk_count += 1
                                full_text += chunk_text
                                # Print chunk immediately (no buffering)
                                print(chunk_text, end='', flush=True)
                                
                        if data.get('done', False):
                            break
                    except json.JSONDecodeError:
                        continue
        
        print("\n\n" + "="*80)
        print(f"✅ Stream completed! Received {chunk_count} chunks")
        print(f"📊 Total length: {len(full_text)} characters")
        print("="*80)
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    test_streaming()

