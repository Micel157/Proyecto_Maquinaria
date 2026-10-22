from django.utils import timezone


def anio_actual():
    return timezone.localdate().year
