#!/bin/sh
# Complete Nginx + CGI + Python FaaS setup for Alpine Linux

echo "🚀 Setting up Nginx CGI FaaS on Alpine Linux..."

# 1. Install required packages
apk add --no-cache nginx python3 py3-pip fcgiwrap spawn-fcgi

# 2. Create directory structure
mkdir -p /var/www/html/cgi-bin
mkdir -p /var/www/html/functions
mkdir -p /var/log/cgi-faas
mkdir -p /run/fcgiwrap

# 3. Configure nginx
cat > /etc/nginx/conf.d/cgi-faas.conf << 'EOF'
server {
    listen 8080;
    server_name localhost;
    root /var/www/html;
    index index.html;

    # Enable access logs
    access_log /var/log/nginx/cgi-faas-access.log;
    error_log /var/log/nginx/cgi-faas-error.log;

    # Serve static files
    location / {
        try_files $uri $uri/ =404;
    }

    # CGI handler for /cgi-bin/
    location ~ ^/cgi-bin/(.+\.cgi)$ {
        include fastcgi_params;
        fastcgi_param SCRIPT_FILENAME $document_root$fastcgi_script_name;
        fastcgi_param PATH_INFO $fastcgi_path_info;
        fastcgi_param QUERY_STRING $query_string;
        fastcgi_pass unix:/run/fcgiwrap/socket;
    }

    # Python CGI handler for /functions/
    location ~ ^/functions/(.+\.py)$ {
        include fastcgi_params;
        fastcgi_param SCRIPT_FILENAME $document_root$fastcgi_script_name;
        fastcgi_param PATH_INFO $fastcgi_path_info;
        fastcgi_param QUERY_STRING $query_string;
        fastcgi_pass unix:/run/fcgiwrap/socket;
    }

    # API endpoint for function management
    location ~ ^/api/(.*)$ {
        include fastcgi_params;
        fastcgi_param SCRIPT_FILENAME $document_root/cgi-bin/faas-api.cgi;
        fastcgi_param PATH_INFO /$1;
        fastcgi_param QUERY_STRING $query_string;
        fastcgi_pass unix:/run/fcgiwrap/socket;
    }
}
EOF

# 4. Create the main FaaS API handler
cat > /var/www/html/cgi-bin/faas-api.cgi << 'EOF'
#!/usr/bin/python3
"""
CGI-based FaaS API for function management
Endpoints:
- GET /api/functions - list all functions
- POST /api/functions - deploy new function
- GET /api/functions/{name} - get function info
- POST /api/functions/{name} - invoke function
- DELETE /api/functions/{name} - delete function
"""

import os
import sys
import json
import cgi
import cgitb
import subprocess
import tempfile
from pathlib import Path

# Enable CGI error reporting
cgitb.enable()

# Configuration
FUNCTIONS_DIR = Path("/var/www/html/functions")
FUNCTIONS_DIR.mkdir(exist_ok=True)

def send_response(data, status="200 OK", content_type="application/json"):
    """Send HTTP response"""
    print(f"Status: {status}")
    print(f"Content-Type: {content_type}")
    print()  # Empty line required
    if isinstance(data, dict):
        print(json.dumps(data))
    else:
        print(data)

def get_path_info():
    """Extract path info from request"""
    path_info = os.environ.get('PATH_INFO', '').strip('/')
    return path_info.split('/') if path_info else []

def read_post_data():
    """Read POST data"""
    try:
        content_length = int(os.environ.get('CONTENT_LENGTH', 0))
        if content_length > 0:
            post_data = sys.stdin.buffer.read(content_length)
            return json.loads(post_data.decode('utf-8'))
    except:
        pass
    return {}

def list_functions():
    """List all deployed functions"""
    functions = []
    for func_file in FUNCTIONS_DIR.glob("*.py"):
        if func_file.is_file():
            functions.append({
                "name": func_file.stem,
                "file": func_file.name,
                "size": func_file.stat().st_size
            })
    return {"functions": functions}

def deploy_function(name, code, runtime="python3"):
    """Deploy a new function"""
    if not name or not code:
        return {"error": "Name and code are required"}, "400 Bad Request"
    
    # Validate function name
    if not name.replace('_', '').replace('-', '').isalnum():
        return {"error": "Invalid function name"}, "400 Bad Request"
    
    func_file = FUNCTIONS_DIR / f"{name}.py"
    
    # Add CGI headers to function code
    function_code = f'''#!/usr/bin/python3
import os
import sys
import json
import cgi
import cgitb
from urllib.parse import parse_qs

cgitb.enable()

def get_input_data():
    """Get input data from CGI request"""
    method = os.environ.get('REQUEST_METHOD', 'GET')
    if method == 'POST':
        try:
            content_length = int(os.environ.get('CONTENT_LENGTH', 0))
            if content_length > 0:
                return sys.stdin.read(content_length)
        except:
            pass
    
    # Try query string for GET requests
    query_string = os.environ.get('QUERY_STRING', '')
    if query_string:
        params = parse_qs(query_string)
        if 'data' in params:
            return params['data'][0]
    
    return ""

def send_response(data):
    """Send CGI response"""
    print("Content-Type: application/json")
    print()
    if isinstance(data, dict):
        print(json.dumps(data))
    else:
        print(json.dumps({{"result": str(data)}}))

# User function code starts here
{code}

# CGI execution
if __name__ == "__main__":
    try:
        input_data = get_input_data()
        if 'main' in globals():
            result = main(input_data)
            send_response(result)
        else:
            send_response({{"error": "Function must define a 'main' function"}})
    except Exception as e:
        send_response({{"error": str(e)}})
'''
    
    try:
        func_file.write_text(function_code)
        func_file.chmod(0o755)
        return {"message": f"Function '{name}' deployed successfully"}
    except Exception as e:
        return {"error": str(e)}, "500 Internal Server Error"

def invoke_function(name, input_data=""):
    """Invoke a function"""
    func_file = FUNCTIONS_DIR / f"{name}.py"
    if not func_file.exists():
        return {"error": "Function not found"}, "404 Not Found"
    
    try:
        # Set up environment
        env = os.environ.copy()
        env['REQUEST_METHOD'] = 'POST'
        env['CONTENT_LENGTH'] = str(len(input_data))
        
        # Execute function
        result = subprocess.run(
            [str(func_file)],
            input=input_data,
            capture_output=True,
            text=True,
            timeout=30,
            env=env
        )
        
        if result.returncode == 0:
            # Try to parse JSON response
            try:
                return json.loads(result.stdout)
            except:
                return {"result": result.stdout.strip()}
        else:
            return {"error": result.stderr or "Function execution failed"}, "500 Internal Server Error"
            
    except subprocess.TimeoutExpired:
        return {"error": "Function timeout"}, "408 Request Timeout"
    except Exception as e:
        return {"error": str(e)}, "500 Internal Server Error"

def delete_function(name):
    """Delete a function"""
    func_file = FUNCTIONS_DIR / f"{name}.py"
    if not func_file.exists():
        return {"error": "Function not found"}, "404 Not Found"
    
    try:
        func_file.unlink()
        return {"message": f"Function '{name}' deleted successfully"}
    except Exception as e:
        return {"error": str(e)}, "500 Internal Server Error"

def main():
    """Main CGI handler"""
    method = os.environ.get('REQUEST_METHOD', 'GET')
    path_parts = get_path_info()
    
    try:
        if not path_parts or path_parts[0] != 'functions':
            send_response({"error": "Invalid API endpoint"}, "404 Not Found")
            return
        
        if len(path_parts) == 1:
            # /api/functions
            if method == 'GET':
                send_response(list_functions())
            elif method == 'POST':
                data = read_post_data()
                result, status = deploy_function(
                    data.get('name', ''),
                    data.get('code', ''),
                    data.get('runtime', 'python3')
                )
                send_response(result, status)
            else:
                send_response({"error": "Method not allowed"}, "405 Method Not Allowed")
        
        elif len(path_parts) == 2:
            # /api/functions/{name}
            func_name = path_parts[1]
            
            if method == 'GET':
                func_file = FUNCTIONS_DIR / f"{func_name}.py"
                if func_file.exists():
                    send_response({
                        "name": func_name,
                        "size": func_file.stat().st_size,
                        "exists": True
                    })
                else:
                    send_response({"error": "Function not found"}, "404 Not Found")
                    
            elif method == 'POST':
                # Invoke function
                content_length = int(os.environ.get('CONTENT_LENGTH', 0))
                input_data = sys.stdin.read(content_length) if content_length > 0 else ""
                
                result, *status = invoke_function(func_name, input_data)
                send_response(result, status[0] if status else "200 OK")
                
            elif method == 'DELETE':
                result, status = delete_function(func_name)
                send_response(result, status)
            else:
                send_response({"error": "Method not allowed"}, "405 Method Not Allowed")
        
        else:
            send_response({"error": "Invalid API endpoint"}, "404 Not Found")
            
    except Exception as e:
        send_response({"error": str(e)}, "500 Internal Server Error")

if __name__ == "__main__":
    main()
EOF

chmod +x /var/www/html/cgi-bin/faas-api.cgi

# 5. Create example functions
cat > /var/www/html/functions/hello.py << 'EOF'
#!/usr/bin/python3
import os
import sys
import json

print("Content-Type: application/json")
print()

def main(data):
    return {"message": f"Hello, {data or 'World'}!", "method": os.environ.get('REQUEST_METHOD')}

# Simple CGI execution
try:
    method = os.environ.get('REQUEST_METHOD', 'GET')
    
    if method == 'POST':
        content_length = int(os.environ.get('CONTENT_LENGTH', 0))
        input_data = sys.stdin.read(content_length) if content_length > 0 else ""
    else:
        input_data = ""
    
    result = main(input_data)
    print(json.dumps(result))
except Exception as e:
    print(json.dumps({"error": str(e)}))
EOF

chmod +x /var/www/html/functions/hello.py

# 6. Create system info function
cat > /var/www/html/functions/sysinfo.py << 'EOF'
#!/usr/bin/python3
import os
import sys
import json
import subprocess

print("Content-Type: application/json")
print()

def main(data):
    try:
        # Get system information
        hostname = subprocess.run(['hostname'], capture_output=True, text=True).stdout.strip()
        uptime = subprocess.run(['uptime'], capture_output=True, text=True).stdout.strip()
        memory = subprocess.run(['free', '-h'], capture_output=True, text=True).stdout.strip()
        
        return {
            "hostname": hostname,
            "uptime": uptime,
            "memory": memory.split('\n')[1] if memory else "N/A",
            "request_method": os.environ.get('REQUEST_METHOD'),
            "query_string": os.environ.get('QUERY_STRING', ''),
            "input": data
        }
    except Exception as e:
        return {"error": str(e)}

# CGI execution
try:
    method = os.environ.get('REQUEST_METHOD', 'GET')
    if method == 'POST':
        content_length = int(os.environ.get('CONTENT_LENGTH', 0))
        input_data = sys.stdin.read(content_length) if content_length > 0 else ""
    else:
        input_data = ""
    
    result = main(input_data)
    print(json.dumps(result, indent=2))
except Exception as e:
    print(json.dumps({"error": str(e)}))
EOF

chmod +x /var/www/html/functions/sysinfo.py

# 7. Create web interface
cat > /var/www/html/index.html << 'EOF'
<!DOCTYPE html>
<html>
<head>
    <title>CGI FaaS - Alpine Linux</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 40px; }
        .container { max-width: 800px; }
        .function { border: 1px solid #ddd; margin: 10px 0; padding: 15px; }
        button { background: #007cba; color: white; border: none; padding: 8px 16px; cursor: pointer; }
        button:hover { background: #005a87; }
        textarea { width: 100%; height: 200px; }
        pre { background: #f5f5f5; padding: 10px; overflow-x: auto; }
    </style>
</head>
<body>
    <div class="container">
        <h1>🚀 CGI FaaS on Alpine Linux</h1>
        
        <h2>Quick Test</h2>
        <button onclick="testHello()">Test Hello Function</button>
        <button onclick="testSysInfo()">Test System Info</button>
        <button onclick="listFunctions()">List Functions</button>
        
        <h2>Deploy New Function</h2>
        <p>Function Name: <input type="text" id="funcName" placeholder="myfunction" /></p>
        <textarea id="funcCode" placeholder="def main(data):&#10;    return {'result': f'Processed: {data}'"}></textarea>
        <br><button onclick="deployFunction()">Deploy Function</button>
        
        <h2>Response</h2>
        <pre id="response"></pre>
    </div>

    <script>
        function showResponse(data) {
            document.getElementById('response').textContent = JSON.stringify(data, null, 2);
        }

        function testHello() {
            fetch('/functions/hello.py', { method: 'POST', body: 'Alpine Linux' })
                .then(r => r.json())
                .then(showResponse)
                .catch(e => showResponse({error: e.message}));
        }

        function testSysInfo() {
            fetch('/functions/sysinfo.py')
                .then(r => r.json())
                .then(showResponse)
                .catch(e => showResponse({error: e.message}));
        }

        function listFunctions() {
            fetch('/api/functions')
                .then(r => r.json())
                .then(showResponse)
                .catch(e => showResponse({error: e.message}));
        }

        function deployFunction() {
            const name = document.getElementById('funcName').value;
            const code = document.getElementById('funcCode').value;
            
            fetch('/api/functions', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({name: name, code: code})
            })
            .then(r => r.json())
            .then(showResponse)
            .catch(e => showResponse({error: e.message}));
        }
    </script>
</body>
</html>
EOF

# 8. Create startup script
cat > /etc/init.d/cgi-faas << 'EOF'
#!/sbin/openrc-run

name="CGI FaaS"
description="Nginx CGI-based FaaS"

depend() {
    need net
    after nginx
}

start() {
    ebegin "Starting fcgiwrap for CGI FaaS"
    
    # Start fcgiwrap
    spawn-fcgi -s /run/fcgiwrap/socket -f /usr/bin/fcgiwrap -u nginx -g nginx -P /run/fcgiwrap.pid
    
    # Start nginx if not running
    if ! pgrep nginx > /dev/null; then
        nginx
    fi
    
    eend $?
}

stop() {
    ebegin "Stopping CGI FaaS"
    
    if [ -f /run/fcgiwrap.pid ]; then
        kill $(cat /run/fcgiwrap.pid)
        rm -f /run/fcgiwrap.pid
    fi
    
    eend $?
}
EOF

chmod +x /etc/init.d/cgi-faas

# 9. Setup permissions
chown -R nginx:nginx /var/www/html
chown -R nginx:nginx /var/log/cgi-faas

echo "✅ Setup complete!"
echo ""
echo "🔧 To start the service:"
echo "   rc-service cgi-faas start"
echo "   rc-update add cgi-faas default"
echo ""
echo "🌐 Access your FaaS:"
echo "   http://localhost:8080           - Web interface"
echo "   http://localhost:8080/functions/hello.py - Test function"
echo ""
echo "📋 API Endpoints:"
echo "   GET  /api/functions             - List functions"
echo "   POST /api/functions             - Deploy function"
echo "   POST /api/functions/{name}      - Invoke function"
echo ""
echo "🧪 Test with curl:"
echo '   curl -X POST http://localhost:8080/functions/hello.py -d "World"'
echo '   curl http://localhost:8080/api/functions'


