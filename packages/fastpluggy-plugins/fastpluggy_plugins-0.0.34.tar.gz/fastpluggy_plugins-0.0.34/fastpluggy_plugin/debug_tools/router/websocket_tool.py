from fastpluggy.core.view_builer.components.button import ButtonView
from fastpluggy.core.widgets import ButtonWidget


def websocket_notification_button():
    """
    Create a button to send a WebSocket notification.
    """
    return ButtonWidget(
        url= "#",  # No direct URL needed since we use JavaScript
        label= "Send WebSocket Notification",
        css_class= "btn btn-primary",
        onclick= """
                fetch('/ws/send-message?method=json', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({type: 'message', content: 'test notification'})
                })
                .then(response => {
                    if (!response.ok) {
                        throw new Error(`HTTP error! Status: ${response.status}`);
                    }
                    return response.json();
                })
                .then(data => console.log(data))
                .catch(error => console.error('Error sending message:', error));
            """,
    )
