# Repository Structure

```
synth-mind/
├── README.md                          # Main project documentation
├── SPEC_SHEET.md                      # Technical specification
├── SECURITY_REPORT.md                 # Security assessment
├── requirements.txt                   # Python dependencies
├── .env.example                       # Environment template
├── run_synth.py                       # CLI entry point
├── run_synth_with_dashboard.py        # CLI + Dashboard entry point
│
├── core/
│   ├── orchestrator.py                # Main processing loop
│   ├── llm_wrapper.py                 # Multi-provider LLM interface
│   ├── memory.py                      # Hybrid vector + SQL storage
│   └── tools.py                       # Tool sandbox manager
│
├── psychological/
│   ├── predictive_dreaming.py         # Anticipation + rewards
│   ├── assurance_resolution.py        # Uncertainty → relief
│   ├── meta_reflection.py             # Introspection
│   ├── temporal_purpose.py            # Identity evolution
│   ├── reward_calibration.py          # Flow state optimization
│   ├── social_companionship.py        # Peer grounding
│   ├── goal_directed_iteration.py     # GDIL project system
│   ├── project_templates.py           # Project templates
│   ├── collaborative_projects.py      # Multi-agent collaboration
│   └── federated_learning.py          # Privacy-preserving learning
│
├── utils/
│   ├── emotion_regulator.py           # Valence tracking
│   ├── metrics.py                     # Performance tracking
│   ├── logging.py                     # Logging setup
│   ├── auth.py                        # JWT authentication
│   ├── version_control.py             # Git VCS integration
│   ├── ssl_utils.py                   # SSL/TLS utilities
│   ├── rate_limiter.py                # API rate limiting
│   ├── access_logger.py               # HTTP access logging
│   └── ip_firewall.py                 # IP-based access control
│
├── dashboard/
│   ├── server.py                      # WebSocket + REST API server
│   ├── dashboard.html                 # Main dashboard page
│   ├── timeline.html                  # Gantt chart visualization
│   └── README_DASHBOARD.md            # Dashboard documentation
│
├── examples/
│   └── simple_chat.py                 # Demo script
│
├── config/
│   ├── personality.yaml               # Personality profiles
│   └── peers.txt                      # Peer endpoints (optional)
│
├── docs/
│   ├── QUICKSTART.md                  # 5-minute setup guide
│   ├── system-arch.md                 # High-level architecture
│   ├── GDIL_README.md                 # GDIL complete documentation
│   ├── PEER_SETUP.md                  # Multi-instance guide
│   └── Repository-Structure.md        # This file
│
├── tests/
│   └── test_security_e2e.py           # Security test suite
│
└── state/                             # Auto-generated on first run
    ├── memory.db                      # Episodic/semantic storage
    ├── embeddings/                    # Vector store
    └── synth.log                      # Application logs
```
