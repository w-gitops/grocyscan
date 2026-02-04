"""Job queue management endpoints."""

from fastapi import APIRouter
from pydantic import BaseModel

from app.services.queue import Job, JobStatus, job_queue

router = APIRouter()


class JobListResponse(BaseModel):
    """Response model for job list."""

    jobs: list[Job]
    total: int
    stats: dict[str, int]


class JobResponse(BaseModel):
    """Response model for single job."""

    job: Job | None
    found: bool


@router.get("", response_model=JobListResponse)
async def list_jobs(
    status: str | None = None,
    limit: int = 100,
) -> JobListResponse:
    """List all jobs in the queue.

    Args:
        status: Filter by status (pending, running, completed, failed, cancelled)
        limit: Maximum number of jobs to return

    Returns:
        JobListResponse: List of jobs with stats
    """
    status_filter = JobStatus(status) if status else None
    jobs = await job_queue.list_jobs(status=status_filter, limit=limit)
    stats = job_queue.get_stats()

    return JobListResponse(
        jobs=jobs,
        total=sum(stats.values()),
        stats=stats,
    )


@router.get("/{job_id}", response_model=JobResponse)
async def get_job(job_id: str) -> JobResponse:
    """Get job by ID.

    Args:
        job_id: The job ID

    Returns:
        JobResponse: Job details
    """
    job = await job_queue.get_job(job_id)
    return JobResponse(job=job, found=job is not None)


@router.post("/{job_id}/retry")
async def retry_job(job_id: str) -> dict[str, str | bool]:
    """Retry a failed job.

    Args:
        job_id: The job ID

    Returns:
        dict: Retry result
    """
    success = await job_queue.retry_job(job_id)
    return {
        "success": success,
        "message": "Job queued for retry" if success else "Cannot retry job",
    }


@router.post("/{job_id}/cancel")
async def cancel_job(job_id: str) -> dict[str, str | bool]:
    """Cancel a pending job.

    Args:
        job_id: The job ID

    Returns:
        dict: Cancellation result
    """
    success = await job_queue.cancel_job(job_id)
    return {
        "success": success,
        "message": "Job cancelled" if success else "Cannot cancel job",
    }


@router.get("/stats", response_model=dict[str, int])
async def get_stats() -> dict[str, int]:
    """Get job queue statistics.

    Returns:
        dict: Job counts by status
    """
    return job_queue.get_stats()
