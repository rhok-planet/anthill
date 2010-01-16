from django.dispatch import Signal

# signal is provided for potential logging of all messages
message_sent = Signal(providing_args=['subject', 'body', 'recipient'])
