from jinja2 import Environment, FileSystemLoader

from ed_core.application.contracts.infrastructure.email.abc_email_templater import \
    ABCEmailTemplater


class EmailTemplater(ABCEmailTemplater):
    def __init__(self) -> None:
        self._file_names: dict[str, str] = {
            "order_placed": "order_placed.html",
            "delivery_completed": "delivery_completed.html",
            "delivery_consumer_otp": "delivery_consumer_otp.html",
            "delivery_business_otp": "delivery_business_otp.html",
        }
        self._template_env = Environment(
            loader=FileSystemLoader("./email_templates"))

    def delivery_business_otp(
        self,
        otp: str,
        order_number: str,
        business_name: str,
        bill_amount: str,
        business_address: str,
        driver_full_name: str,
        driver_phone_number: str,
    ) -> str:
        template = self._load_template("delivery_business_otp")
        return template.render(
            otp=otp,
            order_number=order_number,
            business_name=business_name,
            bill_amount=bill_amount,
            business_address=business_address,
            driver_full_name=driver_full_name,
            driver_phone_number=driver_phone_number,
        )

    def delivery_consumer_otp(
        self,
        otp: str,
        order_number: str,
        consumer_name: str,
        delivery_address: str,
        driver_full_name: str,
        driver_phone_number: str,
    ) -> str:
        template = self._load_template("delivery_consumer_otp")
        return template.render(
            otp=otp,
            order_number=order_number,
            consumer_name=consumer_name,
            delivery_address=delivery_address,
            driver_full_name=driver_full_name,
            driver_phone_number=driver_phone_number,
        )

    def delivery_completed(
        self,
        order_number: str,
        consumer_name: str,
        driver_name: str,
        delivery_address: str,
        delivery_time: str,
    ) -> str:
        template = self._load_template("delivery_completed")
        return template.render(
            order_number=order_number,
            consumer_name=consumer_name,
            driver_name=driver_name,
            delivery_address=delivery_address,
            delivery_time=delivery_time,
        )

    def order_placed(
        self,
        order_number: str,
        consumer_name: str,
        order_date: str,
        business_name: str,
        delivery_address: str,
        estimated_delivery_date: str,
    ) -> str:
        template = self._load_template("order_placed")
        return template.render(
            order_number=order_number,
            consumer_name=consumer_name,
            order_date=order_date,
            business_name=business_name,
            delivery_address=delivery_address,
            estimated_delivery_date=estimated_delivery_date,
        )

    def _load_template(self, template_key: str):
        file_name = self._file_names.get(template_key)
        if not file_name:
            raise ValueError(f"Template key '{template_key}' not found.")
        return self._template_env.get_template(file_name)
