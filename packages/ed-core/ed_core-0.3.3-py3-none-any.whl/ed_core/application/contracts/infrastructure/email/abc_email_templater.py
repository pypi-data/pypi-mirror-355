from abc import abstractmethod


class ABCEmailTemplater:
    @abstractmethod
    def delivery_business_otp(
        self,
        otp: str,
        order_number: str,
        business_name: str,
        bill_amount: str,
        business_address: str,
        driver_full_name: str,
        driver_phone_number: str,
    ) -> str: ...

    @abstractmethod
    def delivery_consumer_otp(
        self,
        otp: str,
        order_number: str,
        consumer_name: str,
        delivery_address: str,
        driver_full_name: str,
        driver_phone_number: str,
    ) -> str: ...

    @abstractmethod
    def delivery_completed(
        self,
        order_number: str,
        consumer_name: str,
        driver_name: str,
        delivery_address: str,
        delivery_time: str,
    ) -> str: ...

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
