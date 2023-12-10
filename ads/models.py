from django.contrib.auth import get_user_model
from django.db import models

from ads.choices import STATUS_CHOICES, STATUS_PENDING
from common.models import BaseModel

User = get_user_model()


# Create your models here.


class AdCategory(BaseModel):
    title = models.CharField(max_length=255)
    image = models.URLField()

    class Meta:
        verbose_name_plural = "Ad Categories"

    def __str__(self):
        return str(self.title)


class AdSubCategory(BaseModel):
    category = models.ForeignKey(AdCategory, on_delete=models.CASCADE, null=True, related_name="sub_categories")
    title = models.CharField(max_length=255)

    def __str__(self):
        return f"{self.category.title} ---- {self.title}"

    class Meta:
        verbose_name_plural = "Ad SubCategories"


class Ad(BaseModel):
    ad_creator = models.ForeignKey(User, on_delete=models.CASCADE, null=True, related_name="created_ads")
    name = models.CharField(max_length=255)
    description = models.TextField()
    price = models.CharField(max_length=255, null=True)
    location = models.CharField(max_length=255, null=True)
    category = models.ForeignKey(AdCategory, on_delete=models.CASCADE, null=True, related_name="ads")
    sub_category = models.ForeignKey(AdSubCategory, on_delete=models.CASCADE, null=True, related_name="ads")
    featured = models.BooleanField(default=False)
    is_approved = models.BooleanField(default=False)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING, null=True)

    class Meta:
        indexes = [
            models.Index(fields=['is_approved', 'status']),
        ]

    def __str__(self):
        return str(self.name)


class AdImage(BaseModel):
    ad = models.ForeignKey(Ad, on_delete=models.CASCADE, null=True, related_name="images")
    image = models.URLField()

    def __str__(self):
        return self.ad.name


class FavouriteAd(BaseModel):
    customer = models.ForeignKey(User, on_delete=models.CASCADE, null=True, related_name="favourite_ads")
    ad = models.ForeignKey(Ad, on_delete=models.CASCADE, null=True, related_name="favourite_ads")

    def __str__(self):
        return f"{self.customer} --- {self.ad.name}"


class Chat(BaseModel):
    ad = models.ForeignKey(Ad, on_delete=models.CASCADE, related_name="ad_chats")
    initiator = models.ForeignKey(User, on_delete=models.CASCADE, related_name="chat_initiators")
    receiver = models.ForeignKey(User, on_delete=models.CASCADE, related_name="chat_receivers")


class Message(BaseModel):
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name="message_sender")
    text = models.CharField(max_length=200, blank=True)
    attachment = models.FileField(blank=True)
    chat = models.ForeignKey(Chat, on_delete=models.CASCADE, related_name="messages")


class AdReport(BaseModel):
    ad = models.ForeignKey(Ad, on_delete=models.CASCADE, related_name="ad_reports")
    reporter = models.ForeignKey(User, on_delete=models.CASCADE, related_name="reports")
    text = models.TextField()

    def __str__(self):
        return f"{self.reporter.full_name} ----> {self.text[:30]}"
