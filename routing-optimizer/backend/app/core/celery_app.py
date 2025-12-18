"""
Celery Application Configuration

Configures Celery for asynchronous task processing of heavy OR-Tools computations.
Uses Redis as both message broker and result backend.

Architecture:
┌──────────────────────────────────────────────────────────────────┐
│                       CELERY ARCHITECTURE                        │
└──────────────────────────────────────────────────────────────────┘

Frontend/API (FastAPI)
    │
    │ POST /api/optimize
    │ {"orders": [...], "fleet": {...}}
    │
    ▼
┌─────────────────────────────────────────────────────────────────┐
│  FastAPI Endpoint                                               │
│  task = solve_vrp_task.delay(request_data)                      │
│  return {"task_id": task.id, "status": "PENDING"}               │
└────────────────────┬────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│  Redis (Message Broker)                                         │
│  Queue: celery (default queue)                                  │
│  Stores: task metadata, arguments, status                       │
└────────────────────┬────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│  Celery Worker(s)                                               │
│  - Picks up task from queue                                     │
│  - Executes OR-Tools optimization                               │
│  - Calls OSRM/Valhalla for distance matrices                    │
│  - Returns result to Redis                                      │
└────────────────────┬────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│  Redis (Result Backend)                                         │
│  Stores: task results, exceptions, execution time               │
└────────────────────┬────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│  FastAPI Endpoint (Polling)                                     │
│  GET /api/tasks/{task_id}                                       │
│  Returns: status, result, or error                              │
└─────────────────────────────────────────────────────────────────┘

Autore: Senior Backend Architect
Data: 2025-12-18
"""

import os
import logging
from celery import Celery
from kombu import serialization

logger = logging.getLogger(__name__)

# ============================================================================
# CELERY CONFIGURATION
# ============================================================================

# Redis URLs from environment
CELERY_BROKER_URL = os.getenv(
    'CELERY_BROKER_URL',
    'redis://redis:6379/0'
)

CELERY_RESULT_BACKEND = os.getenv(
    'CELERY_RESULT_BACKEND',
    'redis://redis:6379/0'
)

# Create Celery instance
celery_app = Celery(
    'routing_optimizer',
    broker=CELERY_BROKER_URL,
    backend=CELERY_RESULT_BACKEND,
    include=['app.tasks.vrp_tasks']  # Auto-discover tasks
)

# ============================================================================
# CELERY CONFIGURATION OPTIONS
# ============================================================================

celery_app.conf.update(
    # Serialization
    task_serializer='json',
    result_serializer='json',
    accept_content=['json'],
    
    # Timezone
    timezone='Europe/Rome',
    enable_utc=True,
    
    # Task execution
    task_track_started=True,
    task_time_limit=3600,  # 1 hour max per task
    task_soft_time_limit=3300,  # 55 minutes soft limit
    task_acks_late=True,  # Acknowledge after task completion
    task_reject_on_worker_lost=True,
    
    # Result backend
    result_expires=86400,  # Results expire after 24 hours
    result_persistent=True,
    result_compression='gzip',
    
    # Worker settings
    worker_prefetch_multiplier=1,  # One task at a time per worker
    worker_max_tasks_per_child=50,  # Restart worker after 50 tasks (memory leaks)
    worker_disable_rate_limits=True,
    
    # Broker settings
    broker_connection_retry_on_startup=True,
    broker_connection_max_retries=10,
    
    # Task routes (optional - for multiple queues)
    task_routes={
        'app.tasks.vrp_tasks.solve_vrp_task': {'queue': 'vrp'},
        'app.tasks.vrp_tasks.solve_vrp_with_geocoding_task': {'queue': 'vrp'},
    },
    
    # Task annotations (optional - for task-specific configs)
    task_annotations={
        'app.tasks.vrp_tasks.solve_vrp_task': {
            'rate_limit': '10/m',  # Max 10 tasks per minute
            'time_limit': 3600,
        }
    },
    
    # Monitoring
    worker_send_task_events=True,
    task_send_sent_event=True,
)

# ============================================================================
# CELERY SIGNALS (Optional - for logging/monitoring)
# ============================================================================

from celery.signals import (
    task_prerun,
    task_postrun,
    task_failure,
    task_success,
    worker_ready,
    worker_shutdown
)


@worker_ready.connect
def worker_ready_handler(sender=None, **kwargs):
    """Log when worker is ready"""
    logger.info(f"🚀 Celery Worker READY: {sender}")
    logger.info(f"   Broker: {CELERY_BROKER_URL}")
    logger.info(f"   Backend: {CELERY_RESULT_BACKEND}")


@worker_shutdown.connect
def worker_shutdown_handler(sender=None, **kwargs):
    """Log when worker shuts down"""
    logger.warning(f"🛑 Celery Worker SHUTDOWN: {sender}")


@task_prerun.connect
def task_prerun_handler(task_id, task, args, kwargs, **extra):
    """Log before task execution"""
    logger.info(f"▶️  Task STARTED: {task.name} (ID: {task_id})")


@task_postrun.connect
def task_postrun_handler(task_id, task, args, kwargs, retval, **extra):
    """Log after task execution"""
    logger.info(f"✅ Task COMPLETED: {task.name} (ID: {task_id})")


@task_success.connect
def task_success_handler(sender=None, result=None, **kwargs):
    """Log on task success"""
    logger.info(f"🎉 Task SUCCESS: {sender.name}")


@task_failure.connect
def task_failure_handler(task_id, exception, args, kwargs, traceback, einfo, **extra):
    """Log on task failure"""
    logger.error(f"❌ Task FAILED: {task_id}")
    logger.error(f"   Exception: {exception}")
    logger.error(f"   Traceback: {traceback}")


# ============================================================================
# HEALTH CHECK TASK (Optional)
# ============================================================================

@celery_app.task(name='app.core.celery_app.health_check')
def health_check():
    """
    Simple health check task for monitoring
    
    Usage:
        from app.core.celery_app import health_check
        result = health_check.delay()
        print(result.get(timeout=5))
    """
    return {
        'status': 'healthy',
        'broker': CELERY_BROKER_URL,
        'backend': CELERY_RESULT_BACKEND,
        'message': 'Celery worker is operational'
    }


# ============================================================================
# CELERY APP INFO
# ============================================================================

def get_celery_info():
    """
    Get Celery configuration info
    
    Returns:
        dict: Celery configuration details
    """
    return {
        'broker_url': CELERY_BROKER_URL,
        'result_backend': CELERY_RESULT_BACKEND,
        'task_serializer': celery_app.conf.task_serializer,
        'result_serializer': celery_app.conf.result_serializer,
        'timezone': celery_app.conf.timezone,
        'task_time_limit': celery_app.conf.task_time_limit,
        'result_expires': celery_app.conf.result_expires,
        'worker_prefetch_multiplier': celery_app.conf.worker_prefetch_multiplier,
        'registered_tasks': list(celery_app.tasks.keys())
    }


if __name__ == '__main__':
    # Print configuration when run directly
    print("=" * 70)
    print("CELERY CONFIGURATION")
    print("=" * 70)
    
    info = get_celery_info()
    for key, value in info.items():
        print(f"{key}: {value}")
    
    print("=" * 70)
