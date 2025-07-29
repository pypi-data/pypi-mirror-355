from http import HTTPStatus
import logging
from urllib.parse import urlencode

from django.http import HttpRequest, JsonResponse
from django.template.loader import render_to_string
from django.urls import path, reverse_lazy
from django.views import View
from djecharts.core.exceptions import InvalidFormError
from djecharts.core.filter import EChartsFilterForm
from djecharts.core.utils import class_property, get_tooltip


log = logging.getLogger("djecharts")


class EChartsView(View):
    title: str | None = None
    description: str | None = None
    filter_form_class: EChartsFilterForm | None = None

    top: str = "3%"
    bottom: str = "3%"
    left: str = "3%"
    right: str = "3%"

    @class_property
    def id(cls):
        # creates and returns an id for the view.
        return cls.__name__.lower() + "_echart"

    def json_response(self, chart_option: dict):
        """
        Returns the chart json data that will be used to
        build the chart in the frontend.
        """

        if not isinstance(chart_option, dict):
            raise TypeError(
                f"chart_option must be a dict, got {type(chart_option)} instead."
            )

        return JsonResponse(
            {
                "title": self.title,
                "description": self.description,
                "option": self.with_base_options(chart_option),
                "grid": {
                    "left": self.left,
                    "right": self.right,
                    "top": self.top,
                    "bottom": self.bottom,
                },
            },
            safe=False,
        )

    def with_base_options(self, option: dict):
        grid = option.get("grid", {})
        toolbox = option.get("toolbox", {})

        option.update(
            {
                "grid": {
                    "left": grid.get("left", self.left),
                    "right": grid.get("right", self.right),
                    "top": grid.get("top", self.top),
                    "bottom": grid.get("bottom", self.bottom),
                    "containLabel": grid.get("containLabel", True),
                    "show": grid.get("show", False),
                },
                "toolbox": {
                    "top": toolbox.get("top", "top"),
                    "left": toolbox.get("left", "right"),
                    "padding": toolbox.get("padding", [0, 50, 0, 0]),
                    "itemSize": toolbox.get("itemSize", 14),
                    "itemGap": toolbox.get("itemGap", 8),
                },
            }
        )

        return option

    def template_response(self, name: str, context=None):
        """
        Returns a json response containing a rendered
        template using the provided context.
        """

        return JsonResponse(
            {"html": render_to_string(name, context)},
            safe=False,
        )

    def error_template_response(self, message: str):
        """
        Returns a json response containing a rendered
        template with the provided error message.
        """

        return JsonResponse(
            {
                "html": render_to_string(
                    "djecharts/echarts_error.html", {"error": message}
                ),
                "error": message,
            },
            safe=False,
            status=HTTPStatus.BAD_REQUEST,
        )

    def form_error_response(self, form: EChartsFilterForm):
        """
        Returns a template response with the
        form errors in a formatted message.
        """

        error_message = " ".join(
            [f"{field}: {' '.join(errors)}" for field, errors in form.errors.items()]
        )

        return self.error_template_response(error_message)

    def dispatch(self, request: HttpRequest, *args, **kwargs):
        """
        Custom dipatch method to handle exceptions
        in the chart view and return a error template
        response when an exception is raised.
        """

        try:
            return super().dispatch(request, *args, **kwargs)

        except InvalidFormError as e:
            return self.on_invalid_form(e.form)

        except Exception:
            log.exception(f"error in chart view: {self.__class__.__name__}")
            return self.error_template_response(message="internal error.")

    @classmethod
    def path(cls, route: str):
        """
        Returns a URLPattern for the chart view
        with the provided route.
        """

        if cls.id is None:
            raise ValueError("chart view must have an id")

        return path(
            route=route,
            name=cls.id,
            view=cls.as_view(),
        )

    @classmethod
    def data(
        cls,
        *,
        initial_form_params: dict | None = None,
        hide_form: bool = False,
        exclude_form_fields: list | tuple | None = None,
    ):
        """
        Returns a dict with all necessary chart data
        that can be used in the template.
        """

        if cls.title is None:
            raise ValueError("title must be set")

        form = None
        initial_params = None

        if cls.filter_form_class is not None:
            form = cls.filter_form_class(initial=initial_form_params)

            if exclude_form_fields is not None and isinstance(
                exclude_form_fields, (list, tuple)
            ):
                for field in exclude_form_fields:
                    form.fields.pop(field, None)

            if initial_form_params is not None:
                initial_params = cls._query_params_from_initials(
                    initial_form_params, prefix=form.prefix
                )

        return {
            "id": cls.id,
            "title": cls.title,
            "description": cls.description,
            "url": reverse_lazy(cls.id),
            "initial_params": initial_params,
            "hide_form": hide_form,
            "form": form,
        }

    @staticmethod
    def js(code: str | None = None, *, tooltip: str | None = None):
        """
        Returns a dict with the js code in the '__js__'
        key that will be evaluated in the frontend.
        """

        if tooltip:
            code = get_tooltip(tooltip)

        return {"__js__": code}

    @staticmethod
    def _query_params_from_initials(initials: dict, prefix: str = ""):
        """
        Convert the initials dict to a query params string
        that can be used in the chart view url.
        """

        try:
            return urlencode(
                {f"{prefix}-{k}": v for k, v in initials.items() if v is not None}
            )

        except TypeError:
            log.error("error converting initials to query params")

        return ""

    def on_invalid_form(self, form: EChartsFilterForm):
        """Called when form.is_valid() returns False. It must return a response."""

        return self.form_error_response(form)

    def get_form(self) -> EChartsFilterForm | None:
        """Returns the form instance."""

        if self.filter_form_class is not None:
            form = self.filter_form_class(self.request.GET or None)

            if not form.is_valid():
                raise InvalidFormError(form)

            return form
