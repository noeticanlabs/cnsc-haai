"""
NPE API Server.

Implements HTTP server for NPE service using aiohttp.
Supports both HTTP and Unix socket modes.
"""

import asyncio
import os
import signal
import socket
import sys
from typing import Optional

from aiohttp import web

from .routes import NPEService, NPERouter, setup_routes
from .wire import create_wire_error


class NPEServer:
    """NPE HTTP/Unix Socket Server.

    Attributes:
        host: Host to bind to (for TCP mode)
        port: Port to bind to (for TCP mode)
        socket_path: Unix socket path (for socket mode)
        registry_path: Path to registry manifest
        corpus_index_path: Optional path to corpus index
        app: The aiohttp application
        runner: The application runner
        site: The web site
    """

    def __init__(
        self,
        host: str = "127.0.0.1",
        port: int = 8080,
        socket_path: Optional[str] = None,
        registry_path: Optional[str] = None,
        corpus_index_path: Optional[str] = None,
    ):
        """Initialize the server.

        Args:
            host: Host for HTTP mode
            port: Port for HTTP mode
            socket_path: Path for Unix socket mode
            registry_path: Path to registry manifest
            corpus_index_path: Path to corpus index
        """
        self.host = host
        self.port = port
        self.socket_path = socket_path
        self.registry_path = registry_path
        self.corpus_index_path = corpus_index_path

        self.app: Optional[web.Application] = None
        self.runner: Optional[web.AppRunner] = None
        self.site: Optional[web.Site] = None
        self._service: Optional[NPEService] = None
        self._shutdown_event: Optional[asyncio.Event] = None

    async def _create_app(self) -> web.Application:
        """Create and configure the aiohttp application.

        Returns:
            Configured application
        """
        app = web.Application(
            middlewares=[
                self._logging_middleware,
                self._error_middleware,
            ]
        )

        # Load registry
        from ..registry.loader import load_registry

        registry = load_registry(self.registry_path)

        # Load corpus index if available
        corpus_index = None
        if self.corpus_index_path and os.path.exists(self.corpus_index_path):
            from ..retrieval.index_build import load_index

            corpus_index = load_index(self.corpus_index_path)

        # Create service and router
        self._service = NPEService(registry, corpus_index)
        router = NPERouter(self._service)

        # Set up routes
        setup_routes(app, router)

        return app

    async def _logging_middleware(self, app, handler):
        """Logging middleware for requests."""

        async def middleware(request):
            import time

            start = time.perf_counter()
            response = await handler(request)
            elapsed = (time.perf_counter() - start) * 1000
            print(f"[NPE] {request.method} {request.path} - {response.status} - {elapsed:.2f}ms")
            return response

        return middleware

    async def _error_middleware(self, app, handler):
        """Error handling middleware."""

        async def middleware(request):
            try:
                return await handler(request)
            except Exception as e:
                print(f"[NPE] Error: {e}", file=sys.stderr)
                error_response = create_wire_error(str(e))
                return web.Response(
                    body=error_response,
                    content_type="application/json; charset=utf-8",
                    status=500,
                )

        return middleware

    async def start(self) -> None:
        """Start the server."""
        # Create application
        self.app = await self._create_app()

        # Create runner
        self.runner = web.AppRunner(self.app)
        await self.runner.setup()

        # Create site
        if self.socket_path:
            # Unix socket mode
            # Clean up existing socket
            if os.path.exists(self.socket_path):
                os.unlink(self.socket_path)

            self.site = web.UnixSite(self.runner, self.socket_path)
        else:
            # TCP mode
            self.site = web.TCPSite(self.runner, self.host, self.port)

        await self.site.start()

        # Print startup banner with artifact hashes
        self._print_startup_banner()

        # Set up shutdown handler
        self._shutdown_event = asyncio.Event()

        # Handle signals
        loop = asyncio.get_event_loop()
        for sig in (signal.SIGTERM, signal.SIGINT):
            loop.add_signal_handler(sig, self._signal_handler)

        # Wait for shutdown
        await self._shutdown_event.wait()

    def _print_startup_banner(self) -> None:
        """Print startup banner with artifact hashes for replay safety."""
        print("=" * 60)
        print("NPE Service Starting")
        print("=" * 60)

        # Get registry hash
        from ..registry.loader import load_registry

        try:
            registry = load_registry(self.registry_path)
            print(f"Registry: {registry.registry_name} v{registry.registry_version}")
            print(f"Registry Hash: {registry.registry_hash}")
        except Exception as e:
            print(f"Registry: Failed to load ({e})")
            print("Registry Hash: N/A")

        # Get corpus index hash
        try:
            if self.corpus_index_path and os.path.exists(self.corpus_index_path):
                from ..retrieval.index_build import load_index

                index = load_index(self.corpus_index_path)
                corpus_hash = index.get("corpus_snapshot_hash", "N/A")
                chunk_count = index.get("chunk_count", 0)
                print(f"Corpus Index: {chunk_count} chunks")
                print(f"Corpus Hash: {corpus_hash}")
            else:
                print("Corpus Index: Not configured")
                print("Corpus Hash: N/A")
        except Exception as e:
            print(f"Corpus Index: Failed to load ({e})")
            print("Corpus Hash: N/A")

        # Get schema bundle hash
        try:
            from ..schema import get_schema_bundle_hash

            schema_hash = get_schema_bundle_hash()
            print(f"Schema Bundle Hash: {schema_hash or 'N/A'}")
        except Exception as e:
            print(f"Schema Bundle Hash: Failed to compute ({e})")

        print("=" * 60)

        # Print binding info
        if self.socket_path:
            print(f"Server started on unix://{self.socket_path}")
        else:
            print(f"Server started on http://{self.host}:{self.port}")
        print("=" * 60)

    def _signal_handler(self) -> None:
        """Handle shutdown signals."""
        print("\n[NPE] Shutting down...")
        if self._shutdown_event:
            self._shutdown_event.set()

    async def stop(self) -> None:
        """Stop the server."""
        if self.runner:
            await self.runner.cleanup()

        # Clean up socket file
        if self.socket_path and os.path.exists(self.socket_path):
            os.unlink(self.socket_path)

        print("[NPE] Server stopped")

    @property
    def service(self) -> NPEService:
        """Get the NPE service."""
        if self._service is None:
            raise RuntimeError("Server not started")
        return self._service


async def create_server(
    host: str = "127.0.0.1",
    port: int = 8080,
    socket_path: Optional[str] = None,
    registry_path: Optional[str] = None,
    corpus_index_path: Optional[str] = None,
) -> NPEServer:
    """Create and configure an NPE server.

    Args:
        host: Host for HTTP mode
        port: Port for HTTP mode
        socket_path: Path for Unix socket mode
        registry_path: Path to registry manifest
        corpus_index_path: Path to corpus index

    Returns:
        Configured server instance
    """
    server = NPEServer(
        host=host,
        port=port,
        socket_path=socket_path,
        registry_path=registry_path,
        corpus_index_path=corpus_index_path,
    )
    return server


def run_server():
    """Run the NPE server from command line."""
    import argparse

    parser = argparse.ArgumentParser(description="NPE Service")
    parser.add_argument("--host", default="127.0.0.1", help="Host to bind to")
    parser.add_argument("--port", type=int, default=8080, help="Port to bind to")
    parser.add_argument("--socket", help="Unix socket path")
    parser.add_argument("--registry", help="Path to registry manifest")
    parser.add_argument("--index", help="Path to corpus index")

    args = parser.parse_args()

    server = NPEServer(
        host=args.host,
        port=args.port,
        socket_path=args.socket,
        registry_path=args.registry,
        corpus_index_path=args.index,
    )

    try:
        asyncio.run(server.start())
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    run_server()
