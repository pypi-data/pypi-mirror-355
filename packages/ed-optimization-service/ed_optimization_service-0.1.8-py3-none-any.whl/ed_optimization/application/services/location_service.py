from ed_domain.common.logging import get_logger
from ed_domain.core.aggregate_roots import Location
from ed_domain.persistence.async_repositories import ABCAsyncUnitOfWork

from ed_optimization.application.services.abc_service import ABCService

CITY = "Addis Ababa"
COUNTRY = "Ethiopia"
LOG = get_logger()


class LocationService(
    ABCService[
        Location,
        None,
        None,
        None,
    ]
):
    def __init__(self, uow: ABCAsyncUnitOfWork) -> None:
        super().__init__("Location", uow.location_repository)

        LOG.info("LocationService initialized with UnitOfWork.")
