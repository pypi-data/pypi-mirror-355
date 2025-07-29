from typing import Optional, Any

from fastpluggy.core.widgets import AbstractWidget


class TracebackWidget(AbstractWidget):
    """
    A custom view that imports a template and dynamically sets data in its context.
    """
    widget_type = "raw"

    def __init__(self, list_traceback: list, **kwargs):
        super().__init__(**kwargs)
        self.source = self.render_error_card(list_traceback)

    def render_error_card(self, traceback_list):
            """
            Given a list of traceback messages, returns a Bootstrap-style alert card
            using a FontAwesome exclamation icon. If the list is empty, returns ''.
            """
            if not traceback_list:
                return ''

            # FontAwesome alert icon

            # Build the list items
            list_items = "\n".join(f"<pre class=\"alert-pre\">{line}</pre>" for line in traceback_list)

            # The full alert card
            html = f"""
        <div class="alert alert-important alert-danger alert-dismissible" role="alert">
          <div class="alert-icon"><i class="fa-solid fa-triangle-exclamation"></i></div>
          <div>
            <h4 class="alert-heading">An error occurred:</h4>
            <div class="alert-description">
              <div class="alert-list">
        {list_items}
              </div>
            </div>
          </div>
          <a class="btn-close" data-bs-dismiss="alert" aria-label="close"></a>
        </div>
        """.lstrip()

            return html

    def process(self, item: Optional[Any] = None, **kwargs) -> dict:
        pass