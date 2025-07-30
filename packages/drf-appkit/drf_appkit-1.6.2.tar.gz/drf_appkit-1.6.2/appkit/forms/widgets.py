from django.forms import MultiWidget, Select, TextInput

from djmoney.settings import CURRENCY_CHOICES


__all__ = ("MoneyWidget",)


class MoneyWidget(MultiWidget):
    step = None
    template_name = 'appkit/forms/widgets/money_widget.html'

    def __init__(
        self,
        choices=CURRENCY_CHOICES,
        amount_widget=None,
        currency_widget=None,
        default_currency=None,
        step=1,
        *args,
        **kwargs
    ):
        self.step = step

        if not amount_widget:
            widget_attrs = {
                'class': 'border-0 py-3 pl-7 pr-20 w-full',
            }
            if isinstance(self.step, int):
                widget_attrs['pattern'] = '[0-9]*'
            amount_widget = TextInput(attrs=widget_attrs)

        self.default_currency = default_currency
        if not currency_widget:
            currency_widget = Select(choices=choices, attrs={
                'class': 'h-full border-0 bg-transparent py-0 pl-2 pr-7 text-gray-500 sm:text-sm',
            })
        widgets = (amount_widget, currency_widget)
        super().__init__(widgets, *args, **kwargs)

    def decompress(self, value):
        if value is not None:
            if isinstance(value, (list, tuple)):
                return value

            amount = value.amount
            if isinstance(self.step, int):
                amount = amount.to_integral_value()

            currency = value.currency
            return [amount, currency]
        return [None, self.default_currency]
