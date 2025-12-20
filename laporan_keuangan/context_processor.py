from .views import get_active_period

def active_period_context(request):
    period = get_active_period(request)
    if not period:
        return {}
    return {
        "period_start": period.start_date,
        "period_end": period.end_date,
        "active_period": period,
    }
