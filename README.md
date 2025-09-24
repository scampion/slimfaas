# SLIMFAAS

## CGI-based FaaS solution for Alpine Linux with nginx

This setup provides a lightweight CGI-based FaaS (Function as a Service) solution for Alpine Linux.

## Key Features

✅ **Ultra-lightweight**: Uses Alpine's built-in tools + nginx + fcgiwrap  
✅ **CGI-native approach**: Pure CGI approach, no containers or complex runtimes  
✅ **Python support**: Full Python 3 function support with CGI headers  
✅ **REST API**: Complete API for function management  
✅ **Web interface**: Browser-based deployment and testing  
✅ **File operations**: Functions can read/write temporary files  
✅ **Direct access**: Functions callable via direct CGI endpoints  

## Installation

```bash
# 1. Run the setup script
chmod +x setup.sh && ./setup.sh

# 2. Start the service
rc-service cgi-faas start
rc-update add cgi-faas default

# 3. Test it works
curl http://localhost:8080/api/functions
curl -X POST http://localhost:8080/functions/hello.py -d "Alpine"
```

## Why This Solution is Perfect

- **Minimal footprint**: ~20MB total (nginx + fcgiwrap + Python)
- **No cgroup issues**: Pure CGI, no containers
- **Alpine-native**: Uses musl libc, perfect for Alpine
- **Production-ready**: nginx handles HTTP, fcgiwrap manages CGI
- **Extensible**: Easy to add new runtimes (PHP, Perl, etc.)

## Resource Usage

- **Memory**: ~15MB base + ~5MB per concurrent function
- **Storage**: ~20MB for the system
- **CPU**: Minimal overhead, scales with function complexity

This gives you a true serverless experience on Alpine Linux using the most lightweight approach possible - pure CGI with nginx! 🚀🐧
