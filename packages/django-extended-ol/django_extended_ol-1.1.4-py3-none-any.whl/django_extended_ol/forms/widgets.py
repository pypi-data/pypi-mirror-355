from django.contrib.gis.forms.widgets import OpenLayersWidget
from django.conf import settings


class WMTSWidget(OpenLayersWidget):
    template_name = "gis/openlayers-wmts.html"
    map_srid = settings.OLWIDGET["globals"].get("srid", 4326)
    extent = settings.OLWIDGET["globals"]["extent"]
    center_from_extent = [
            (extent[0] + extent[2]) / 2,
            (extent[1] + extent[3]) / 2,
        ]
    widget_options = {
        "wmts_layer_name": settings.OLWIDGET["wmts"].get("layer_name"),
        "wmts_style": settings.OLWIDGET["wmts"]["style"],
        "wmts_matrix_set": settings.OLWIDGET["wmts"]["matrix_set"],
        "wmts_attributions": settings.OLWIDGET["wmts"].get("attributions", None),
        "wmts_url_template": settings.OLWIDGET["wmts"]["url_template"],
        "wmts_request_encoding": settings.OLWIDGET["wmts"].get("request_encoding", 'KVP'),
        "wmts_format": settings.OLWIDGET["wmts"].get("format", None),
        "default_map_center": settings.OLWIDGET["globals"].get("default_center", center_from_extent),
        "default_resolution": settings.OLWIDGET["globals"].get("default_resolution", 8),
        "extent": extent,
        "resolutions": settings.OLWIDGET["globals"]["resolutions"]
    }

    class Media(OpenLayersWidget.Media):
        js = OpenLayersWidget.Media.js + (
            "olwidget/js/WMTSWidget.js",
        )
        css = {
            "all": OpenLayersWidget.Media.css["all"] + ("olwidget/css/WMTSWidget.css",)
        }

    def __init__(self, attrs=None):
        super().__init__()
        # Give widget_options to the template
        for key in self.widget_options.keys():
            self.attrs[key] = self.widget_options[key]
        if attrs:
            self.attrs.update(attrs)


class WMTSWithSearchWidget(WMTSWidget):
    widget_options = {
        **WMTSWidget.widget_options, 
        "search_url": settings.OLWIDGET["search"].get("url_template", None)
    }
