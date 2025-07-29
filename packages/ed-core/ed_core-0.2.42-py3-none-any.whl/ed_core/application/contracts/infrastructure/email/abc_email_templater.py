from abc import abstractmethod


class ABCEmailTemplater:
    @abstractmethod
    def order_placed(
        self,
        order_number: str,
        consumer_name: str,
        order_date: str,
        business_name: str,
        delivery_address: str,
        estimated_delivery_date: str,
    ) -> str: ...
