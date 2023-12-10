from ads.choices import STATUS_ACTIVE
from ads.models import Ad


class AdsByCategoryMixin:
    @staticmethod
    def get_ads_by_category(category):
        return Ad.objects.select_related('category').filter(category=category, is_approved=True, status=STATUS_ACTIVE)
