"""Health and metrics endpoints (REL-05, REL-06)."""

from __future__ import annotations

import os

from fastapi import APIRouter, HTTPException

from ..services.circuit_breaker import get_all_circuit_states, CircuitState
from ..settings import settings


router = APIRouter(prefix="/health", tags=["health"])


@router.get("/")
async def health_check() -> dict:
    """Basic liveness probe.
    
    Returns 200 if the application is running.
    Used for Kubernetes liveness probes.
    """
    return {"status": "ok"}


@router.get("/ready")
async def readiness_check() -> dict:
    """Deep readiness probe (REL-06).
    
    Checks all critical components:
    - Database connectivity
    - Inference backend health (via circuit breaker state)
    - Disk space availability
    - Project directory writability
    
    Returns 503 if any critical component is unhealthy.
    Used for Kubernetes readiness probes and load balancer health checks.
    """
    issues = []
    
    # Check database connectivity
    try:
        from ..database import get_db_connection
        
        conn = get_db_connection()
        conn.execute("SELECT 1")
        conn.close()
    except Exception as e:
        issues.append({"component": "database", "error": str(e)})
    
    # Check circuit breaker states (inference backend health)
    circuit_states = get_all_circuit_states()
    for backend_name, state in circuit_states.items():
        if state.state == CircuitState.OPEN:
            recovery_seconds = 0
            if state.recovery_available_at:
                import time
                recovery_seconds = max(0, state.recovery_available_at - time.time())
            
            issues.append({
                "component": f"inference_{backend_name}",
                "error": f"Circuit breaker open",
                "recovery_in_seconds": recovery_seconds,
            })
    
    # Check disk space (warn if < 1GB free)
    try:
        project_dir = settings.projects_dir
        if project_dir.exists():
            # Cross-platform disk space check
            import shutil
            if os.name == 'nt':  # Windows
                # Get drive letter from path (e.g., "F:" from "F:\Dev\...")
                drive = str(project_dir).split(':')[0] + ':'
                total, used, free = shutil.disk_usage(drive)
                free_bytes = free
            else:  # Unix/Linux/macOS
                stat = os.statvfs(project_dir)
                free_bytes = stat.f_bavail * stat.f_frsize
            
            min_free_bytes = 1_073_741_824  # 1 GB
            
            if free_bytes < min_free_bytes:
                issues.append({
                    "component": "disk_space",
                    "error": f"Low disk space: {free_bytes / (1024*1024):.1f}MB free",
                })
    except Exception as e:
        issues.append({"component": "disk_space", "error": str(e)})
    
    # Check project directory writability
    try:
        projects_dir = settings.projects_dir
        if not projects_dir.exists():
            projects_dir.mkdir(parents=True, exist_ok=True)
        
        # Test write permission with temp file
        test_file = projects_dir / ".health_check_test"
        test_file.write_text("test")
        test_file.unlink()
    except Exception as e:
        issues.append({"component": "projects_directory", "error": str(e)})
    
    if issues:
        raise HTTPException(
            status_code=503,
            detail={
                "status": "unhealthy",
                "issues": issues,
            },
        )
    
    return {
        "status": "ready",
        "components": {
            "database": "ok",
            "inference": {
                "backend": settings.inference_backend,
                "backends": {name: str(state.state) for name, state in circuit_states.items()},
            },
            "disk_space": "ok",
            "projects_directory": "ok",
        },
    }


@router.get("/llm")
async def llm_health_check() -> dict:
    """Check if the configured inference backend is reachable.

    Uses a lightweight /models call to verify connectivity without blocking
    on inference. Returns 200 with model info if reachable, 503 if not.
    """
    try:
        from ..inference.factory import build_inference_backend

        inferencer = build_inference_backend(settings)
        models = inferencer.list_models()
        model_name = settings.inference_default_model or (models[0] if models else "unknown")
        return {
            "status": "ok",
            "backend": settings.inference_backend,
            "model": model_name,
        }
    except Exception as e:
        raise HTTPException(
            status_code=503,
            detail={
                "status": "unavailable",
                "backend": settings.inference_backend,
                "error": str(e),
            },
        )


@router.get("/metrics")
async def get_metrics() -> dict:
    """Prometheus-style metrics endpoint (REL-05).
    
    Returns current system metrics:
    - Circuit breaker states for all inference backends
    - Failure counts and recovery times
    - Job status counts
    - Role model checker status counts
    
    Can be scraped by Prometheus or similar monitoring systems.
    """
    import time
    from ..settings import settings
    from ..persistence.sqlite import connect
    
    circuit_states = get_all_circuit_states()
    
    metrics = {
        "timestamp": time.time(),
        "circuit_breakers": {},
        "jobs": {},
        "role_model_checker": {},
    }
    
    # Circuit breaker states
    for backend_name, state in circuit_states.items():
        metrics["circuit_breakers"][backend_name] = {
            "state": state.state.value,
            "failure_count": state.failure_count,
            "last_failure_time": state.last_failure_time,
            "last_success_time": state.last_success_time,
            "recovery_available_at": state.recovery_available_at,
        }
    
    # Job status counts
    try:
        db_path = settings.operations_db_path
        with connect(db_path) as connection:
            # Count jobs by status
            row = connection.execute(
                "SELECT status, COUNT(*) as count FROM jobs GROUP BY status"
            ).fetchall()
            for r in row:
                metrics["jobs"][r["status"]] = r["count"]
            
            # Ensure all terminal statuses are present
            for status in ["PENDING", "PROCESSING", "COMPLETED", "FAILED"]:
                if status not in metrics["jobs"]:
                    metrics["jobs"][status] = 0
            
            # Compute success and failure rates from terminal states only
            completed_count = metrics["jobs"].get("COMPLETED", 0)
            failed_count = metrics["jobs"].get("FAILED", 0)
            terminal_total = completed_count + failed_count
            if terminal_total > 0:
                metrics["jobs"]["success_rate"] = completed_count / terminal_total
                metrics["jobs"]["failure_rate"] = failed_count / terminal_total
            else:
                metrics["jobs"]["success_rate"] = 0.0
                metrics["jobs"]["failure_rate"] = 0.0
            
            # Compute latency telemetry from job_attempts with both started_at and finished_at
            latency_rows = connection.execute(
                """SELECT started_at, finished_at FROM job_attempts 
                   WHERE started_at IS NOT NULL AND finished_at IS NOT NULL"""
            ).fetchall()
            
            if latency_rows:
                latencies_ms = []
                for lr in latency_rows:
                    from datetime import datetime
                    started = datetime.fromisoformat(lr["started_at"].replace('Z', '+00:00'))
                    finished = datetime.fromisoformat(lr["finished_at"].replace('Z', '+00:00'))
                    duration_ms = (finished - started).total_seconds() * 1000
                    latencies_ms.append(duration_ms)
                
                metrics["jobs"]["average_latency_ms"] = sum(latencies_ms) / len(latencies_ms)
                metrics["jobs"]["min_latency_ms"] = min(latencies_ms)
                metrics["jobs"]["max_latency_ms"] = max(latencies_ms)
            else:
                metrics["jobs"]["average_latency_ms"] = 0.0
                metrics["jobs"]["min_latency_ms"] = 0.0
                metrics["jobs"]["max_latency_ms"] = 0.0
    except Exception:
        # If we can't read job counts, return zeros
        metrics["jobs"] = {
            "PENDING": 0,
            "PROCESSING": 0,
            "COMPLETED": 0,
            "FAILED": 0,
            "success_rate": 0.0,
            "failure_rate": 0.0,
            "average_latency_ms": 0.0,
            "min_latency_ms": 0.0,
            "max_latency_ms": 0.0,
        }
    
    # Role model checker status counts
    try:
        db_path = settings.operations_db_path
        with connect(db_path) as connection:
            # Count checker runs by status
            row = connection.execute(
                "SELECT status, COUNT(*) as count FROM checker_runs GROUP BY status"
            ).fetchall()
            for r in row:
                metrics["role_model_checker"][r["status"]] = r["count"]
            
            # Ensure all terminal statuses are present
            for status in ["PENDING", "RUNNING", "COMPLETED", "FAILED"]:
                if status not in metrics["role_model_checker"]:
                    metrics["role_model_checker"][status] = 0
            
            # Compute success and failure rates from terminal states only
            completed_count = metrics["role_model_checker"].get("COMPLETED", 0)
            failed_count = metrics["role_model_checker"].get("FAILED", 0)
            terminal_total = completed_count + failed_count
            if terminal_total > 0:
                metrics["role_model_checker"]["success_rate"] = completed_count / terminal_total
                metrics["role_model_checker"]["failure_rate"] = failed_count / terminal_total
            else:
                metrics["role_model_checker"]["success_rate"] = 0.0
                metrics["role_model_checker"]["failure_rate"] = 0.0
            
            # Compute latency telemetry from checker_run_attempts with both started_at and finished_at
            latency_rows = connection.execute(
                """SELECT started_at, finished_at FROM checker_run_attempts 
                   WHERE started_at IS NOT NULL AND finished_at IS NOT NULL"""
            ).fetchall()
            
            if latency_rows:
                latencies_ms = []
                for lr in latency_rows:
                    from datetime import datetime
                    started = datetime.fromisoformat(lr["started_at"].replace('Z', '+00:00'))
                    finished = datetime.fromisoformat(lr["finished_at"].replace('Z', '+00:00'))
                    duration_ms = (finished - started).total_seconds() * 1000
                    latencies_ms.append(duration_ms)
                
                metrics["role_model_checker"]["average_latency_ms"] = sum(latencies_ms) / len(latencies_ms)
                metrics["role_model_checker"]["min_latency_ms"] = min(latencies_ms)
                metrics["role_model_checker"]["max_latency_ms"] = max(latencies_ms)
            else:
                metrics["role_model_checker"]["average_latency_ms"] = 0.0
                metrics["role_model_checker"]["min_latency_ms"] = 0.0
                metrics["role_model_checker"]["max_latency_ms"] = 0.0
    except Exception:
        # If we can't read checker counts, return zeros
        metrics["role_model_checker"] = {
            "PENDING": 0,
            "RUNNING": 0,
            "COMPLETED": 0,
            "FAILED": 0,
            "success_rate": 0.0,
            "failure_rate": 0.0,
            "average_latency_ms": 0.0,
            "min_latency_ms": 0.0,
            "max_latency_ms": 0.0,
        }
    
    return metrics
