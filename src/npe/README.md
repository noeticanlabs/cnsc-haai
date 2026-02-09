# NPE (Noetican Proposal Engine)

The NPE is an external proposer service for CNSC-HAAI that handles proposal generation and repair operations.

## Starting the NPE Service

### Quick Start

```bash
# From the repo root directory
cd src/npe
pip install -e .

# Start the server on HTTP (default: 127.0.0.1:8080)
npe serve

# Start on a specific port
npe serve --port 9000

# Start on Unix socket
npe serve --socket /tmp/npe.sock
```

### Using the Python API

```python
import asyncio
from npe.api.server import NPEServer

async def main():
    # Create server
    server = NPEServer(host="127.0.0.1", port=8080)
    
    # Start serving
    await server.start()
    print("NPE server started on http://127.0.0.1:8080")
    
    # Keep running
    try:
        await asyncio.Event().wait()
    except KeyboardInterrupt:
        await server.stop()

asyncio.run(main())
```

### CLI Commands

The NPE CLI provides the following commands:

- `npe serve` - Start the NPE HTTP/Unix socket server
- `npe index` - Build corpus index for retrieval
- `npe propose` - Run a single proposal request
- `npe repair` - Run a single repair request

### Environment Variables

No environment variables are required. The NPE service:

- Finds schemas automatically regardless of working directory
- Loads registry from the package (configurable via `--registry`)
- Uses embedded corpus/index if available

### Schema Location

NPE schemas are packaged with the distribution:

- `npe/schemas/npe_request.schema.json` - Request validation schema
- `npe/schemas/npe_response.schema.json` - Response validation schema

The schema loader automatically resolves paths relative to the package installation, so validation works from any working directory.
