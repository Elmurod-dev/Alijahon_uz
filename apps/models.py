import datetime
import uuid

from django.contrib.auth.base_user import AbstractBaseUser
from django.contrib.auth.base_user import BaseUserManager
from django.contrib.auth.hashers import make_password
from django.contrib.auth.models import AbstractUser
from django.db.models import Model, CharField, ImageField, SlugField, ForeignKey, DecimalField, SET_NULL, CASCADE, \
    DateTimeField, ManyToManyField, SmallIntegerField, TextField, UUIDField, BooleanField, TextChoices
from django.utils.text import slugify

from apps import functions


# Create your here.
class CustomUserManager(BaseUserManager):
    def _create_user(self, phone_number, email, password, **extra_fields):
        """
        Create and save a user with the given username, email, and password.
        """
        if not phone_number:
            raise ValueError("The given phone_number must be set")
        email = self.normalize_email(email)

        user = self.model(phone_number=phone_number, email=email, **extra_fields)
        user.password = make_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, phone_number, email=None, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        return self._create_user(phone_number, email, password, **extra_fields)

    def create_superuser(self, phone_number, email=None, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")

        return self._create_user(phone_number, email, password, **extra_fields)


class User(AbstractUser):
    class RoleChoices(TextChoices):
        user='user',"User"
        operator='operator',"Operator"
        super_admin='super_admin',"Super admin"
    phone_number = CharField(max_length=20, unique=True)
    objects = CustomUserManager()
    USERNAME_FIELD = 'phone_number'
    username = None
    bio = TextField(blank=True, null=True)
    address = CharField(max_length=200, blank=True, null=True)
    telegram_id = CharField(max_length=20, blank=True, null=True)
    balance = SmallIntegerField(default=0)
    role = CharField(max_length=20,choices=RoleChoices.choices, default=RoleChoices.user)
    district = ForeignKey('apps.District', on_delete=SET_NULL, null=True, related_name='users')


class Category(Model):
    image = ImageField(upload_to='categories/')
    name = CharField(max_length=50)
    slug = SlugField(unique=True)

    def save(
            self,
            *args,
            **kwargs
    ):
        if not self.slug:
            self.slug = slugify(self.name.lower())
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Region(Model):
    name = CharField(max_length=50)


class District(Model):
    name = CharField(max_length=50)
    region = ForeignKey('apps.Region', on_delete=SET_NULL, null=True, related_name='districts')


class Product(Model):
    name = CharField(max_length=50)
    description = CharField(max_length=500)
    price = DecimalField(max_digits=9, decimal_places=2)
    image = ImageField(upload_to='products/')
    slug = SlugField(unique=True)
    category = ForeignKey('apps.Category', on_delete=SET_NULL, null=True, blank=True, related_name='products')
    liked_by_users = ManyToManyField('apps.User', related_name='liked_products', blank=True)
    reserve = SmallIntegerField(default=1)
    discount = SmallIntegerField(default=0)

    def save(
            self,
            *args,
            **kwargs
    ):
        if not self.slug:
            self.slug = slugify(self.name.lower())
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Wishlist(Model):
    user = ForeignKey(User, on_delete=CASCADE, related_name='wishlist')
    product = ForeignKey('Product', on_delete=CASCADE, related_name='wishlisted_by')
    added_at = DateTimeField(auto_now_add=True)
    quantity = SmallIntegerField(default=1)


class Order(Model):
    class StatusChoices(TextChoices):
        new = 'new', 'Yangi'
        ready_to_deliver = 'ready_to_deliver', 'Dostavkaga tayyor'
        delivering = 'delivering', 'Yetkazilmoqda'
        delivered = 'delivered', 'Yetkazib berildi'
        cancelled_phone = 'cancelled_phone', 'Telefon ko\'tarmadi'
        cancelled = 'cancelled', 'Bekor qilidi'
        archived = 'archived', 'Arxivlandi'
        completed = 'completed', 'Tugallandi'

    phone_number = CharField(max_length=20)
    fullname = CharField(max_length=50)
    user = ForeignKey(User, on_delete=CASCADE, related_name='orders')
    product = ForeignKey(Product, on_delete=CASCADE, related_name='orders')
    date_ordered = DateTimeField(auto_now_add=True)
    status = CharField(max_length=50, choices=StatusChoices.choices, default=StatusChoices.new)
    quantity = SmallIntegerField(default=1)
    thread = ForeignKey('Thread', on_delete=SET_NULL, null=True, related_name='orders')
    # code = functions.make()
    price = DecimalField(max_digits=9, decimal_places=2,null=True)
    send_order_date=DateTimeField(default=datetime.datetime.now().date()+datetime.timedelta(days=1))

class OperatorComment(Model):
    comment = TextField()
    operator=ForeignKey('apps.User',on_delete=SET_NULL,null=True,related_name='operator')
    order=ForeignKey('apps.Order',on_delete=SET_NULL,null=True,related_name='comments')


class Thread(Model):
    title = CharField(max_length=50, null=True)
    visit = SmallIntegerField(default=1)
    user = ForeignKey(User, on_delete=CASCADE, related_name='threads')
    product = ForeignKey(Product, on_delete=CASCADE, related_name='threads')
    created_at = DateTimeField(auto_now_add=True)
    discount_price = SmallIntegerField(default=0)
    trade_count = SmallIntegerField(default=0)
    cancel_count = SmallIntegerField(
        default=0)  # ========= bu threadga tegishli productni necha marta cancel qilinganligi


class Payment(Model):
    class StatusChoices(TextChoices):
        in_progress='in_progress','In Progress'
        accepted='accepted','Accepted'
        canceled='canceled','Canceled'
        completed='completed','Completed'
    receiver = ForeignKey(User, on_delete=CASCADE, related_name='receiver')
    amount = DecimalField(max_digits=10, decimal_places=2)
    payment_method = CharField(
        max_length=10, default='money'
    )
    status=CharField(max_length=50, choices=StatusChoices.choices,default=StatusChoices.in_progress)
    message = TextField(null=True)
    card_number = CharField(max_length=50)
    created_at = DateTimeField(auto_now_add=True)
    check_image=ImageField(upload_to='transactions/',null=True)


class Transaction(Model):
    user = ForeignKey(User, on_delete=SET_NULL,null=True, related_name='transactions')
    amount = DecimalField(max_digits=10, decimal_places=2)
    card_number = CharField(max_length=50)
    date = DateTimeField(auto_now_add=True)
    payment=ForeignKey(Payment, on_delete=CASCADE, related_name='transactions')
    check_image=ImageField(upload_to='transactions/',null=True)


