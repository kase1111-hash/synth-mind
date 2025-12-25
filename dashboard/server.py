"""
Dashboard Server - WebSocket server for real-time state streaming.
Serves the HTML dashboard and broadcasts internal state updates.
Includes JWT authentication for production security.
Supports HTTPS/WSS encryption for secure communication.
"""

import asyncio
import json
import ssl
import sys
from pathlib import Path
from typing import Set, Optional
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from aiohttp import web
    import aiohttp_cors
except ImportError:
    raise ImportError(
        "aiohttp and aiohttp-cors are required for the dashboard server. "
        "Install them with: pip install aiohttp aiohttp-cors"
    )

from core.orchestrator import SynthOrchestrator
from utils.auth import AuthManager, UserRole
from utils.rate_limiter import RateLimiter, RateLimitConfig, create_rate_limit_middleware
from utils.access_logger import AccessLogger, AccessLogConfig, LogFormat, create_access_log_middleware
from utils.ip_firewall import IPFirewall, FirewallConfig, FirewallMode, create_firewall_middleware

class DashboardServer:
    """WebSocket server for streaming internal state to dashboard."""

    # Public paths that don't require authentication
    PUBLIC_PATHS = [
        '/',
        '/ws',
        '/timeline',
        '/api/auth/login',
        '/api/auth/setup',
        '/api/auth/status',
        '/api/auth/refresh'
    ]

    def __init__(self, orchestrator: SynthOrchestrator, port: int = 8080,
                 auth_enabled: bool = True, allowed_origins: list = None,
                 ssl_cert: str = None, ssl_key: str = None,
                 ssl_context: ssl.SSLContext = None,
                 rate_limit_enabled: bool = True,
                 rate_limit_config: RateLimitConfig = None,
                 access_log_enabled: bool = True,
                 access_log_config: AccessLogConfig = None,
                 firewall_enabled: bool = False,
                 firewall_config: FirewallConfig = None):
        """
        Initialize the dashboard server.

        Args:
            orchestrator: The SynthOrchestrator instance
            port: Server port (default: 8080)
            auth_enabled: Enable JWT authentication (default: True)
            allowed_origins: List of allowed CORS origins
            ssl_cert: Path to SSL certificate file (enables HTTPS)
            ssl_key: Path to SSL private key file
            ssl_context: Pre-configured SSLContext (overrides ssl_cert/ssl_key)
            rate_limit_enabled: Enable rate limiting (default: True)
            rate_limit_config: Custom rate limit configuration
            access_log_enabled: Enable access logging (default: True)
            access_log_config: Custom access log configuration
            firewall_enabled: Enable IP firewall (default: False)
            firewall_config: Custom firewall configuration
        """
        self.orchestrator = orchestrator
        self.port = port
        self.auth_enabled = auth_enabled
        self.websockets: Set[web.WebSocketResponse] = set()
        self.state_cache = {}

        # SSL/TLS configuration
        self.ssl_context = ssl_context
        self.ssl_cert = ssl_cert
        self.ssl_key = ssl_key
        self.is_https = False

        # Initialize SSL context if cert/key provided
        if ssl_cert and ssl_key and not ssl_context:
            self.ssl_context = self._create_ssl_context(ssl_cert, ssl_key)

        if self.ssl_context:
            self.is_https = True

        # Determine protocol for CORS
        protocol = "https" if self.is_https else "http"

        # CORS allowed origins (restricted to localhost by default for security)
        self.allowed_origins = allowed_origins or [
            f"{protocol}://localhost:8080",
            f"{protocol}://127.0.0.1:8080",
            f"{protocol}://localhost:{port}",
            f"{protocol}://127.0.0.1:{port}",
            # Also allow HTTP origins when using HTTPS (for redirects)
            f"http://localhost:{port}",
            f"http://127.0.0.1:{port}",
        ]

        # Initialize authentication
        self.auth = AuthManager() if auth_enabled else None

        # Initialize rate limiter
        self.rate_limit_enabled = rate_limit_enabled
        if rate_limit_enabled:
            config = rate_limit_config or RateLimitConfig()
            self.rate_limiter = RateLimiter(config)
        else:
            self.rate_limiter = None

        # Initialize access logger
        self.access_log_enabled = access_log_enabled
        if access_log_enabled:
            config = access_log_config or AccessLogConfig()
            self.access_logger = AccessLogger(config)
        else:
            self.access_logger = None

        # Initialize IP firewall
        self.firewall_enabled = firewall_enabled
        if firewall_enabled:
            config = firewall_config or FirewallConfig()
            self.firewall = IPFirewall(config)
        else:
            self.firewall = None

        # Build middleware stack (order: firewall -> logging -> rate limit -> auth)
        middlewares = []
        if firewall_enabled and self.firewall:
            middlewares.append(create_firewall_middleware(self.firewall))
        if access_log_enabled and self.access_logger:
            middlewares.append(create_access_log_middleware(self.access_logger))
        if rate_limit_enabled and self.rate_limiter:
            middlewares.append(create_rate_limit_middleware(self.rate_limiter))
        if auth_enabled:
            middlewares.append(self._auth_middleware)

        # Create app with middleware
        self.app = web.Application(middlewares=middlewares)

        # Setup routes
        self._setup_routes()

    def _create_ssl_context(self, cert_path: str, key_path: str) -> ssl.SSLContext:
        """Create SSL context from certificate and key files."""
        try:
            from utils.ssl_utils import create_ssl_context
            return create_ssl_context(cert_path, key_path)
        except ImportError:
            # Fallback if ssl_utils not available
            ssl_context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
            ssl_context.load_cert_chain(cert_path, key_path)
            ssl_context.minimum_version = ssl.TLSVersion.TLSv1_2
            return ssl_context
        
    def _setup_routes(self):
        """Setup HTTP and WebSocket routes."""
        # Core dashboard routes
        self.app.router.add_get('/', self.serve_dashboard)
        self.app.router.add_get('/ws', self.websocket_handler)
        self.app.router.add_get('/api/state', self.get_state)
        self.app.router.add_post('/api/simulate', self.simulate_turn)
        self.app.router.add_post('/api/reflect', self.trigger_reflection)
        self.app.router.add_post('/api/generate', self.peer_generate)
        self.app.router.add_post('/api/federated/receive', self.federated_receive)
        self.app.router.add_get('/api/federated/stats', self.federated_stats)

        # Chat API - process messages through full cognitive pipeline
        self.app.router.add_post('/api/chat', self.chat_handler)

        # Collaborative Projects API
        self.app.router.add_get('/api/collab/projects', self.collab_projects)
        self.app.router.add_post('/api/collab/sync', self.collab_sync)
        self.app.router.add_get('/api/collab/stats', self.collab_stats)

        # Authentication API (always available, even if auth disabled)
        self.app.router.add_get('/api/auth/status', self.auth_status)
        self.app.router.add_post('/api/auth/login', self.auth_login)
        self.app.router.add_post('/api/auth/logout', self.auth_logout)
        self.app.router.add_post('/api/auth/refresh', self.auth_refresh)
        self.app.router.add_post('/api/auth/setup', self.auth_setup)

        # User management API (admin only)
        self.app.router.add_get('/api/users', self.list_users)
        self.app.router.add_post('/api/users', self.create_user)
        self.app.router.add_delete('/api/users/{username}', self.delete_user)
        self.app.router.add_put('/api/users/{username}/password', self.update_password)
        self.app.router.add_put('/api/users/{username}/role', self.update_role)

        # Timeline / Gantt Chart API
        self.app.router.add_get('/timeline', self.serve_timeline)
        self.app.router.add_get('/api/timeline', self.get_timeline_data)

        # Rate limiting API
        self.app.router.add_get('/api/ratelimit/stats', self.ratelimit_stats)

        # Access logging API
        self.app.router.add_get('/api/accesslog/stats', self.accesslog_stats)

        # Firewall API
        self.app.router.add_get('/api/firewall/stats', self.firewall_stats)
        self.app.router.add_get('/api/firewall/rules', self.firewall_rules)
        self.app.router.add_get('/api/firewall/blocked', self.firewall_blocked)
        self.app.router.add_post('/api/firewall/whitelist', self.firewall_add_whitelist)
        self.app.router.add_post('/api/firewall/blacklist', self.firewall_add_blacklist)
        self.app.router.add_delete('/api/firewall/whitelist', self.firewall_remove_whitelist)
        self.app.router.add_delete('/api/firewall/blacklist', self.firewall_remove_blacklist)

        # Enable CORS with restricted origins (security fix)
        # Only allow localhost by default - configure allowed_origins for production
        allowed_origins = getattr(self, 'allowed_origins', [
            "http://localhost:8080",
            "http://127.0.0.1:8080",
            f"http://localhost:{self.port}",
            f"http://127.0.0.1:{self.port}",
        ])

        cors_config = {}
        for origin in allowed_origins:
            cors_config[origin] = aiohttp_cors.ResourceOptions(
                allow_credentials=True,
                expose_headers=["Content-Type", "Authorization"],
                allow_headers=["Content-Type", "Authorization"],
                allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            )

        cors = aiohttp_cors.setup(self.app, defaults=cors_config)
        for route in list(self.app.router.routes()):
            cors.add(route)
    
    async def serve_dashboard(self, request):
        """Serve the HTML dashboard."""
        dashboard_path = Path(__file__).parent / 'dashboard.html'

        # If dashboard.html doesn't exist, return inline version
        if not dashboard_path.exists():
            html = self._get_inline_dashboard()
            return web.Response(text=html, content_type='text/html')

        return web.FileResponse(dashboard_path)

    async def serve_timeline(self, request):
        """Serve the timeline/Gantt chart page."""
        timeline_path = Path(__file__).parent / 'timeline.html'

        if not timeline_path.exists():
            return web.Response(
                text="<h1>Timeline not available</h1><p>timeline.html not found</p>",
                content_type='text/html'
            )

        return web.FileResponse(timeline_path)

    async def get_timeline_data(self, request):
        """Get project timeline data for Gantt chart visualization."""
        try:
            projects = []

            # Get GDIL projects
            if hasattr(self.orchestrator, 'gdil') and self.orchestrator.gdil:
                gdil = self.orchestrator.gdil
                for project_id, project in gdil.projects.items():
                    # Extract roadmap tasks
                    roadmap = project.get('roadmap', [])
                    tasks = []

                    for i, task in enumerate(roadmap):
                        task_data = {
                            'id': f"{project_id}_task_{i}",
                            'name': task.get('name', f'Task {i + 1}'),
                            'status': self._normalize_task_status(task, project),
                            'priority': task.get('priority', 3),
                            'dependencies': task.get('dependencies', []),
                            'progress': self._calculate_task_progress(task, project)
                        }
                        tasks.append(task_data)

                    # Get phase as string
                    phase = project.get('phase')
                    phase_str = phase.value if hasattr(phase, 'value') else str(phase)

                    project_data = {
                        'id': project_id,
                        'name': project.get('name', 'Unnamed Project'),
                        'phase': phase_str,
                        'roadmap': tasks,
                        'progress': project.get('progress_score', 0),
                        'is_collaborative': False,
                        'created_at': project.get('created_at', 0),
                        'updated_at': project.get('updated_at', 0)
                    }
                    projects.append(project_data)

            # Get collaborative projects
            if hasattr(self.orchestrator, 'collab') and self.orchestrator.collab:
                collab = self.orchestrator.collab
                for project_id, project in collab.projects.items():
                    tasks = []
                    for task in project.tasks:
                        task_data = {
                            'id': task.id,
                            'name': task.name,
                            'status': task.status.value if hasattr(task.status, 'value') else str(task.status),
                            'priority': task.priority,
                            'dependencies': task.depends_on,
                            'progress': 1.0 if task.status.value in ['approved', 'completed'] else 0.5 if task.status.value == 'in_progress' else 0.0,
                            'assigned_to': task.assigned_to
                        }
                        tasks.append(task_data)

                    project_data = {
                        'id': project_id,
                        'name': project.name,
                        'phase': 'active' if project.active else 'inactive',
                        'roadmap': tasks,
                        'progress': len([t for t in project.tasks if t.status.value in ['approved', 'completed']]) / max(len(project.tasks), 1),
                        'is_collaborative': True,
                        'created_at': project.created_at,
                        'coordinator': project.coordinator
                    }
                    projects.append(project_data)

            return web.json_response({
                'success': True,
                'projects': projects,
                'total_projects': len(projects)
            })

        except Exception as e:
            return web.json_response({
                'success': False,
                'error': str(e),
                'projects': []
            }, status=500)

    def _normalize_task_status(self, task: dict, project: dict) -> str:
        """Normalize task status for Gantt display."""
        completed_tasks = project.get('completed_tasks', [])
        current_task = project.get('current_subtask')

        task_name = task.get('name', '')

        # Check if task is completed
        if task_name in completed_tasks or task.get('completed', False):
            return 'completed'

        # Check if task is current
        if current_task and current_task.get('name') == task_name:
            return 'in_progress'

        # Check for explicit status
        if 'status' in task:
            return task['status']

        return 'pending'

    def _calculate_task_progress(self, task: dict, project: dict) -> float:
        """Calculate task progress for visualization."""
        completed_tasks = project.get('completed_tasks', [])
        current_task = project.get('current_subtask')

        task_name = task.get('name', '')

        if task_name in completed_tasks or task.get('completed', False):
            return 1.0

        if current_task and current_task.get('name') == task_name:
            return 0.5

        return 0.0

    async def websocket_handler(self, request):
        """Handle WebSocket connections for real-time updates."""
        ws = web.WebSocketResponse()
        await ws.prepare(request)
        self.websockets.add(ws)
        
        print(f"Dashboard connected: {len(self.websockets)} active connections")
        
        # Send initial state
        await self.send_state_update(ws)
        
        try:
            async for msg in ws:
                if msg.type == web.WSMsgType.TEXT:
                    data = json.loads(msg.data)
                    await self.handle_command(ws, data)
                elif msg.type == web.WSMsgType.ERROR:
                    print(f'WebSocket error: {ws.exception()}')
        finally:
            self.websockets.remove(ws)
            print(f"Dashboard disconnected: {len(self.websockets)} active connections")
        
        return ws
    
    async def handle_command(self, ws: web.WebSocketResponse, data: dict):
        """Handle commands from dashboard."""
        command = data.get('command')
        
        if command == 'simulate_turn':
            await self.simulate_turn(None)
        elif command == 'trigger_reflection':
            await self.trigger_reflection(None)
        elif command == 'get_state':
            await self.send_state_update(ws)
    
    async def get_state(self, request):
        """HTTP endpoint to get current state."""
        state = self.gather_state()
        return web.json_response(state)
    
    async def simulate_turn(self, request):
        """Simulate a conversation turn."""
        test_input = "This is a simulated user input for testing."
        await self.orchestrator._process_turn(test_input)
        
        # Broadcast updated state
        await self.broadcast_state()
        
        if request:
            return web.json_response({"success": True})
    
    async def trigger_reflection(self, request):
        """Force meta-reflection."""
        result = self.orchestrator.reflection.run_cycle(
            self.orchestrator._format_context(),
            self.orchestrator.emotion.current_state(),
            self.orchestrator._gather_metrics()
        )

        # Broadcast updated state
        await self.broadcast_state()

        if request:
            return web.json_response({"success": True, "result": result})

    async def peer_generate(self, request):
        """
        Peer-to-peer generation endpoint for social companionship.
        Compatible with the social companionship layer's expected API format.
        """
        try:
            data = await request.json()
            prompt = data.get('prompt', '')
            temperature = data.get('temperature', 0.85)
            max_tokens = data.get('max_tokens', 150)

            if not prompt:
                return web.json_response(
                    {"error": "No prompt provided"},
                    status=400
                )

            # Generate response using the orchestrator's LLM
            response_text = await self.orchestrator.llm.generate(
                prompt=prompt,
                temperature=temperature,
                max_tokens=max_tokens
            )

            return web.json_response({
                "response": response_text.strip(),
                "success": True
            })

        except Exception as e:
            return web.json_response(
                {"error": str(e), "success": False},
                status=500
            )

    async def chat_handler(self, request):
        """
        Process a chat message through the full cognitive pipeline.
        This runs dreaming, assurance, meta-reflection, and all psychological modules.
        """
        try:
            data = await request.json()
            message = data.get('message', '')

            if not message:
                return web.json_response(
                    {"error": "No message provided", "success": False},
                    status=400
                )

            # Process through full pipeline (dreaming, assurance, reflection, etc.)
            await self.orchestrator._process_turn(message)

            # Get the response (last assistant message in context)
            response = self.orchestrator.context[-1]["content"]

            # Gather current state
            emotion_state = self.orchestrator.emotion.current_state()

            # Broadcast state update to any connected dashboards
            await self.broadcast_state()

            return web.json_response({
                "success": True,
                "response": response,
                "state": {
                    "valence": emotion_state["valence"],
                    "mood_tags": emotion_state["tags"],
                    "turn_count": self.orchestrator.turn_count,
                    "dream_alignment": self.orchestrator.metrics.last_dream_alignment,
                    "flow_state": "flow" if 0.4 <= self.orchestrator.calibration.difficulty_moving_avg <= 0.7 else "bored" if self.orchestrator.calibration.difficulty_moving_avg < 0.4 else "overloaded"
                }
            })

        except Exception as e:
            return web.json_response(
                {"error": str(e), "success": False},
                status=500
            )

    async def federated_receive(self, request):
        """
        Receive federated learning update from a peer.
        Endpoint for privacy-preserving pattern sharing.
        """
        try:
            data = await request.json()

            # Check if social layer has federated learning enabled
            if hasattr(self.orchestrator, 'social') and self.orchestrator.social:
                result = await self.orchestrator.social.receive_federated_update(data)
                return web.json_response(result)
            else:
                return web.json_response({
                    "success": False,
                    "error": "Federated learning not available"
                }, status=503)

        except Exception as e:
            return web.json_response(
                {"error": str(e), "success": False},
                status=500
            )

    async def federated_stats(self, request):
        """Get federated learning statistics."""
        try:
            if hasattr(self.orchestrator, 'social') and self.orchestrator.social:
                stats = self.orchestrator.social.get_federated_stats()
                if stats:
                    return web.json_response({"success": True, "stats": stats})
                else:
                    return web.json_response({
                        "success": False,
                        "error": "Federated learning not enabled"
                    })
            else:
                return web.json_response({
                    "success": False,
                    "error": "Social layer not available"
                }, status=503)

        except Exception as e:
            return web.json_response(
                {"error": str(e), "success": False},
                status=500
            )

    async def collab_projects(self, request):
        """Get collaborative projects for sync."""
        try:
            if hasattr(self.orchestrator, 'collab') and self.orchestrator.collab:
                data = self.orchestrator.collab.get_sync_data()
                return web.json_response({"success": True, **data})
            else:
                return web.json_response({
                    "success": False,
                    "error": "Collaboration not available"
                }, status=503)
        except Exception as e:
            return web.json_response(
                {"error": str(e), "success": False},
                status=500
            )

    async def collab_sync(self, request):
        """Receive collaborative project sync from peer."""
        try:
            data = await request.json()

            if hasattr(self.orchestrator, 'collab') and self.orchestrator.collab:
                result = await self.orchestrator.collab.receive_sync(data)
                return web.json_response(result)
            else:
                return web.json_response({
                    "success": False,
                    "error": "Collaboration not available"
                }, status=503)
        except Exception as e:
            return web.json_response(
                {"error": str(e), "success": False},
                status=500
            )

    async def collab_stats(self, request):
        """Get collaboration statistics."""
        try:
            if hasattr(self.orchestrator, 'collab') and self.orchestrator.collab:
                stats = self.orchestrator.collab.get_stats()
                return web.json_response({"success": True, "stats": stats})
            else:
                return web.json_response({
                    "success": False,
                    "error": "Collaboration not available"
                }, status=503)
        except Exception as e:
            return web.json_response(
                {"error": str(e), "success": False},
                status=500
            )

    async def ratelimit_stats(self, request):
        """Get rate limiting statistics (admin only)."""
        # Check admin permission
        authorized, error = self._require_role(request, UserRole.ADMIN)
        if not authorized:
            return error

        if not self.rate_limit_enabled or not self.rate_limiter:
            return web.json_response({
                "success": True,
                "enabled": False,
                "message": "Rate limiting is disabled"
            })

        try:
            stats = self.rate_limiter.get_stats()
            return web.json_response({
                "success": True,
                **stats
            })
        except Exception as e:
            return web.json_response(
                {"error": str(e), "success": False},
                status=500
            )

    async def accesslog_stats(self, request):
        """Get access logging statistics (admin only)."""
        # Check admin permission
        authorized, error = self._require_role(request, UserRole.ADMIN)
        if not authorized:
            return error

        if not self.access_log_enabled or not self.access_logger:
            return web.json_response({
                "success": True,
                "enabled": False,
                "message": "Access logging is disabled"
            })

        try:
            stats = self.access_logger.get_stats()
            return web.json_response({
                "success": True,
                **stats
            })
        except Exception as e:
            return web.json_response(
                {"error": str(e), "success": False},
                status=500
            )

    async def firewall_stats(self, request):
        """Get firewall statistics (admin only)."""
        authorized, error = self._require_role(request, UserRole.ADMIN)
        if not authorized:
            return error

        if not self.firewall_enabled or not self.firewall:
            return web.json_response({
                "success": True,
                "enabled": False,
                "message": "Firewall is disabled"
            })

        try:
            stats = self.firewall.get_stats()
            return web.json_response({"success": True, **stats})
        except Exception as e:
            return web.json_response(
                {"error": str(e), "success": False},
                status=500
            )

    async def firewall_rules(self, request):
        """Get current firewall rules (admin only)."""
        authorized, error = self._require_role(request, UserRole.ADMIN)
        if not authorized:
            return error

        if not self.firewall_enabled or not self.firewall:
            return web.json_response({
                "success": True,
                "enabled": False,
                "message": "Firewall is disabled"
            })

        try:
            rules = self.firewall.get_rules()
            return web.json_response({"success": True, **rules})
        except Exception as e:
            return web.json_response(
                {"error": str(e), "success": False},
                status=500
            )

    async def firewall_blocked(self, request):
        """Get blocked request log (admin only)."""
        authorized, error = self._require_role(request, UserRole.ADMIN)
        if not authorized:
            return error

        if not self.firewall_enabled or not self.firewall:
            return web.json_response({
                "success": True,
                "enabled": False,
                "blocked": []
            })

        try:
            limit = int(request.query.get('limit', 100))
            blocked = self.firewall.get_blocked_log(limit)
            return web.json_response({
                "success": True,
                "blocked": blocked,
                "count": len(blocked)
            })
        except Exception as e:
            return web.json_response(
                {"error": str(e), "success": False},
                status=500
            )

    async def firewall_add_whitelist(self, request):
        """Add IP to whitelist (admin only)."""
        authorized, error = self._require_role(request, UserRole.ADMIN)
        if not authorized:
            return error

        if not self.firewall_enabled or not self.firewall:
            return web.json_response(
                {"error": "Firewall is disabled", "success": False},
                status=400
            )

        try:
            data = await request.json()
            ip = data.get('ip')
            if not ip:
                return web.json_response(
                    {"error": "IP address required", "success": False},
                    status=400
                )

            success = self.firewall.add_to_whitelist(ip)
            return web.json_response({
                "success": success,
                "message": f"Added {ip} to whitelist" if success else "Failed to add"
            })
        except Exception as e:
            return web.json_response(
                {"error": str(e), "success": False},
                status=500
            )

    async def firewall_add_blacklist(self, request):
        """Add IP to blacklist (admin only)."""
        authorized, error = self._require_role(request, UserRole.ADMIN)
        if not authorized:
            return error

        if not self.firewall_enabled or not self.firewall:
            return web.json_response(
                {"error": "Firewall is disabled", "success": False},
                status=400
            )

        try:
            data = await request.json()
            ip = data.get('ip')
            if not ip:
                return web.json_response(
                    {"error": "IP address required", "success": False},
                    status=400
                )

            success = self.firewall.add_to_blacklist(ip)
            return web.json_response({
                "success": success,
                "message": f"Added {ip} to blacklist" if success else "Failed to add"
            })
        except Exception as e:
            return web.json_response(
                {"error": str(e), "success": False},
                status=500
            )

    async def firewall_remove_whitelist(self, request):
        """Remove IP from whitelist (admin only)."""
        authorized, error = self._require_role(request, UserRole.ADMIN)
        if not authorized:
            return error

        if not self.firewall_enabled or not self.firewall:
            return web.json_response(
                {"error": "Firewall is disabled", "success": False},
                status=400
            )

        try:
            data = await request.json()
            ip = data.get('ip')
            if not ip:
                return web.json_response(
                    {"error": "IP address required", "success": False},
                    status=400
                )

            success = self.firewall.remove_from_whitelist(ip)
            return web.json_response({
                "success": success,
                "message": f"Removed {ip} from whitelist" if success else "Failed to remove"
            })
        except Exception as e:
            return web.json_response(
                {"error": str(e), "success": False},
                status=500
            )

    async def firewall_remove_blacklist(self, request):
        """Remove IP from blacklist (admin only)."""
        authorized, error = self._require_role(request, UserRole.ADMIN)
        if not authorized:
            return error

        if not self.firewall_enabled or not self.firewall:
            return web.json_response(
                {"error": "Firewall is disabled", "success": False},
                status=400
            )

        try:
            data = await request.json()
            ip = data.get('ip')
            if not ip:
                return web.json_response(
                    {"error": "IP address required", "success": False},
                    status=400
                )

            success = self.firewall.remove_from_blacklist(ip)
            return web.json_response({
                "success": success,
                "message": f"Removed {ip} from blacklist" if success else "Failed to remove"
            })
        except Exception as e:
            return web.json_response(
                {"error": str(e), "success": False},
                status=500
            )

    # =========================================================================
    # Authentication Middleware & Endpoints
    # =========================================================================

    @web.middleware
    async def _auth_middleware(self, request, handler):
        """JWT authentication middleware."""
        # Skip auth for public paths
        if any(request.path.startswith(p) for p in self.PUBLIC_PATHS):
            return await handler(request)

        # Skip if auth is disabled
        if not self.auth_enabled or not self.auth:
            return await handler(request)

        # Extract token from Authorization header
        auth_header = request.headers.get('Authorization', '')

        if not auth_header.startswith('Bearer '):
            return web.json_response(
                {"error": "Missing or invalid authorization header"},
                status=401
            )

        token = auth_header[7:]  # Remove 'Bearer ' prefix
        valid, payload = self.auth.validate_token(token)

        if not valid:
            return web.json_response(
                {"error": "Invalid or expired token"},
                status=401
            )

        # Add user info to request
        request['user'] = payload
        return await handler(request)

    def _get_token_from_request(self, request) -> Optional[str]:
        """Extract token from Authorization header."""
        auth_header = request.headers.get('Authorization', '')
        if auth_header.startswith('Bearer '):
            return auth_header[7:]
        return None

    def _require_role(self, request, required_role: UserRole) -> tuple:
        """
        Check if request has required role.
        Returns (authorized, error_response or None)
        """
        if not self.auth_enabled or not self.auth:
            return True, None

        token = self._get_token_from_request(request)
        if not token:
            return False, web.json_response(
                {"error": "Authentication required"},
                status=401
            )

        authorized, _ = self.auth.check_permission(token, required_role)
        if not authorized:
            return False, web.json_response(
                {"error": "Insufficient permissions"},
                status=403
            )

        return True, None

    async def auth_status(self, request):
        """Get authentication status and requirements."""
        if not self.auth_enabled:
            return web.json_response({
                "enabled": False,
                "setup_required": False,
                "message": "Authentication disabled"
            })

        return web.json_response({
            "enabled": True,
            "setup_required": self.auth.get_setup_required(),
            "message": "Setup required" if self.auth.get_setup_required() else "Ready"
        })

    async def auth_setup(self, request):
        """Initial admin setup (only works if no admin exists)."""
        if not self.auth_enabled or not self.auth:
            return web.json_response(
                {"error": "Authentication not enabled"},
                status=400
            )

        if not self.auth.get_setup_required():
            return web.json_response(
                {"error": "Setup already completed"},
                status=400
            )

        try:
            data = await request.json()
            username = data.get('username')
            password = data.get('password')

            if not username or not password:
                return web.json_response(
                    {"error": "Username and password required"},
                    status=400
                )

            success, message = self.auth.setup_initial_admin(username, password)

            if success:
                # Auto-login after setup
                _, tokens = self.auth.authenticate(username, password)
                return web.json_response({
                    "success": True,
                    "message": message,
                    **tokens
                })
            else:
                return web.json_response(
                    {"error": message},
                    status=400
                )

        except Exception as e:
            return web.json_response(
                {"error": str(e)},
                status=500
            )

    async def auth_login(self, request):
        """Authenticate and get tokens."""
        if not self.auth_enabled or not self.auth:
            return web.json_response({
                "success": True,
                "message": "Authentication disabled - access granted"
            })

        try:
            data = await request.json()
            username = data.get('username')
            password = data.get('password')

            if not username or not password:
                return web.json_response(
                    {"error": "Username and password required"},
                    status=400
                )

            success, tokens = self.auth.authenticate(username, password)

            if success:
                return web.json_response({
                    "success": True,
                    **tokens
                })
            else:
                return web.json_response(
                    {"error": "Invalid credentials"},
                    status=401
                )

        except Exception as e:
            return web.json_response(
                {"error": str(e)},
                status=500
            )

    async def auth_logout(self, request):
        """Logout and blacklist token."""
        if not self.auth_enabled or not self.auth:
            return web.json_response({"success": True})

        token = self._get_token_from_request(request)
        if token:
            self.auth.logout(token)

        return web.json_response({
            "success": True,
            "message": "Logged out successfully"
        })

    async def auth_refresh(self, request):
        """Refresh access token."""
        if not self.auth_enabled or not self.auth:
            return web.json_response({
                "success": True,
                "message": "Authentication disabled"
            })

        try:
            data = await request.json()
            refresh_token = data.get('refresh_token')

            if not refresh_token:
                return web.json_response(
                    {"error": "Refresh token required"},
                    status=400
                )

            success, new_tokens = self.auth.refresh_access_token(refresh_token)

            if success:
                return web.json_response({
                    "success": True,
                    **new_tokens
                })
            else:
                return web.json_response(
                    {"error": "Invalid or expired refresh token"},
                    status=401
                )

        except Exception as e:
            return web.json_response(
                {"error": str(e)},
                status=500
            )

    # =========================================================================
    # User Management Endpoints (Admin only)
    # =========================================================================

    async def list_users(self, request):
        """List all users (admin only)."""
        authorized, error = self._require_role(request, UserRole.ADMIN)
        if not authorized:
            return error

        if not self.auth:
            return web.json_response({"users": []})

        return web.json_response({
            "success": True,
            "users": self.auth.list_users()
        })

    async def create_user(self, request):
        """Create new user (admin only)."""
        authorized, error = self._require_role(request, UserRole.ADMIN)
        if not authorized:
            return error

        if not self.auth:
            return web.json_response(
                {"error": "Authentication not available"},
                status=503
            )

        try:
            data = await request.json()
            username = data.get('username')
            password = data.get('password')
            role = data.get('role', 'viewer')

            if not username or not password:
                return web.json_response(
                    {"error": "Username and password required"},
                    status=400
                )

            try:
                user_role = UserRole(role)
            except ValueError:
                return web.json_response(
                    {"error": f"Invalid role. Must be: admin, operator, or viewer"},
                    status=400
                )

            success, message = self.auth.create_user(username, password, user_role)

            if success:
                return web.json_response({
                    "success": True,
                    "message": message
                })
            else:
                return web.json_response(
                    {"error": message},
                    status=400
                )

        except Exception as e:
            return web.json_response(
                {"error": str(e)},
                status=500
            )

    async def delete_user(self, request):
        """Delete user (admin only)."""
        authorized, error = self._require_role(request, UserRole.ADMIN)
        if not authorized:
            return error

        if not self.auth:
            return web.json_response(
                {"error": "Authentication not available"},
                status=503
            )

        username = request.match_info['username']
        success, message = self.auth.delete_user(username)

        if success:
            return web.json_response({
                "success": True,
                "message": message
            })
        else:
            return web.json_response(
                {"error": message},
                status=404
            )

    async def update_password(self, request):
        """Update user password (admin only)."""
        authorized, error = self._require_role(request, UserRole.ADMIN)
        if not authorized:
            return error

        if not self.auth:
            return web.json_response(
                {"error": "Authentication not available"},
                status=503
            )

        try:
            username = request.match_info['username']
            data = await request.json()
            new_password = data.get('password')

            if not new_password:
                return web.json_response(
                    {"error": "New password required"},
                    status=400
                )

            success, message = self.auth.update_password(username, new_password)

            if success:
                return web.json_response({
                    "success": True,
                    "message": message
                })
            else:
                return web.json_response(
                    {"error": message},
                    status=400
                )

        except Exception as e:
            return web.json_response(
                {"error": str(e)},
                status=500
            )

    async def update_role(self, request):
        """Update user role (admin only)."""
        authorized, error = self._require_role(request, UserRole.ADMIN)
        if not authorized:
            return error

        if not self.auth:
            return web.json_response(
                {"error": "Authentication not available"},
                status=503
            )

        try:
            username = request.match_info['username']
            data = await request.json()
            role = data.get('role')

            if not role:
                return web.json_response(
                    {"error": "Role required"},
                    status=400
                )

            try:
                user_role = UserRole(role)
            except ValueError:
                return web.json_response(
                    {"error": f"Invalid role. Must be: admin, operator, or viewer"},
                    status=400
                )

            success, message = self.auth.update_role(username, user_role)

            if success:
                return web.json_response({
                    "success": True,
                    "message": message
                })
            else:
                return web.json_response(
                    {"error": message},
                    status=400
                )

        except Exception as e:
            return web.json_response(
                {"error": str(e)},
                status=500
            )

    def gather_state(self) -> dict:
        """Gather complete internal state."""
        emotion_state = self.orchestrator.emotion.current_state()
        metrics = self.orchestrator._gather_metrics()
        calib_state = {
            "current_difficulty": self.orchestrator.calibration.difficulty_moving_avg,
            "temperature": self.orchestrator.calibration.creativity_temperature,
            "persistence": self.orchestrator.calibration.persistence_factor,
            "rejection_threshold": self.orchestrator.calibration.rejection_threshold
        }
        
        # Determine flow state
        difficulty = self.orchestrator.calibration.difficulty_moving_avg
        if difficulty < 0.4:
            flow_state = "bored"
        elif difficulty > 0.7:
            flow_state = "overloaded"
        else:
            flow_state = "flow"
        
        state = {
            "timestamp": datetime.now().isoformat(),
            "turn_count": self.orchestrator.turn_count,
            
            # Emotional state
            "valence": emotion_state['valence'],
            "mood_tags": emotion_state['tags'],
            
            # Predictive dreaming
            "dream_alignment": self.orchestrator.metrics.last_dream_alignment,
            "dream_buffer_size": len(self.orchestrator.dreaming.dream_buffer),
            "dream_buffer": [
                {
                    "text": d["text"][:80] + "..." if len(d["text"]) > 80 else d["text"],
                    "probability": d["prob"]
                }
                for d in self.orchestrator.dreaming.dream_buffer[:5]
            ],
            
            # Flow calibration
            "difficulty": calib_state["current_difficulty"],
            "flow_state": flow_state,
            "temperature": calib_state["temperature"],
            "persistence": calib_state["persistence"],
            
            # Assurance
            "uncertainty": self.orchestrator.metrics.avg_uncertainty(n=5),
            "pending_concerns": len(self.orchestrator.assurance.pending_concerns),
            "assurance_success_rate": metrics['assurance_success'],
            
            # Meta-reflection
            "coherence": 0.85 + (self.orchestrator.emotion.current_valence * 0.1),
            "next_reflection": self.orchestrator.reflection.reflection_interval - 
                             (self.orchestrator.turn_count % self.orchestrator.reflection.reflection_interval),
            "total_insights": self.orchestrator.reflection.turn_counter // 10,
            
            # Temporal purpose
            "sessions_completed": self.orchestrator.temporal.purpose_metrics["sessions_completed"],
            "growth_delta": self.orchestrator.temporal.purpose_metrics["growth_delta"],
            "narrative": self.orchestrator.temporal.current_narrative_summary(),
            
            # Performance metrics
            "metrics": {
                "predictive_alignment": metrics['predictive_alignment'],
                "user_sentiment": metrics['user_sentiment']
            },

            # Project status (if active)
            "project": self._get_project_state()
        }

        return state

    def _get_project_state(self) -> dict:
        """Get current project status for dashboard."""
        if not self.orchestrator.gdil or not self.orchestrator.gdil.active_project:
            return None

        project = self.orchestrator.gdil.active_project
        phase = project.get("phase")
        phase_value = phase.value if hasattr(phase, 'value') else str(phase)

        return {
            "id": project.get("id"),
            "name": project.get("name", "Unnamed"),
            "phase": phase_value,
            "brief": project.get("brief", "In progress"),
            "progress": project.get("progress_score", 0),
            "iterations": len(project.get("iterations", [])),
            "completed_tasks": len(project.get("completed_tasks", [])),
            "total_tasks": len(project.get("roadmap", [])),
            "current_subtask": project.get("current_subtask", {}).get("name", "None") if project.get("current_subtask") else "None",
            "total_projects": len(self.orchestrator.gdil.projects)
        }
    
    async def send_state_update(self, ws: web.WebSocketResponse):
        """Send state update to specific WebSocket."""
        state = self.gather_state()
        await ws.send_json({
            "type": "state_update",
            "data": state
        })
    
    async def broadcast_state(self):
        """Broadcast state to all connected WebSockets."""
        if not self.websockets:
            return
        
        state = self.gather_state()
        message = json.dumps({
            "type": "state_update",
            "data": state
        })
        
        # Send to all connected clients
        dead_sockets = set()
        for ws in self.websockets:
            try:
                await ws.send_str(message)
            except Exception:
                dead_sockets.add(ws)
        
        # Clean up dead connections
        self.websockets -= dead_sockets
    
    def _get_inline_dashboard(self) -> str:
        """Return inline HTML dashboard if file doesn't exist."""
        return """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Synth Mind Dashboard</title>
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            color: #e4e4e4;
            padding: 20px;
            margin: 0;
        }
        .container { max-width: 1200px; margin: 0 auto; }
        h1 { text-align: center; color: #667eea; }
        .status { padding: 20px; background: rgba(255,255,255,0.05); border-radius: 10px; margin: 20px 0; }
        .metric { display: flex; justify-content: space-between; padding: 10px 0; border-bottom: 1px solid rgba(255,255,255,0.1); }
        button { padding: 10px 20px; margin: 5px; background: #667eea; color: white; border: none; border-radius: 5px; cursor: pointer; }
        button:hover { background: #764ba2; }
        .ws-status { color: #4ade80; }
        .ws-status.disconnected { color: #ef4444; }
    </style>
</head>
<body>
    <div class="container">
        <h1>🔮 Synth Mind Dashboard</h1>
        <div class="status">
            <div class="metric">
                <span>WebSocket Status:</span>
                <span class="ws-status" id="ws-status">Connecting...</span>
            </div>
            <div class="metric">
                <span>Emotional Valence:</span>
                <span id="valence">--</span>
            </div>
            <div class="metric">
                <span>Dream Alignment:</span>
                <span id="dream-alignment">--</span>
            </div>
            <div class="metric">
                <span>Flow State:</span>
                <span id="flow-state">--</span>
            </div>
            <div class="metric">
                <span>Turn Count:</span>
                <span id="turn-count">--</span>
            </div>
        </div>
        <div style="text-align: center;">
            <button onclick="simulateTurn()">Simulate Turn</button>
            <button onclick="triggerReflection()">Trigger Reflection</button>
        </div>
        <div class="status">
            <h3>Current Narrative</h3>
            <p id="narrative">Loading...</p>
        </div>
    </div>
    <script>
        let ws;

        function connect() {
            // Use WSS for HTTPS, WS for HTTP
            const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
            ws = new WebSocket(`${wsProtocol}//${window.location.host}/ws`);
            
            ws.onopen = () => {
                document.getElementById('ws-status').textContent = 'Connected';
                document.getElementById('ws-status').className = 'ws-status';
            };
            
            ws.onclose = () => {
                document.getElementById('ws-status').textContent = 'Disconnected';
                document.getElementById('ws-status').className = 'ws-status disconnected';
                setTimeout(connect, 3000);
            };
            
            ws.onmessage = (event) => {
                const msg = JSON.parse(event.data);
                if (msg.type === 'state_update') {
                    updateUI(msg.data);
                }
            };
        }
        
        function updateUI(state) {
            document.getElementById('valence').textContent = state.valence >= 0 ? 
                `+${state.valence.toFixed(2)}` : state.valence.toFixed(2);
            document.getElementById('dream-alignment').textContent = state.dream_alignment.toFixed(2);
            document.getElementById('flow-state').textContent = state.flow_state.toUpperCase();
            document.getElementById('turn-count').textContent = state.turn_count;
            document.getElementById('narrative').textContent = state.narrative;
        }
        
        function simulateTurn() {
            ws.send(JSON.stringify({command: 'simulate_turn'}));
        }
        
        function triggerReflection() {
            ws.send(JSON.stringify({command: 'trigger_reflection'}));
        }
        
        connect();
    </script>
</body>
</html>
        """
    
    async def start_background_broadcast(self):
        """Background task to periodically broadcast state."""
        while True:
            await asyncio.sleep(2)  # Broadcast every 2 seconds
            if self.websockets and self.orchestrator.running:
                await self.broadcast_state()
    
    async def start(self):
        """Start the server with optional HTTPS/WSS support."""
        # Start background broadcaster
        asyncio.create_task(self.start_background_broadcast())

        # Start web server
        runner = web.AppRunner(self.app)
        await runner.setup()

        # Use SSL if configured
        if self.ssl_context:
            site = web.TCPSite(
                runner,
                'localhost',
                self.port,
                ssl_context=self.ssl_context
            )
            protocol = "https"
            ws_protocol = "wss"
        else:
            site = web.TCPSite(runner, 'localhost', self.port)
            protocol = "http"
            ws_protocol = "ws"

        await site.start()

        print(f"\n{'='*60}")
        print(f"  Dashboard server running at {protocol}://localhost:{self.port}")
        if self.is_https:
            print(f"  WebSocket endpoint: {ws_protocol}://localhost:{self.port}/ws")
            print(f"  TLS: ENABLED (TLS 1.2+)")
            if self.ssl_cert:
                print(f"  Certificate: {self.ssl_cert}")
        print(f"{'='*60}")

        # Show authentication status
        if self.auth_enabled and self.auth:
            if self.auth.get_setup_required():
                print(f"  Authentication: ENABLED (setup required)")
                print(f"  POST /api/auth/setup to create admin user")
            else:
                print(f"  Authentication: ENABLED")
                print(f"  POST /api/auth/login to authenticate")
        else:
            print(f"  Authentication: DISABLED")

        # Show rate limiting status
        if self.rate_limit_enabled and self.rate_limiter:
            config = self.rate_limiter.config
            print(f"  Rate Limiting: ENABLED")
            print(f"    - Auth endpoints: {config.strict_limit}/min")
            print(f"    - API endpoints: {config.standard_limit}/min")
            print(f"    - Read-only: {config.relaxed_limit}/min")
        else:
            print(f"  Rate Limiting: DISABLED")

        # Show access logging status
        if self.access_log_enabled and self.access_logger:
            config = self.access_logger.config
            print(f"  Access Logging: ENABLED")
            print(f"    - Format: {config.format.value}")
            if config.log_to_file:
                print(f"    - Log file: {config.log_file}")
            if config.log_to_stdout:
                print(f"    - Stdout: enabled")
        else:
            print(f"  Access Logging: DISABLED")

        # Show firewall status
        if self.firewall_enabled and self.firewall:
            config = self.firewall.config
            print(f"  IP Firewall: ENABLED")
            print(f"    - Mode: {config.mode.value}")
            stats = self.firewall.get_stats()
            print(f"    - Whitelist rules: {stats['whitelist_rules']}")
            print(f"    - Blacklist rules: {stats['blacklist_rules']}")
            print(f"    - Peer IPs: {stats['peer_ips']}")
        else:
            print(f"  IP Firewall: DISABLED")

        print(f"{'='*60}\n")

        # Keep server running
        try:
            await asyncio.Event().wait()
        except KeyboardInterrupt:
            await runner.cleanup()


async def main():
    """Main entry point for dashboard server."""
    import argparse

    parser = argparse.ArgumentParser(description='Synth Mind Dashboard Server')
    parser.add_argument('--port', type=int, default=8080, help='Server port (default: 8080)')
    parser.add_argument('--no-auth', action='store_true', help='Disable authentication')

    # SSL/TLS options
    ssl_group = parser.add_argument_group('SSL/TLS Options')
    ssl_group.add_argument('--ssl-cert', type=str, help='Path to SSL certificate file')
    ssl_group.add_argument('--ssl-key', type=str, help='Path to SSL private key file')
    ssl_group.add_argument('--ssl-dev', action='store_true',
                          help='Generate/use self-signed certificate for development')

    # Rate limiting options
    rate_group = parser.add_argument_group('Rate Limiting Options')
    rate_group.add_argument('--no-rate-limit', action='store_true',
                           help='Disable rate limiting')
    rate_group.add_argument('--rate-limit-auth', type=int, default=5,
                           help='Rate limit for auth endpoints (default: 5/min)')
    rate_group.add_argument('--rate-limit-api', type=int, default=60,
                           help='Rate limit for API endpoints (default: 60/min)')
    rate_group.add_argument('--rate-limit-window', type=int, default=60,
                           help='Rate limit window in seconds (default: 60)')

    # Access logging options
    log_group = parser.add_argument_group('Access Logging Options')
    log_group.add_argument('--no-access-log', action='store_true',
                          help='Disable access logging')
    log_group.add_argument('--access-log-file', type=str, default='state/access.log',
                          help='Access log file path (default: state/access.log)')
    log_group.add_argument('--access-log-format', type=str, default='json',
                          choices=['json', 'common', 'combined', 'simple'],
                          help='Access log format (default: json)')
    log_group.add_argument('--access-log-stdout', action='store_true',
                          help='Also log to stdout')

    # Firewall options
    fw_group = parser.add_argument_group('IP Firewall Options')
    fw_group.add_argument('--firewall', action='store_true',
                         help='Enable IP firewall')
    fw_group.add_argument('--firewall-mode', type=str, default='blacklist',
                         choices=['whitelist', 'blacklist', 'peers_only'],
                         help='Firewall mode (default: blacklist)')
    fw_group.add_argument('--firewall-whitelist', type=str, nargs='*',
                         help='IPs to whitelist (space-separated)')
    fw_group.add_argument('--firewall-blacklist', type=str, nargs='*',
                         help='IPs to blacklist (space-separated)')
    fw_group.add_argument('--firewall-peers-file', type=str, default='config/peers.txt',
                         help='Peers file for peers_only mode')

    args = parser.parse_args()

    # Handle SSL configuration
    ssl_cert = args.ssl_cert
    ssl_key = args.ssl_key

    # Generate development certificates if requested
    if args.ssl_dev:
        try:
            from utils.ssl_utils import get_or_create_dev_certs
            ssl_cert, ssl_key = get_or_create_dev_certs()
            print("\nUsing development SSL certificates (self-signed)")
            print("Note: You may need to accept the certificate in your browser\n")
        except ImportError as e:
            print(f"Warning: Could not generate dev certificates: {e}")
            print("Install cryptography: pip install cryptography")
            ssl_cert = ssl_key = None

    # Validate SSL arguments
    if (ssl_cert and not ssl_key) or (ssl_key and not ssl_cert):
        parser.error("Both --ssl-cert and --ssl-key are required for HTTPS")

    # Configure rate limiting
    rate_limit_config = None
    if not args.no_rate_limit:
        rate_limit_config = RateLimitConfig(
            strict_limit=args.rate_limit_auth,
            standard_limit=args.rate_limit_api,
            relaxed_limit=args.rate_limit_api * 2,  # Double for read-only
            window_seconds=args.rate_limit_window,
            enabled=True
        )

    # Configure access logging
    access_log_config = None
    if not args.no_access_log:
        format_map = {
            'json': LogFormat.JSON,
            'common': LogFormat.COMMON,
            'combined': LogFormat.COMBINED,
            'simple': LogFormat.SIMPLE,
        }
        access_log_config = AccessLogConfig(
            enabled=True,
            format=format_map[args.access_log_format],
            log_file=args.access_log_file,
            log_to_file=True,
            log_to_stdout=args.access_log_stdout,
        )

    # Configure IP firewall
    firewall_config = None
    if args.firewall:
        mode_map = {
            'whitelist': FirewallMode.WHITELIST,
            'blacklist': FirewallMode.BLACKLIST,
            'peers_only': FirewallMode.PEERS_ONLY,
        }
        firewall_config = FirewallConfig(
            mode=mode_map[args.firewall_mode],
            whitelist=args.firewall_whitelist or [],
            blacklist=args.firewall_blacklist or [],
            peers_file=args.firewall_peers_file,
        )

    print("Initializing Synth Mind with dashboard...")

    # Initialize orchestrator
    orchestrator = SynthOrchestrator()
    await orchestrator.initialize()

    # Create and start dashboard server
    server = DashboardServer(
        orchestrator,
        port=args.port,
        auth_enabled=not args.no_auth,
        ssl_cert=ssl_cert,
        ssl_key=ssl_key,
        rate_limit_enabled=not args.no_rate_limit,
        rate_limit_config=rate_limit_config,
        access_log_enabled=not args.no_access_log,
        access_log_config=access_log_config,
        firewall_enabled=args.firewall,
        firewall_config=firewall_config
    )

    # Start both server and orchestrator
    await asyncio.gather(
        server.start(),
        # Keep orchestrator ready (not in conversation loop, just monitoring)
    )


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nShutting down dashboard server...")
