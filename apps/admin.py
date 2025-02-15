from django.contrib import admin
from apps.models import Category, Product

# ProductAdmin uchun
@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    exclude = ('slug',)  # 'slug'ni exclude qilish uchun ro'yxatni ishlatish kerak

# CategoryAdmin uchun
@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    exclude = ('slug',)  # 'slug'ni exclude qilish uchun ro'yxatni ishlatish kerak
