from typing import Any, Optional

from flet.core.constrained_control import ConstrainedControl
from flet.core.control import OptionalNumber


class FletSvg(ConstrainedControl):
    def __init__(
        self,
        #
        # Control
        #
        opacity: OptionalNumber = None,
        tooltip: Optional[str] = None,
        visible: Optional[bool] = None,
        data: Any = None,
        #
        # ConstrainedControl
        #
        left: OptionalNumber = None,
        top: OptionalNumber = None,
        right: OptionalNumber = None,
        bottom: OptionalNumber = None,
        #
        # FletSvg specific
        #
        src: Optional[str] = None,
        kind: Optional[str] = None,
        key: Optional[str] = None,
        fit: str = "contain",
        alignment: str = "center",
        width: OptionalNumber = None,
        height: OptionalNumber = None,
        match_text_direction: bool = False,
        allow_drawing_outside_view_box: bool = False,
        semantics_label: Optional[str] = None,
        exclude_from_semantics: bool = False,
        clip_behavior: str = "hard_edge",
    ) -> None:
        ConstrainedControl.__init__(
            self,
            tooltip=tooltip,
            opacity=opacity,
            visible=visible,
            data=data,
            left=left,
            top=top,
            right=right,
            bottom=bottom,
        )

        self.src = src
        self.kind = kind
        self.key = key
        self.fit = fit
        self.alignment = alignment
        self.width = width
        self.height = height
        self.match_text_direction = match_text_direction
        self.allow_drawing_outside_view_box = allow_drawing_outside_view_box
        self.semantics_label = semantics_label
        self.exclude_from_semantics = exclude_from_semantics
        self.clip_behavior = clip_behavior

    def _get_control_name(self) -> str:
        return "flet_svg"

    # src
    @property
    def src(self):
        return self._get_attr("src")

    @src.setter
    def src(self, src) -> None:
        self._set_attr("src", src)

    # kind
    @property
    def kind(self):
        return self._get_attr("kind")

    @kind.setter
    def kind(self, kind) -> None:
        self._set_attr("kind", kind)

    # key
    @property
    def key(self):
        return self._get_attr("key")

    @key.setter
    def key(self, key) -> None:
        self._set_attr("key", key)

    # fit
    @property
    def fit(self):
        return self._get_attr("fit")

    @fit.setter
    def fit(self, fit) -> None:
        self._set_attr("fit", fit)

    # alignment
    @property
    def alignment(self):
        return self._get_attr("alignment")

    @alignment.setter
    def alignment(self, alignment) -> None:
        self._set_attr("alignment", alignment)

    # width
    @property
    def width(self):
        return self._get_attr("width")

    @width.setter
    def width(self, width) -> None:
        self._set_attr("width", width)

    # height
    @property
    def height(self):
        return self._get_attr("height")

    @height.setter
    def height(self, height) -> None:
        self._set_attr("height", height)

    # match_text_direction
    @property
    def match_text_direction(self):
        return self._get_attr("match_text_direction")

    @match_text_direction.setter
    def match_text_direction(self, match_text_direction) -> None:
        self._set_attr("match_text_direction", match_text_direction)

    # allow_drawing_outside_view_box
    @property
    def allow_drawing_outside_view_box(self):
        return self._get_attr("allow_drawing_outside_view_box")

    @allow_drawing_outside_view_box.setter
    def allow_drawing_outside_view_box(self, allow_drawing_outside_view_box) -> None:
        self._set_attr("allow_drawing_outside_view_box", allow_drawing_outside_view_box)

    # semantics_label
    @property
    def semantics_label(self):
        return self._get_attr("semantics_label")

    @semantics_label.setter
    def semantics_label(self, semantics_label) -> None:
        self._set_attr("semantics_label", semantics_label)

    # exclude_from_semantics
    @property
    def exclude_from_semantics(self):
        return self._get_attr("exclude_from_semantics")

    @exclude_from_semantics.setter
    def exclude_from_semantics(self, exclude_from_semantics) -> None:
        self._set_attr("exclude_from_semantics", exclude_from_semantics)

    # clip_behavior
    @property
    def clip_behavior(self):
        return self._get_attr("clip_behavior")

    @clip_behavior.setter
    def clip_behavior(self, clip_behavior) -> None:
        self._set_attr("clip_behavior", clip_behavior)

