#!/bin/bash
# CGI FaaS Usage Guide and Examples

echo "🚀 CGI FaaS Usage Guide"
echo "======================="

# 1. Installation (run the setup script first)
echo "📦 1. Installation:"
echo "   Save the setup script and run: chmod +x setup.sh && ./setup.sh"
echo "   Start services: rc-service cgi-faas start"
echo ""

# 2. Basic API Usage
echo "📋 2. API Endpoints:"
echo "   GET  /api/functions                - List all functions"
echo "   POST /api/functions                - Deploy new function"
echo "   GET  /api/functions/{name}         - Get function info"
echo "   POST /api/functions/{name}         - Invoke function"
echo "   DELETE /api/functions/{name}       - Delete function"
echo ""

# 3. Deploy functions using curl
echo "🚀 3. Deploy Example Functions:"
echo ""

echo "📊 Calculator Function:"
cat << 'EOF'
curl -X POST http://localhost:8080/api/functions \
  -H "Content-Type: application/json" \
  -d '{
    "name": "calculator",
    "code": "def main(data):\n    try:\n        if not data:\n            return {\"error\": \"Provide math expression\"}\n        
allowed = set(\"0123456789+-*/.() \")\n        if not all(c in allowed for c in data):\n            return {\"error\": 
\"Invalid chars\"}\n        result = eval(data)\n        return {\"expression\": data, \"result\": result}\n    except 
Exception as e:\n        return {\"error\": str(e)}"
  }'
EOF

echo ""
echo "🔤 Text Processing Function:"
cat << 'EOF'
curl -X POST http://localhost:8080/api/functions \
  -H "Content-Type: application/json" \
  -d '{
    "name": "textproc",
    "code": "import re\nfrom collections import Counter\n\ndef main(data):\n    if not data:\n        return {\"error\": 
\"Provide text\"}\n    text = str(data).strip()\n    words = re.findall(r\"\\b\\w+\\b\", text.lower())\n    return {\n        
\"char_count\": len(text),\n        \"word_count\": len(text.split()),\n        \"top_words\": 
dict(Counter(words).most_common(3)),\n        \"avg_word_len\": round(sum(len(w) for w in words) / len(words), 2) if words 
else 0\n    }"
  }'
EOF

echo ""
echo "🌐 Simple Web Info Function:"
cat << 'EOF'
curl -X POST http://localhost:8080/api/functions \
  -H "Content-Type: application/json" \
  -d '{
    "name": "webinfo",
    "code": "import urllib.request\nimport re\n\ndef main(data):\n    try:\n        url = data.strip()\n        if not 
url.startswith((\"http://\", \"https://\")):\n            url = \"https://\" + url\n        req = 
urllib.request.Request(url, headers={\"User-Agent\": \"CGI-FaaS/1.0\"})\n        with urllib.request.urlopen(req, 
timeout=10) as response:\n            content = response.read().decode(\"utf-8\", errors=\"ignore\")\n        title_match = 
re.search(r\"<title[^>]*>([^<]+)</title>\", content, re.I)\n        title = title_match.group(1).strip() if title_match 
else \"No title\"\n        return {\"url\": url, \"title\": title, \"length\": len(content)}\n    except Exception as e:\n        
return {\"error\": str(e)}"
  }'
EOF

echo ""
echo "🗂️ File Operations Function:"
cat << 'EOF'
curl -X POST http://localhost:8080/api/functions \
  -H "Content-Type: application/json" \
  -d '{
    "name": "fileops",
    "code": "import os\nimport json\n\ndef main(data):\n    try:\n        req = json.loads(data) if data.startswith(\"{\") 
else {\"op\": \"list\"}\n        op = req.get(\"op\", \"list\")\n        temp_dir = \"/tmp/cgi-faas\"\n        
os.makedirs(temp_dir, exist_ok=True)\n        \n        if op == \"write\":\n            filename = req.get(\"file\", 
\"temp.txt\")\n            content = req.get(\"content\", \"\")\n            filepath = os.path.join(temp_dir, filename)\n            
with open(filepath, \"w\") as f:\n                f.write(content)\n            return {\"op\": \"write\", \"file\": 
filename, \"size\": len(content)}\n        \n        elif op == \"read\":\n            filename = req.get(\"file\", 
\"temp.txt\")\n            filepath = os.path.join(temp_dir, filename)\n            if os.path.exists(filepath):\n                
with open(filepath, \"r\") as f:\n                    content = f.read()\n                return {\"op\": \"read\", 
\"file\": filename, \"content\": content}\n            return {\"error\": \"File not found\"}\n        \n        else:  # 
list\n            files = []\n            for f in os.listdir(temp_dir):\n                if 
os.path.isfile(os.path.join(temp_dir, f)):\n                    size = os.path.getsize(os.path.join(temp_dir, f))\n                    
files.append({\"name\": f, \"size\": size})\n            return {\"op\": \"list\", \"files\": files}\n    \n    except 
Exception as e:\n        return {\"error\": str(e)}"
  }'
EOF

echo ""
echo "⚡ 4. Test Functions:"
echo ""

echo "🧮 Test Calculator:"
echo "curl -X POST http://localhost:8080/api/functions/calculator -d '5+3*2'"
echo ""

echo "📝 Test Text Processing:"
echo "curl -X POST http://localhost:8080/api/functions/textproc -d 'Hello world! This is a test message with hello 
repeated.'"
echo ""

echo "🌐 Test Web Info:"
echo "curl -X POST http://localhost:8080/api/functions/webinfo -d 'httpbin.org'"
echo ""

echo "📁 Test File Operations:"
echo "# Write file:"
echo 'curl -X POST http://localhost:8080/api/functions/fileops -d '\''{"op":"write","file":"test.txt","content":"Hello from 
CGI FaaS!"}'\'''
echo "# Read file:"
echo 'curl -X POST http://localhost:8080/api/functions/fileops -d '\''{"op":"read","file":"test.txt"}'\'''
echo "# List files:"
echo "curl -X POST http://localhost:8080/api/functions/fileops -d '{\"op\":\"list\"}'"
echo ""

echo "📋 5. Management Commands:"
echo ""

echo "📃 List all functions:"
echo "curl http://localhost:8080/api/functions"
echo ""

echo "ℹ️ Get function info:"
echo "curl http://localhost:8080/api/functions/calculator"
echo ""

echo "🗑️ Delete function:"
echo "curl -X DELETE http://localhost:8080/api/functions/calculator"
echo ""

echo "🔧 6. Direct Function Access:"
echo "Functions can also be called directly via their CGI endpoints:"
echo "curl -X POST http://localhost:8080/functions/hello.py -d 'Direct call'"
echo "curl http://localhost:8080/functions/sysinfo.py"
echo ""

echo "🖥️ 7. Web Interface:"
echo "Open http://localhost:8080 in your browser for the web interface"
echo ""

echo "🐛 8. Debugging:"
echo "Check logs:"
echo "  tail -f /var/log/nginx/cgi-faas-error.log"
echo "  tail -f /var/log/nginx/cgi-faas-access.log"
echo ""
echo "Test CGI directly:"
echo "  cd /var/www/html && ./cgi-bin/faas-api.cgi"
echo "  REQUEST_METHOD=GET PATH_INFO=/functions ./cgi-bin/faas-api.cgi"
echo ""

echo "⚠️ 9. Security Notes:"
echo "- Functions run as nginx user"
echo "- Limited to /tmp/cgi-faas for file operations"
echo "- 30-second execution timeout"
echo "- Basic input validation in examples"
echo "- For production, add authentication and rate limiting"
echo ""

echo "🔄 10. Service Management:"
echo "Start:    rc-service cgi-faas start"
echo "Stop:     rc-service cgi-faas stop"
echo "Restart:  rc-service cgi-faas restart"
echo "Status:   rc-service cgi-faas status"
echo "Auto-start: rc-update add cgi-faas default"
echo ""

echo "✨ 11. Advanced Examples:"
echo ""

echo "🎯 Deploy a JSON API function:"
cat << 'EOF'
curl -X POST http://localhost:8080/api/functions \
  -H "Content-Type: application/json" \
  -d '{
    "name": "jsonapi",
    "code": "import json\n\ndef main(data):\n    try:\n        if not data:\n            return {\"endpoints\": 
[\"/health\", \"/time\", \"/echo\"], \"usage\": \"Send JSON with 'endpoint' and 'payload'\"}\n        \n        req = 
json.loads(data)\n        endpoint = req.get(\"endpoint\", \"/health\")\n        payload = req.get(\"payload\", {})\n        
\n        if endpoint == \"/health\":\n            return {\"status\": \"healthy\", \"service\": \"CGI-FaaS\", \"version\": 
\"1.0\"}\n        elif endpoint == \"/time\":\n            import datetime\n            return {\"timestamp\": 
datetime.datetime.now().isoformat(), \"timezone\": \"UTC\"}\n        elif endpoint == \"/echo\":\n            return 
{\"echoed\": payload, \"type\": type(payload).__name__}\n        else:\n            return {\"error\": \"Unknown 
endpoint\"}\n    \n    except Exception as e:\n        return {\"error\": str(e)}"
  }'
EOF

echo ""
echo "Test the JSON API:"
echo 'curl -X POST http://localhost:8080/api/functions/jsonapi -d '\''{"endpoint":"/health"}'\'''
echo 'curl -X POST http://localhost:8080/api/functions/jsonapi -d 
'\''{"endpoint":"/echo","payload":{"message":"Hello"}}'\'''
echo ""

echo "🎉 Your CGI FaaS is ready! Happy serverless computing on Alpine! 🐧"


