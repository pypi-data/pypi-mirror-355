"""CLI uploader – users run:  python -m cli_tool.cli_tool ..."""
import argparse, hashlib, os, json, requests, sys, mimetypes
from datetime import datetime, timezone

# -------- helpers ---------

def warn_if_large(path: str, limit_mb: int = 200):
    size_mb = os.path.getsize(path) / 1_048_576
    if size_mb > limit_mb:
        print(f"⚠️  File is {size_mb:.1f} MB (> {limit_mb} MB). It will be split server-side.")
    else:
        print(f"📄 File size: {size_mb:.1f} MB (limit: {limit_mb} MB)")

def validate_input_format(lines: list, endpoint: str = None):
    """Check if input is in proper batch request format or API request format"""
    if not lines:
        print("❌ Empty input file")
        return False
        
    # Handle both string lines and pre-parsed objects
    if isinstance(lines[0], str):
        first_line = json.loads(lines[0])
    else:
        first_line = lines[0]
    
    # Check if it's batch request format (preferred - contains endpoint in URL)
    if all(key in first_line for key in ["custom_id", "method", "url", "body"]):
        detected_url = first_line.get("url", "")
        print(f"✅ Detected batch request format ({len(lines)} requests)")
        print(f"🎯 Endpoint detected from URL field: {detected_url}")
        
        if endpoint and detected_url != endpoint:
            print(f"⚠️  Note: Batch URL '{detected_url}' differs from manual endpoint '{endpoint}'")
            print("   The batch URL will take precedence")
        return True
    
    # For non-batch format, validate based on endpoint or use auto-detection
    if endpoint:
        # Manual endpoint specified - validate format
        if endpoint == "/v1/chat/completions":
            if any(key in first_line for key in ["model", "messages"]):
                print(f"✅ Detected chat completion format ({len(lines)} requests)")
                print("💡 Server will convert to batch request format automatically")
                return True
        elif endpoint == "/v1/completions":
            if any(key in first_line for key in ["model", "prompt"]):
                print(f"✅ Detected text completion format ({len(lines)} requests)")
                print("💡 Server will convert to batch request format automatically")
                return True
        elif endpoint == "/v1/embeddings":
            if any(key in first_line for key in ["model", "input"]):
                print(f"✅ Detected embedding format ({len(lines)} requests)")
                print("💡 Server will convert to batch request format automatically")
                return True
        elif endpoint == "/v1/responses":
            if any(key in first_line for key in ["model", "input"]) and "input" in first_line:
                print(f"✅ Detected response format ({len(lines)} requests)")
                print("💡 Server will convert to batch request format automatically")
                return True
        
        print(f"❌ Invalid format for endpoint {endpoint}. Expected either:")
        print("   1. Batch request format: {\"custom_id\": \"...\", \"method\": \"POST\", \"url\": \"...\", \"body\": {...}}")
        print(f"   2. Direct API format for {endpoint}")
        return False
    else:
        # Auto-detection mode (recommended)
        if any(key in first_line for key in ["model", "messages", "prompt", "input"]):
            print(f"✅ Detected API request format ({len(lines)} requests)")
            print("🎯 Server will auto-detect endpoint from request structure")
            
            # Give a hint about what was detected
            if "messages" in first_line:
                print("   Likely: Chat Completions API")
            elif "input" in first_line and isinstance(first_line.get("input"), list):
                # Check if it looks like responses API
                input_data = first_line["input"]
                if any(isinstance(item, dict) and "role" in item for item in input_data):
                    print("   Likely: Responses API")
                else:
                    print("   Likely: Embeddings API")
            elif "prompt" in first_line:
                print("   Likely: Text Completions API")
            elif "input" in first_line:
                print("   Likely: Embeddings API")
                
            return True
        else:
            print("❌ Invalid format. Expected either:")
            print("   1. Batch request format: {\"custom_id\": \"...\", \"method\": \"POST\", \"url\": \"...\", \"body\": {...}}")
            print("   2. API request format with fields like 'model', 'messages', 'prompt', or 'input'")
            return False

# -------- main ---------

def main():
    ap = argparse.ArgumentParser(description="Submit OpenAI batch job to central server")
    
    # Check for list-endpoints first to avoid requiring other arguments
    if "--list-endpoints" in sys.argv:
        print("📋 Supported OpenAI Batch Endpoints:")
        print("  /v1/chat/completions: Chat completions (text generation with conversation context)")
        print("  /v1/embeddings: Text embeddings (vector representations of text)")
        print("  /v1/completions: Text completions (simple text generation)")
        print("  /v1/responses: AI assistant responses (beta feature)")
        print("\n🎯 Detection Rules:")
        print("  • Batch format: URL field is used directly (most reliable)")
        print("  • Non-batch format: Auto-detected from request structure")
        print("    - messages field → /v1/chat/completions")
        print("    - input field with roles → /v1/responses")
        print("    - input field without roles → /v1/embeddings")
        print("    - prompt field → /v1/completions")
        print("\n💡 Recommendation: Use batch format with explicit URL field for best reliability")
        return
    
    ap.add_argument("--project-id", required=True, help="Your OpenAI project ID (e.g., proj_xxxxxxxxx)")
    ap.add_argument("--input", required=True, help="JSONL file to send")
    ap.add_argument("--server", required=True, help="Server root URL, e.g. http://165.132.142.28:9551")
    ap.add_argument("--tag", default="", help="Optional label visible in dashboard")
    ap.add_argument("--endpoint", default=None, 
                   choices=["/v1/chat/completions", "/v1/completions", "/v1/embeddings", "/v1/responses"],
                   help="OpenAI API endpoint (default: auto-detect from URL field in batch format or request structure)")
    ap.add_argument("--list-endpoints", action="store_true", help="List supported endpoints and exit")
    args = ap.parse_args()

    if not os.path.isfile(args.input):
        sys.exit("⛔ input file not found")

    warn_if_large(args.input)

    # Validate project ID format
    if not args.project_id.startswith("proj_"):
        print("⚠️  Warning: Project ID should start with 'proj_'")

    # Read messages but keep file raw too (server may stream‑upload)
    with open(args.input, "r", encoding="utf8") as f:
        lines = f.readlines()
    messages = [json.loads(l) for l in lines]

    if not validate_input_format(messages, args.endpoint):
        sys.exit("❌ Invalid input format")

    payload = {
        "project_id": args.project_id,
        "messages": messages,
        "tag": args.tag,
        "submitted_at": datetime.now(timezone.utc).isoformat(),
    }
    
    # Only include endpoint if manually specified
    if args.endpoint:
        payload["endpoint"] = args.endpoint

    r = requests.post(f"{args.server}/submit_batch", json=payload, timeout=300)
    r.raise_for_status()
    result = r.json()
    print("✅ submitted!", json.dumps(result, indent=2))
    
    # Show helpful info
    if "project_name" in result:
        print(f"\n📋 Project: {result['project_name']}")
    print(f"🆔 Job ID: {result['job_group_id']}")
    
    endpoint_info = result.get('endpoint', args.endpoint or 'unknown')
    auto_detected = result.get('endpoint_auto_detected', False)
    if auto_detected:
        print(f"🎯 Endpoint: {endpoint_info} (auto-detected)")
    else:
        print(f"🎯 Endpoint: {endpoint_info} (manually specified)")
    
    WEBUI_URL = 'http://usually-tp.gl.at.ply.gg:13295'
    print(f"🌐 Track progress at: {WEBUI_URL}")
    print(f"🔑 Login with Project ID: {args.project_id}")

if __name__ == "__main__":
    main()