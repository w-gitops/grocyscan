"""Background job queue manager."""

import asyncio
import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Callable

from pydantic import BaseModel

from app.core.logging import get_logger

logger = get_logger(__name__)


class JobStatus(str, Enum):
    """Job status values."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class JobType(str, Enum):
    """Job type values."""

    LLM_OPTIMIZE = "llm_optimize"
    GROCY_SYNC = "grocy_sync"
    IMAGE_DOWNLOAD = "image_download"
    OFFLINE_SYNC = "offline_sync"


class Job(BaseModel):
    """Job model for queue operations."""

    id: str
    job_type: JobType
    status: JobStatus = JobStatus.PENDING
    priority: int = 0
    payload: dict[str, Any]
    result: dict[str, Any] | None = None
    error_message: str | None = None
    attempts: int = 0
    max_attempts: int = 3
    created_at: datetime
    started_at: datetime | None = None
    completed_at: datetime | None = None


class JobQueueManager:
    """In-memory job queue manager.

    For production, this should be backed by the database and use
    proper async workers.
    """

    def __init__(self) -> None:
        self._jobs: dict[str, Job] = {}
        self._handlers: dict[JobType, Callable[[dict[str, Any]], Any]] = {}
        self._running = False
        self._worker_task: asyncio.Task | None = None

    def register_handler(
        self, job_type: JobType, handler: Callable[[dict[str, Any]], Any]
    ) -> None:
        """Register a handler for a job type.

        Args:
            job_type: The job type
            handler: Async function to handle the job
        """
        self._handlers[job_type] = handler
        logger.info("Registered job handler", job_type=job_type.value)

    async def enqueue(
        self,
        job_type: JobType,
        payload: dict[str, Any],
        priority: int = 0,
    ) -> str:
        """Add a job to the queue.

        Args:
            job_type: Type of job
            payload: Job data
            priority: Higher priority runs first

        Returns:
            str: Job ID
        """
        job_id = str(uuid.uuid4())
        job = Job(
            id=job_id,
            job_type=job_type,
            priority=priority,
            payload=payload,
            created_at=datetime.now(timezone.utc),
        )

        self._jobs[job_id] = job
        logger.info("Job enqueued", job_id=job_id, job_type=job_type.value)
        return job_id

    async def get_job(self, job_id: str) -> Job | None:
        """Get a job by ID.

        Args:
            job_id: The job ID

        Returns:
            Job if found, None otherwise
        """
        return self._jobs.get(job_id)

    async def list_jobs(
        self,
        status: JobStatus | None = None,
        limit: int = 100,
    ) -> list[Job]:
        """List jobs, optionally filtered by status.

        Args:
            status: Filter by status
            limit: Maximum jobs to return

        Returns:
            list: Jobs matching criteria
        """
        jobs = list(self._jobs.values())

        if status:
            jobs = [j for j in jobs if j.status == status]

        # Sort by priority (desc) and created_at (asc)
        jobs.sort(key=lambda j: (-j.priority, j.created_at))

        return jobs[:limit]

    async def retry_job(self, job_id: str) -> bool:
        """Retry a failed job.

        Args:
            job_id: The job ID

        Returns:
            bool: True if job was reset for retry
        """
        job = self._jobs.get(job_id)
        if not job or job.status != JobStatus.FAILED:
            return False

        job.status = JobStatus.PENDING
        job.error_message = None
        logger.info("Job reset for retry", job_id=job_id)
        return True

    async def cancel_job(self, job_id: str) -> bool:
        """Cancel a pending job.

        Args:
            job_id: The job ID

        Returns:
            bool: True if job was cancelled
        """
        job = self._jobs.get(job_id)
        if not job or job.status != JobStatus.PENDING:
            return False

        job.status = JobStatus.CANCELLED
        logger.info("Job cancelled", job_id=job_id)
        return True

    async def start_worker(self) -> None:
        """Start the background worker."""
        if self._running:
            return

        self._running = True
        self._worker_task = asyncio.create_task(self._worker_loop())
        logger.info("Job queue worker started")

    async def stop_worker(self) -> None:
        """Stop the background worker."""
        self._running = False
        if self._worker_task:
            self._worker_task.cancel()
            try:
                await self._worker_task
            except asyncio.CancelledError:
                pass
        logger.info("Job queue worker stopped")

    async def _worker_loop(self) -> None:
        """Main worker loop that processes jobs."""
        while self._running:
            try:
                # Get next pending job
                pending = await self.list_jobs(status=JobStatus.PENDING, limit=1)

                if pending:
                    await self._process_job(pending[0])
                else:
                    # No jobs, wait before checking again
                    await asyncio.sleep(1)

            except Exception as e:
                logger.error("Worker loop error", error=str(e))
                await asyncio.sleep(5)

    async def _process_job(self, job: Job) -> None:
        """Process a single job.

        Args:
            job: The job to process
        """
        handler = self._handlers.get(job.job_type)
        if not handler:
            logger.error("No handler for job type", job_type=job.job_type.value)
            job.status = JobStatus.FAILED
            job.error_message = f"No handler for job type: {job.job_type.value}"
            return

        job.status = JobStatus.RUNNING
        job.started_at = datetime.now(timezone.utc)
        job.attempts += 1

        logger.info(
            "Processing job",
            job_id=job.id,
            job_type=job.job_type.value,
            attempt=job.attempts,
        )

        try:
            result = await handler(job.payload)
            job.status = JobStatus.COMPLETED
            job.result = result if isinstance(result, dict) else {"result": result}
            job.completed_at = datetime.now(timezone.utc)
            logger.info("Job completed", job_id=job.id)

        except Exception as e:
            logger.error("Job failed", job_id=job.id, error=str(e))

            if job.attempts >= job.max_attempts:
                job.status = JobStatus.FAILED
                job.error_message = str(e)
            else:
                job.status = JobStatus.PENDING  # Will retry
                job.error_message = f"Attempt {job.attempts} failed: {e}"

    def get_stats(self) -> dict[str, int]:
        """Get queue statistics.

        Returns:
            dict: Job counts by status
        """
        stats = {status.value: 0 for status in JobStatus}
        for job in self._jobs.values():
            stats[job.status.value] += 1
        return stats


# Global queue manager instance
job_queue = JobQueueManager()
