"""Resource namespaces exposed on the clients (client.jobs, client.companies,
client.tasks)."""

from .jobs import AsyncJobsResource, JobsResource
from .companies import AsyncCompaniesResource, CompaniesResource
from .tasks import AsyncTasksResource, TasksResource

__all__ = [
    "JobsResource",
    "AsyncJobsResource",
    "CompaniesResource",
    "AsyncCompaniesResource",
    "TasksResource",
    "AsyncTasksResource",
]
