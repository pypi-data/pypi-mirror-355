from ed_domain.common.logging import get_logger
from ed_domain.core.aggregate_roots import Business
from ed_domain.persistence.async_repositories import ABCAsyncUnitOfWork

from ed_optimization.application.services.abc_service import ABCService
from ed_optimization.application.services.location_service import \
    LocationService

LOG = get_logger()


class BusinessService(
    ABCService[
        Business,
        None,
        None,
        None,
    ]
):
    def __init__(self, uow: ABCAsyncUnitOfWork):
        super().__init__("Business", uow.business_repository)

        self._uow = uow
        self._location_service = LocationService(self._uow)

        LOG.info("BusinessService initialized with UnitOfWork.")
