from fastapi import Request

from fastpluggy.core.widgets import ButtonWidget


def run_task_button(request: Request, task, kwargs):
    """
    Create a button to send a WebSocket notification.
    """


    url_submit_task = request.url_for("submit_task")
    url_detail_task = request.url_for("task_details", task_id="__TASK_ID_REPLACE__")

    full_payload = {
        "function": task,
        "kwargs": kwargs,
    }
    # Dump to JSON (double-quoted), then escape any single quotes just in case
    payload_str = full_payload

    js = f"""
       (async () => {{
            const body = {payload_str}
           try {{
               const response = await fetch('{url_submit_task}?method=json', {{
                   method: 'POST',
                   headers: {{ 'Content-Type': 'application/json' }},
                   body: JSON.stringify(body)
               }});
               const data = await response.json();

               if (data.task_id) {{
                   window.location.href = '{url_detail_task}'.replace('__TASK_ID_REPLACE__', data.task_id);
               }} else {{
                   alert('Could not start task.');
               }}
           }} catch (err) {{
               console.error(err);
               alert('Network error. Please try again.');
           }}
       }})();
       """

    return ButtonWidget(
        url= "#",  # No direct URL needed since we use JavaScript
        label= f"Run Task {task}",
        css_class= "btn btn-primary",
        onclick=js ,
    )
