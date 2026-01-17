"""
Prometheus Metrics for Synth Mind

Provides metrics in Prometheus exposition format for monitoring and alerting.
Tracks request rates, latencies, cognitive module states, and system health.
"""

import time
from collections import defaultdict
from dataclasses import dataclass, field
from threading import Lock


@dataclass
class MetricValue:
    """A single metric value with optional labels."""
    value: float
    labels: dict[str, str] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)


class Counter:
    """Prometheus-style counter (monotonically increasing)."""

    def __init__(self, name: str, help_text: str, labels: list[str] = None):
        self.name = name
        self.help_text = help_text
        self.label_names = labels or []
        self._values: dict[tuple, float] = defaultdict(float)
        self._lock = Lock()

    def inc(self, value: float = 1, **labels):
        """Increment counter by value."""
        label_key = tuple(sorted(labels.items()))
        with self._lock:
            self._values[label_key] += value

    def get(self, **labels) -> float:
        """Get current counter value."""
        label_key = tuple(sorted(labels.items()))
        return self._values.get(label_key, 0)

    def collect(self) -> list[MetricValue]:
        """Collect all metric values."""
        with self._lock:
            return [
                MetricValue(value=v, labels=dict(k))
                for k, v in self._values.items()
            ]


class Gauge:
    """Prometheus-style gauge (can go up and down)."""

    def __init__(self, name: str, help_text: str, labels: list[str] = None):
        self.name = name
        self.help_text = help_text
        self.label_names = labels or []
        self._values: dict[tuple, float] = {}
        self._lock = Lock()

    def set(self, value: float, **labels):
        """Set gauge to value."""
        label_key = tuple(sorted(labels.items()))
        with self._lock:
            self._values[label_key] = value

    def inc(self, value: float = 1, **labels):
        """Increment gauge by value."""
        label_key = tuple(sorted(labels.items()))
        with self._lock:
            self._values[label_key] = self._values.get(label_key, 0) + value

    def dec(self, value: float = 1, **labels):
        """Decrement gauge by value."""
        self.inc(-value, **labels)

    def get(self, **labels) -> float:
        """Get current gauge value."""
        label_key = tuple(sorted(labels.items()))
        return self._values.get(label_key, 0)

    def collect(self) -> list[MetricValue]:
        """Collect all metric values."""
        with self._lock:
            return [
                MetricValue(value=v, labels=dict(k))
                for k, v in self._values.items()
            ]


class Histogram:
    """Prometheus-style histogram for latency tracking."""

    DEFAULT_BUCKETS = (0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1, 2.5, 5, 10)

    def __init__(self, name: str, help_text: str,
                 labels: list[str] = None, buckets: tuple = None):
        self.name = name
        self.help_text = help_text
        self.label_names = labels or []
        self.buckets = buckets or self.DEFAULT_BUCKETS
        self._counts: dict[tuple, dict[float, int]] = defaultdict(
            lambda: dict.fromkeys(self.buckets, 0)
        )
        self._sums: dict[tuple, float] = defaultdict(float)
        self._totals: dict[tuple, int] = defaultdict(int)
        self._lock = Lock()

    def observe(self, value: float, **labels):
        """Record an observation."""
        label_key = tuple(sorted(labels.items()))
        with self._lock:
            self._sums[label_key] += value
            self._totals[label_key] += 1
            for bucket in self.buckets:
                if value <= bucket:
                    self._counts[label_key][bucket] += 1

    def collect(self) -> list[MetricValue]:
        """Collect all metric values."""
        results = []
        with self._lock:
            for label_key, counts in self._counts.items():
                labels = dict(label_key)
                # Bucket counts
                cumulative = 0
                for bucket in self.buckets:
                    cumulative += counts[bucket]
                    results.append(MetricValue(
                        value=cumulative,
                        labels={**labels, 'le': str(bucket)}
                    ))
                # +Inf bucket
                results.append(MetricValue(
                    value=self._totals[label_key],
                    labels={**labels, 'le': '+Inf'}
                ))
            # Sum and count
            for label_key in self._sums:
                labels = dict(label_key)
                results.append(MetricValue(
                    value=self._sums[label_key],
                    labels={**labels, '_type': 'sum'}
                ))
                results.append(MetricValue(
                    value=self._totals[label_key],
                    labels={**labels, '_type': 'count'}
                ))
        return results


class PrometheusMetrics:
    """
    Central metrics registry for Synth Mind.

    Tracks:
    - HTTP request metrics (count, latency)
    - Cognitive module states (valence, flow, coherence)
    - System health (memory, connections)
    - Project metrics (active, completed)
    """

    def __init__(self):
        # HTTP metrics
        self.http_requests_total = Counter(
            'synth_http_requests_total',
            'Total HTTP requests',
            ['method', 'endpoint', 'status']
        )
        self.http_request_duration_seconds = Histogram(
            'synth_http_request_duration_seconds',
            'HTTP request latency',
            ['method', 'endpoint']
        )

        # WebSocket metrics
        self.websocket_connections = Gauge(
            'synth_websocket_connections',
            'Active WebSocket connections'
        )

        # Cognitive state metrics
        self.emotional_valence = Gauge(
            'synth_emotional_valence',
            'Current emotional valence (-1 to 1)'
        )
        self.flow_state = Gauge(
            'synth_flow_state',
            'Flow state (0=bored, 0.5=flow, 1=overloaded)'
        )
        self.coherence_score = Gauge(
            'synth_coherence_score',
            'Meta-reflection coherence score'
        )
        self.dream_alignment = Gauge(
            'synth_dream_alignment',
            'Predictive dreaming alignment score'
        )
        self.uncertainty_level = Gauge(
            'synth_uncertainty_level',
            'Current uncertainty gauge'
        )

        # Conversation metrics
        self.turns_total = Counter(
            'synth_turns_total',
            'Total conversation turns processed'
        )
        self.llm_requests_total = Counter(
            'synth_llm_requests_total',
            'Total LLM API requests',
            ['provider']
        )
        self.llm_request_duration_seconds = Histogram(
            'synth_llm_request_duration_seconds',
            'LLM request latency',
            ['provider']
        )

        # Project metrics
        self.active_projects = Gauge(
            'synth_active_projects',
            'Number of active GDIL projects'
        )
        self.completed_projects = Counter(
            'synth_completed_projects_total',
            'Total completed projects'
        )
        self.project_iterations = Counter(
            'synth_project_iterations_total',
            'Total project iterations'
        )

        # Memory metrics
        self.memory_episodes = Gauge(
            'synth_memory_episodes',
            'Number of episodic memories'
        )
        self.memory_semantic = Gauge(
            'synth_memory_semantic',
            'Number of semantic memories'
        )

        # Authentication metrics
        self.auth_attempts_total = Counter(
            'synth_auth_attempts_total',
            'Authentication attempts',
            ['result']
        )

        # System info
        self.info = Gauge(
            'synth_info',
            'Synth Mind version info',
            ['version']
        )
        self.info.set(1, version='0.1.0-alpha')

    def format_prometheus(self) -> str:
        """Format all metrics in Prometheus exposition format."""
        lines = []

        # Helper to format a metric
        def format_metric(metric, suffix=''):
            metric_name = metric.name + suffix
            lines.append(f'# HELP {metric_name} {metric.help_text}')

            if isinstance(metric, Counter):
                lines.append(f'# TYPE {metric_name} counter')
            elif isinstance(metric, Gauge):
                lines.append(f'# TYPE {metric_name} gauge')
            elif isinstance(metric, Histogram):
                lines.append(f'# TYPE {metric_name} histogram')

            for mv in metric.collect():
                if mv.labels:
                    # Handle histogram special labels
                    if '_type' in mv.labels:
                        label_type = mv.labels.pop('_type')
                        label_str = ','.join(
                            f'{k}="{v}"' for k, v in mv.labels.items()
                        )
                        if label_str:
                            lines.append(
                                f'{metric_name}_{label_type}{{{label_str}}} {mv.value}'
                            )
                        else:
                            lines.append(f'{metric_name}_{label_type} {mv.value}')
                    else:
                        label_str = ','.join(
                            f'{k}="{v}"' for k, v in mv.labels.items()
                        )
                        lines.append(f'{metric_name}{{{label_str}}} {mv.value}')
                else:
                    lines.append(f'{metric_name} {mv.value}')

            lines.append('')

        # Format all metrics
        format_metric(self.http_requests_total)
        format_metric(self.http_request_duration_seconds)
        format_metric(self.websocket_connections)
        format_metric(self.emotional_valence)
        format_metric(self.flow_state)
        format_metric(self.coherence_score)
        format_metric(self.dream_alignment)
        format_metric(self.uncertainty_level)
        format_metric(self.turns_total)
        format_metric(self.llm_requests_total)
        format_metric(self.llm_request_duration_seconds)
        format_metric(self.active_projects)
        format_metric(self.completed_projects)
        format_metric(self.project_iterations)
        format_metric(self.memory_episodes)
        format_metric(self.memory_semantic)
        format_metric(self.auth_attempts_total)
        format_metric(self.info)

        return '\n'.join(lines)

    def update_from_orchestrator(self, orchestrator) -> None:
        """Update metrics from orchestrator state."""
        if not orchestrator:
            return

        # Emotional state
        if hasattr(orchestrator, 'emotion'):
            self.emotional_valence.set(orchestrator.emotion.current_valence)

        # Flow state
        if hasattr(orchestrator, 'calibration'):
            difficulty = orchestrator.calibration.difficulty_moving_avg
            if difficulty < 0.4:
                self.flow_state.set(0)  # bored
            elif difficulty > 0.7:
                self.flow_state.set(1)  # overloaded
            else:
                self.flow_state.set(0.5)  # flow

        # Dream alignment
        if hasattr(orchestrator, 'metrics'):
            self.dream_alignment.set(orchestrator.metrics.last_dream_alignment)

        # Uncertainty
        if hasattr(orchestrator, 'assurance'):
            self.uncertainty_level.set(
                len(orchestrator.assurance.pending_concerns) / 10.0
            )

        # Projects
        if hasattr(orchestrator, 'gdil') and orchestrator.gdil:
            active = len([p for p in orchestrator.gdil.projects.values()
                         if p.get('phase') not in ['exit', 'archived']])
            self.active_projects.set(active)

        # Turn count
        if hasattr(orchestrator, 'turn_count'):
            # Set turns as gauge (counter would require tracking increments)
            pass


# Global metrics instance
metrics = PrometheusMetrics()


def get_metrics() -> PrometheusMetrics:
    """Get the global metrics instance."""
    return metrics
