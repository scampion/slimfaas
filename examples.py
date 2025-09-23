# Example 1: Simple Math Function
# Deploy this as "calculator"

def main(data):
    """
    Simple calculator function
    Input: "5+3" or "10*2" or "20/4"
    """
    try:
        if not data:
            return {"error": "Please provide a math expression"}
        
        # Basic security - only allow safe characters
        allowed_chars = set('0123456789+-*/.() ')
        if not all(c in allowed_chars for c in data):
            return {"error": "Invalid characters in expression"}
        
        result = eval(data)
        return {
            "expression": data,
            "result": result,
            "type": type(result).__name__
        }
    except Exception as e:
        return {"error": str(e)}

# Deploy with:
# curl -X POST http://localhost:8080/api/functions \
#   -H "Content-Type: application/json" \
#   -d '{"name": "calculator", "code": "def main(data):\n    try:\n        if not data:\n            return {\"error\": 
\"Please provide a math expression\"}\n        allowed_chars = set(\"0123456789+-*/.() \")\n        if not all(c in 
allowed_chars for c in data):\n            return {\"error\": \"Invalid characters in expression\"}\n        result = 
eval(data)\n        return {\"expression\": data, \"result\": result, \"type\": type(result).__name__}\n    except 
Exception as e:\n        return {\"error\": str(e)}"}'

# Test with:
# curl -X POST http://localhost:8080/api/functions/calculator -d "5+3*2"

# ==========================================

# Example 2: Text Processing Function
# Deploy this as "textproc"

import re
from collections import Counter

def main(data):
    """
    Text processing function
    Analyzes text and returns statistics
    """
    if not data:
        return {"error": "Please provide text to analyze"}
    
    text = str(data).strip()
    
    # Basic statistics
    char_count = len(text)
    word_count = len(text.split())
    line_count = len(text.splitlines())
    
    # Word frequency
    words = re.findall(r'\b\w+\b', text.lower())
    word_freq = dict(Counter(words).most_common(5))
    
    # Character analysis
    alpha_count = sum(1 for c in text if c.isalpha())
    digit_count = sum(1 for c in text if c.isdigit())
    space_count = sum(1 for c in text if c.isspace())
    
    return {
        "text": text[:100] + "..." if len(text) > 100 else text,
        "statistics": {
            "characters": char_count,
            "words": word_count,
            "lines": line_count,
            "alphabetic": alpha_count,
            "digits": digit_count,
            "spaces": space_count
        },
        "top_words": word_freq,
        "avg_word_length": round(sum(len(word) for word in words) / len(words), 2) if words else 0
    }

# ==========================================

# Example 3: JSON Processor Function
# Deploy this as "jsonproc"

import json

def main(data):
    """
    JSON processing function
    Validates, formats, and manipulates JSON data
    """
    try:
        if not data:
            return {"error": "Please provide JSON data"}
        
        # Try to parse JSON
        parsed = json.loads(data)
        
        # Generate statistics
        def analyze_json(obj, path="root"):
            stats = {"keys": 0, "arrays": 0, "objects": 0, "primitives": 0, "max_depth": 0}
            
            def recurse(item, depth=0):
                stats["max_depth"] = max(stats["max_depth"], depth)
                
                if isinstance(item, dict):
                    stats["objects"] += 1
                    stats["keys"] += len(item)
                    for value in item.values():
                        recurse(value, depth + 1)
                elif isinstance(item, list):
                    stats["arrays"] += 1
                    for value in item:
                        recurse(value, depth + 1)
                else:
                    stats["primitives"] += 1
            
            recurse(obj)
            return stats
        
        stats = analyze_json(parsed)
        
        return {
            "valid": True,
            "formatted": json.dumps(parsed, indent=2),
            "statistics": stats,
            "type": type(parsed).__name__,
            "size_bytes": len(data)
        }
        
    except json.JSONDecodeError as e:
        return {
            "valid": False,
            "error": f"Invalid JSON: {str(e)}",
            "position": getattr(e, 'pos', None)
        }
    except Exception as e:
        return {"error": str(e)}

# ==========================================

# Example 4: File System Function
# Deploy this as "fileops"

import os
import tempfile
import base64

def main(data):
    """
    File operations function
    Can create, read, and list temporary files
    """
    try:
        if not data:
            return {"error": "Please provide operation and data"}
        
        # Parse input (expecting JSON)
        import json
        request = json.loads(data) if data.startswith('{') else {"operation": "list", "data": data}
        
        operation = request.get("operation", "list")
        file_data = request.get("data", "")
        filename = request.get("filename", "temp.txt")
        
        temp_dir = "/tmp/cgi-faas"
        os.makedirs(temp_dir, exist_ok=True)
        
        if operation == "write":
            # Write file
            filepath = os.path.join(temp_dir, filename)
            with open(filepath, 'w') as f:
                f.write(file_data)
            return {
                "operation": "write",
                "filename": filename,
                "size": len(file_data),
                "path": filepath
            }
            
        elif operation == "read":
            # Read file
            filepath = os.path.join(temp_dir, filename)
            if os.path.exists(filepath):
                with open(filepath, 'r') as f:
                    content = f.read()
                return {
                    "operation": "read",
                    "filename": filename,
                    "content": content,
                    "size": len(content)
                }
            else:
                return {"error": f"File {filename} not found"}
                
        elif operation == "list":
            # List files
            files = []
            for f in os.listdir(temp_dir):
                filepath = os.path.join(temp_dir, f)
                if os.path.isfile(filepath):
                    stat = os.stat(filepath)
                    files.append({
                        "name": f,
                        "size": stat.st_size,
                        "modified": stat.st_mtime
                    })
            return {
                "operation": "list",
                "files": files,
                "count": len(files)
            }
            
        else:
            return {"error": f"Unknown operation: {operation}"}
            
    except Exception as e:
        return {"error": str(e)}

# ==========================================

# Example 5: Web Scraper Function (simple)
# Deploy this as "webscraper"

import urllib.request
import urllib.parse
import re

def main(data):
    """
    Simple web scraper function
    Fetches webpage and extracts basic info
    """
    try:
        if not data:
            return {"error": "Please provide a URL"}
        
        url = data.strip()
        
        # Basic URL validation
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
        
        # Fetch webpage (with timeout)
        req = urllib.request.Request(url, headers={
            'User-Agent': 'CGI-FaaS-Bot/1.0'
        })
        
        with urllib.request.urlopen(req, timeout=10) as response:
            content = response.read().decode('utf-8', errors='ignore')
            headers = dict(response.headers)
        
        # Extract basic information
        title_match = re.search(r'<title[^>]*>([^<]+)</title>', content, re.IGNORECASE)
        title = title_match.group(1).strip() if title_match else "No title found"
        
        # Count elements
        links = len(re.findall(r'<a[^>]*href=["\'][^"\']*["\'][^>]*>', content, re.IGNORECASE))
        images = len(re.findall(r'<img[^>]*src=["\'][^"\']*["\'][^>]*>', content, re.IGNORECASE))
        
        return {
            "url": url,
            "title": title,
            "content_length": len(content),
            "content_type": headers.get('Content-Type', 'unknown'),
            "server": headers.get('Server', 'unknown'),
            "links": links,
            "images": images,
            "headers": dict(list(headers.items())[:5])  # First 5 headers
        }
        
    except urllib.error.URLError as e:
        return {"error": f"URL error: {str(e)}"}
    except Exception as e:
        return {"error": str(e)}


