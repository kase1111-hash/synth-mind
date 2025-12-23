# Security Assessment Report - Synth Mind

**Date:** 2025-12-23
**Assessment Type:** Full Security Audit
**Repository:** synth-mind

---

## Executive Summary

This security assessment covers the Synth Mind codebase with focus on OWASP Top 10 vulnerabilities. The codebase demonstrates good security practices in most areas, with proper parameterized SQL queries, secure password hashing, and JWT authentication. However, **one critical vulnerability** was identified in the shell command execution module that requires immediate attention.

| Severity | Count |
|----------|-------|
| Critical | 1 |
| High | 1 |
| Medium | 3 |
| Low | 2 |

---

## Critical Findings

### 1. Command Injection via Shell Execution

**File:** `core/tools.py:493-548`
**Severity:** CRITICAL
**CVSS Score:** 9.8

**Description:**
The `_shell_run` function uses `subprocess.run` with `shell=True`, which creates a command injection vulnerability despite the presence of a blocklist.

```python
result = subprocess.run(
    command,
    shell=True,  # <-- DANGEROUS
    capture_output=True,
    text=True,
    timeout=10,
    cwd=str(self.workspace)
)
```

**Attack Vectors:**
1. The `find` command in `ALLOWED_SHELL_COMMANDS` can execute arbitrary code:
   ```
   find . -exec /bin/sh -c 'malicious_command' \;
   ```

2. The `grep` command with Perl regex can potentially execute code on some systems

3. Newline injection may bypass the dangerous_patterns check

**Recommendation:**
- Replace `shell=True` with list-based command execution
- Remove `find` and `grep` from allowed commands or strictly validate arguments
- Implement a proper command allowlist with argument validation

---

## High Findings

### 2. Code Execution Sandbox Missing Timeout Enforcement

**File:** `core/tools.py:297-382`
**Severity:** HIGH
**CVSS Score:** 7.5

**Description:**
The `_code_execute` function claims to execute code with a timeout but no actual timeout mechanism is implemented. This allows denial-of-service through infinite loops.

```python
# Comment says "Execute with timeout" but no timeout is actually enforced
with redirect_stdout(stdout_capture), redirect_stderr(stderr_capture):
    exec(compiled, restricted_globals)  # Can run forever
```

**Impact:**
- Denial of service via infinite loops
- Resource exhaustion (CPU, memory)

**Recommendation:**
- Implement actual timeout using `signal.alarm()` or `multiprocessing` with timeout
- Add memory limits using `resource.setrlimit()`

---

## Medium Findings

### 3. Eval Usage in Calculator

**File:** `core/tools.py:160-166`
**Severity:** MEDIUM
**CVSS Score:** 5.3

**Description:**
The calculator uses `eval()` on user input. While mitigated by regex filtering and restricted builtins, `eval()` is inherently risky.

```python
clean_expr = re.sub(r'[^0-9+\-*/().,%\s\w]', '', expression)
result = eval(clean_expr, {"__builtins__": {}}, safe_dict)
```

**Current Mitigations:**
- Regex removes most dangerous characters
- `__builtins__` set to empty dict
- Limited `safe_dict` with only math functions

**Recommendation:**
- Consider using `ast.literal_eval()` or a proper math parser library
- Add comprehensive test cases for bypass attempts

### 4. Overly Permissive CORS Configuration

**File:** `dashboard/server.py:100-106`
**Severity:** MEDIUM
**CVSS Score:** 5.0

**Description:**
CORS is configured with wildcard origin `"*"`, allowing any website to make authenticated requests.

```python
cors = aiohttp_cors.setup(self.app, defaults={
    "*": aiohttp_cors.ResourceOptions(
        allow_credentials=True,
        expose_headers="*",
        allow_headers="*",
    )
})
```

**Impact:**
- Cross-site request forgery possible if authentication tokens are accessible
- Sensitive data exposure to malicious websites

**Recommendation:**
- Configure specific allowed origins for production deployment
- Remove `allow_credentials=True` if not needed

### 5. Auto-Install of Python Packages

**Files:** `utils/auth.py:19-22`, `dashboard/server.py:22-25`
**Severity:** MEDIUM
**CVSS Score:** 4.8

**Description:**
The code automatically installs Python packages via pip if they're missing, which could introduce supply chain risks.

```python
except ImportError:
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "PyJWT"])
    import jwt
```

**Recommendation:**
- Remove auto-install and document dependencies in requirements.txt
- Use virtual environments and pre-installed dependencies

---

## Low Findings

### 6. Sensitive Files Not in .gitignore

**Severity:** LOW

**Description:**
The `.gitignore` template in version_control.py correctly excludes `.env` but the actual `.env.example` is tracked in git.

**Recommendation:**
- Ensure production deployments never commit actual `.env` files
- Add security reminder in `.env.example`

### 7. Token Blacklist In-Memory Only

**File:** `utils/auth.py:99`
**Severity:** LOW

**Description:**
The token blacklist is stored only in memory and is lost on server restart.

```python
self.blacklisted_tokens: set = set()
```

**Impact:**
- Logged out tokens may still be valid after server restart

**Recommendation:**
- Persist blacklist to database or use short-lived tokens
- Consider Redis for production deployments

---

## Security Strengths

The codebase demonstrates several security best practices:

### Authentication (utils/auth.py)
- PBKDF2-SHA256 with 100,000 iterations for password hashing
- Secure random salt generation using `secrets.token_hex()`
- Timing-safe password comparison using `secrets.compare_digest()`
- JWT tokens with proper expiration handling
- File permissions set to 0o600 for sensitive data

### SQL Injection Prevention (core/memory.py)
- All database queries use parameterized statements with `?` placeholders
- No string interpolation in SQL queries

### Path Traversal Prevention (core/tools.py)
- Proper path validation using `.resolve()` and containment checks
- Workspace sandboxing for file operations

### Version Control (utils/version_control.py)
- Safe subprocess usage with list arguments (not shell=True)
- Branch name sanitization

---

## Recommendations Summary

| Priority | Action |
|----------|--------|
| Immediate | Fix command injection in `_shell_run` - remove `shell=True` |
| Immediate | Implement actual timeout in `_code_execute` |
| High | Restrict CORS origins for production |
| Medium | Replace `eval()` with proper math parser |
| Medium | Remove auto-pip-install behavior |
| Low | Persist token blacklist |

---

## Files Reviewed

| File | Status |
|------|--------|
| `core/memory.py` | Reviewed - SQL Injection Safe |
| `core/tools.py` | Reviewed - Critical Issues Found |
| `core/orchestrator.py` | Reviewed - No Issues |
| `utils/version_control.py` | Reviewed - Safe |
| `utils/auth.py` | Reviewed - Strong Security |
| `dashboard/server.py` | Reviewed - CORS Issue |
| `config/personality.yaml` | Reviewed - No Issues |

---

*Report generated by security audit on 2025-12-23*
