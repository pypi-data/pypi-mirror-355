from ed_core.application.services.abc_service import ABCService
from ed_core.application.services.bill_service import BillService
from ed_core.application.services.business_service import BusinessService
from ed_core.application.services.consumer_service import ConsumerService
from ed_core.application.services.parcel_service import ParcelService
from ed_domain.common.logging import get_logger
from ed_domain.core.aggregate_roots import Order
from ed_domain.persistence.async_repositories import ABCAsyncUnitOfWork

LOG = get_logger()


class OrderService(ABCService[Order, None, None, None]):
    def __init__(self, uow: ABCAsyncUnitOfWork):
        super().__init__("Order", uow.order_repository)

        self._uow = uow
        self._bill_service = BillService(self._uow)
        self._business_service = BusinessService(self._uow)
        self._consumer_service = ConsumerService(self._uow)
        self._parcel_service = ParcelService(self._uow)

        LOG.info("OrderService initialized with UnitOfWork.")
