from jinja2 import Environment, FileSystemLoader

from ed_core.application.contracts.infrastructure.email.abc_email_templater import \
    ABCEmailTemplater


class EmailTemplater(ABCEmailTemplater):
    def __init__(self) -> None:
        self._file_names: dict[str, str] = {
            "order_placed": "order_placed.html",
        }
        self._template_env = Environment(
            loader=FileSystemLoader("./email_templates"))

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
