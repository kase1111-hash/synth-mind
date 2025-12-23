"""
Dashboard Server - WebSocket server for real-time state streaming.
Serves the HTML dashboard and broadcasts internal state updates.
Includes JWT authentication for production security.
"""

import asyncio
import json
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
    print("Installing required packages...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "aiohttp", "aiohttp-cors"])
    from aiohttp import web
    import aiohttp_cors

from core.orchestrator import SynthOrchestrator
from utils.auth import AuthManager, UserRole

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
                 auth_enabled: bool = True):
        self.orchestrator = orchestrator
        self.port = port
        self.auth_enabled = auth_enabled
        self.websockets: Set[web.WebSocketResponse] = set()
        self.state_cache = {}

        # Initialize authentication
        self.auth = AuthManager() if auth_enabled else None

        # Create app with middleware
        if auth_enabled:
            self.app = web.Application(middlewares=[self._auth_middleware])
        else:
            self.app = web.Application()

        # Setup routes
        self._setup_routes()
        
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

        # Enable CORS
        cors = aiohttp_cors.setup(self.app, defaults={
            "*": aiohttp_cors.ResourceOptions(
                allow_credentials=True,
                expose_headers="*",
                allow_headers="*",
            )
        })
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
            ws = new WebSocket(`ws://${window.location.host}/ws`);
            
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
        """Start the server."""
        # Start background broadcaster
        asyncio.create_task(self.start_background_broadcast())

        # Start web server
        runner = web.AppRunner(self.app)
        await runner.setup()
        site = web.TCPSite(runner, 'localhost', self.port)
        await site.start()

        print(f"\n{'='*60}")
        print(f"  Dashboard server running at http://localhost:{self.port}")
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
    args = parser.parse_args()

    print("Initializing Synth Mind with dashboard...")

    # Initialize orchestrator
    orchestrator = SynthOrchestrator()
    await orchestrator.initialize()

    # Create and start dashboard server
    server = DashboardServer(
        orchestrator,
        port=args.port,
        auth_enabled=not args.no_auth
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
