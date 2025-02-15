import datetime
import json
import re

from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.hashers import check_password, make_password
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q, Sum, Count, F
from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.urls import reverse_lazy
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import ListView, DetailView, View, FormView, TemplateView

from apps.forms import UserForm, UpdatePasswordForm, SearchForm
from apps.models import Product, Category, User, Wishlist, Order, Thread, Payment, Region, District, OperatorComment, \
    Transaction


class HomeListView(ListView):
    template_name = 'home.html'
    model = Category
    context_object_name = 'categorys'

    def get_context_data(self, *, object_list=None, **kwargs):
        data = super().get_context_data(**kwargs)
        data['products'] = Product.objects.filter(reserve__gt=0)


        if self.request.user.is_authenticated:
            data['user'] = self.request.user

            liked_products = self.request.user.liked_products.all()
            data['liked_products_ids'] = [product.id for product in liked_products]

        data['wishlist_count'] = Wishlist.objects.filter(user_id=self.request.user.id).count()
        data['regions']=Region.objects.all()
        return data

class AdminTemplateView(TemplateView):
    template_name = 'admin.html'


class ProductDetailView(LoginRequiredMixin,DetailView):
    model = Product
    login_url = reverse_lazy('auth')
    template_name = 'apps/product/product-detail.html'
    context_object_name = 'product'
    slug_url_kwarg = 'slug'
    slug_field = 'slug'

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        data['user'] = self.request.user
        data['wishlist_count'] = Wishlist.objects.filter(user_id=self.request.user.id).count()
        return data


class ProductListView(ListView):
    model = Product
    context_object_name = 'products'
    template_name = 'apps/product/mahsulotlar.html'

    def get_context_data(self, *, object_list=None, **kwargs):
        data = super().get_context_data(**kwargs)
        data['products'] = Product.objects.filter(reserve__gt=0)
        data['categorys'] = Category.objects.all()
        data['wishlist_count'] = Wishlist.objects.filter(user_id=self.request.user.id).count()
        return data


class CategoryProduct(ListView):
    model = Product
    context_object_name = 'products'
    template_name = 'apps/product/mahsulotlar.html'

    def get_queryset(self):
        if self.kwargs['slug'] != 'barchasi' and self.kwargs['slug'] != 'top_tovarlar':
            return Product.objects.filter(category__slug=self.kwargs['slug'],reserve__gt=0)
        if self.kwargs['slug'] == 'top_tovarlar':
            return Product.objects.annotate(
                total_quantity=Sum('orders__quantity')
            ).order_by('-total_quantity')[:2]
        return Product.objects.filter(reserve__gt=0)

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categorys'] = Category.objects.all()
        if self.kwargs['slug'] != 'barchasi':
            context['current_category'] = self.kwargs.get('slug')
        elif self.kwargs['slug'] == 'top_tovarlar':
            context['current_category'] = 'top_tovarlar'
        else:
            context['current_category'] = 'barchasi'
        context['wishlist_count'] = Wishlist.objects.filter(user_id=self.request.user.id).count()
        return context


class MyFavorites(ListView):
    model = Product
    context_object_name = 'products'
    template_name = 'apps/product/favorite-products.html'

    def get_queryset(self):
        if self.request.user.is_authenticated:
            return Product.objects.filter(liked_by_users=self.request.user,reserve__gt=0)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['wishlist_count'] = Wishlist.objects.filter(user_id=self.request.user.id).count()
        return context


def wishlist(request, slug):
    product = Product.objects.filter(slug=slug).first()
    user = request.user.id
    wishlist_item = Wishlist.objects.filter(user_id=user, product_id=product.id).first()
    if not wishlist_item:
        Wishlist.objects.create(product_id=product.id, user_id=user)
    else:

        Wishlist.objects.filter(user_id=request.user.id, product_id=product.id).update(
            quantity=wishlist_item.quantity + 1)
    return redirect('home')


class WishListView(ListView):
    template_name = 'apps/product/wishlist.html'
    model = Wishlist
    context_object_name = 'wishlists'

    def get_queryset(self):
        return Wishlist.objects.filter(user_id=self.request.user.id)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context['wishlist_count'] = Wishlist.objects.filter(user_id=self.request.user.id).count()

        wishlist_items = Wishlist.objects.filter(user_id=self.request.user.id)

        total_sum = sum(item.product.price * item.quantity for item in wishlist_items)

        context['total_sum'] = total_sum or 0

        if context['total_sum'] == 0:
            context['free'] = True

        return context


class OrderView(View):
    def get(self, *args, **kwargs):
        orders = Order.objects.filter(user=self.request.user)
        context = {
            'orders': orders,
            'wishlist_count': Wishlist.objects.filter(user_id=self.request.user.id).count()
        }
        return render(self.request, 'apps/product/orders.html', context)


class CreateOrderView(View):
    def post(self, *args, **kwargs):
        full_name = self.request.POST.get('full_name')
        phone_number = self.request.POST.get('phone_number')
        quantity = self.request.POST.get('quantity')
        cleaned_phone_number = re.sub(r'\D', '', phone_number)[3:]
        slug = kwargs.get('slug')
        product = Product.objects.filter(slug=slug).first()
        new_reserve=int(product.reserve)-int(quantity)




        if new_reserve >= 0:
            Product.objects.filter(slug=slug).update(reserve=new_reserve)
            price=int(product.price)*int(quantity)
            Order.objects.create(user=self.request.user, phone_number=cleaned_phone_number, product=product,
                                 fullname=full_name, quantity=quantity,price=price)

            thread = Thread.objects.filter(user=self.request.user, product=product).first()

            if thread:
                new_trade_count = int(thread.trade_count) + int(quantity)
                Thread.objects.filter(user=self.request.user, product=product).update(trade_count=new_trade_count)

            context={
                'product': product,
                'quantity': quantity,
                'all_price': price,
            }
            return render(self.request,'apps/utils/success.html',context)
        return render(self.request, 'apps/utils/error.html',{'product_reserve':Product.objects.filter(id=product.id).first().reserve,
                        'product':Product.objects.filter(id=product.id).first()})

class AuthView(View):
    def get(self, request):
        logout(request)
        return render(self.request, 'apps/auth/login-register.html')

    def post(self, request):
        phone_number = request.POST['phone_number']
        password = request.POST['password']
        cleaned_phone_number = re.sub(r'\D', '', phone_number)[3:]
        user = User.objects.filter(phone_number=cleaned_phone_number).first()
        if user:
            if check_password(password, user.password):
                login(request, user)
                context = {
                    'user': request.user,
                    'wishlist_count': Wishlist.objects.filter(user_id=request.user.id).count(),
                    'products': Product.objects.all()
                }
                return render(request, 'home.html', context=context)
            else:
                messages.error(request, 'Username yoki parol hato!')
                login(request, user)
                return render(request, 'apps/auth/login-register.html')
        else:
            User.objects.create(phone_number=cleaned_phone_number, password=make_password(password))
            context = {
                'user': request.user,
                'wishlist_count': Wishlist.objects.filter(user_id=request.user.id).count()
            }
            return render(request, 'home.html', context)

class ProfileView(View):
    def get(self, *args, **kwargs):
        context={
            'user':User.objects.get(pk=self.request.user.pk),
            'wishlist_count': Wishlist.objects.filter(user_id=self.request.user.pk).count()
        }

        return render(self.request,'apps/user/profile.html',context)

class SettingsFormView(FormView):
    template_name = 'apps/user/settings.html'
    form_class = UserForm
    def form_valid(self, form):
        first_name=form.cleaned_data['first_name']
        last_name=form.cleaned_data['last_name']
        region=form.cleaned_data['region']
        district=form.cleaned_data['district']
        address=form.cleaned_data['address']
        telegram_id=form.cleaned_data['telegram_id']
        bio=form.cleaned_data['bio']

        User.objects.filter(id=self.request.user.pk).update(first_name=first_name.title(),last_name=last_name.title(),bio=bio.title(),
                                                            region=region.title(),district=district.title(),address=address.title(),telegram_id=telegram_id)
        context={
            'wishlist_count': Wishlist.objects.filter(user_id=self.request.user.pk).count(),

        }
        return render(self.request,'apps/user/settings.html',context)

class UpdatePasswordFromView(FormView):
    template_name = 'apps/user/settings.html'
    form_class = UpdatePasswordForm
    def form_valid(self, form):
        f=form.cleaned_data['old_password']
        print(f)

class MarketListview(ListView):
    template_name = 'apps/utils/market.html'
    model = Category
    context_object_name = 'categorys'

    def get_context_data(self, *, object_list=None, **kwargs):
        data = super().get_context_data(**kwargs)
        data['products'] = Product.objects.all()

        if self.request.user.is_authenticated:
            data['user'] = self.request.user

            liked_products = self.request.user.liked_products.all()
            data['liked_products_ids'] = [product.id for product in liked_products]

        data['wishlist_count'] = Wishlist.objects.filter(user_id=self.request.user.id).count()
        return data

class CancelOrderView(View):
    def get(self, *args, **kwargs):
        id=self.kwargs['id']
        order = Order.objects.filter(id=id).first()
        Order.objects.filter(id=id).update(status=f'{Order.StatusChoices.cancelled}')
        new_reserve=int(Product.objects.filter(id=order.product.id).first().reserve)+int(order.quantity)
        Product.objects.filter(id=order.product.id).update(reserve=new_reserve)
        # old_cancel_count=int(Thread.objects.filter(user=self.request.user,product=order.product).first().cancel_count)
        # old_trade_count=int(Thread.objects.filter(user=self.request.user,product=order.product).first().trade_count)
        # Thread.objects.filter(user=self.request.user,product=order.product).update(cancel_count=old_cancel_count+1,trade_count=old_trade_count-1)
        return redirect('orders')

class RecoverOrder(View):
    def get(self, *args, **kwargs):
        id=self.kwargs['id']
        order = Order.objects.filter(id=id).first()
        new_reserve = int(Product.objects.filter(id=order.product.id).first().reserve) - int(order.quantity)
        if new_reserve>=0:
            Product.objects.filter(id=order.product.id).update(reserve=new_reserve)
            Order.objects.filter(id=id).update(status=f'{Order.StatusChoices.new}',date_ordered=datetime.datetime.now())
            # old_cancel_count=int(Thread.objects.filter(user=self.request.user,product=order.product).first().cancel_count)
            #         old_trade_count=int(Thread.objects.filter(user=self.request.user,product=order.product).first().trade_count)
            #         Thread.objects.filter(user=self.request.user,product=order.product).update(cancel_count=old_cancel_count+1,trade_count=old_trade_count-1)
            return redirect('orders')
        return render(self.request, 'apps/utils/error.html',{'product_reserve':Product.objects.filter(id=order.product.id).first().reserve,
                                'product':Product.objects.filter(id=order.product.id).first()})

class WishlistOrderView(View):
    def post(self,*args, **kwargs):
        full_name=self.request.POST.get('full_name')
        phone_number=self.request.POST.get('phone_number')
        products=Wishlist.objects.filter(user=self.request.user)
        for i in products:
            Order.objects.create(product=i.product,user=self.request.user,fullname=full_name,phone_number=phone_number,quantity=i.quantity)
        Wishlist.objects.filter(user=self.request.user).delete()
        return render(self.request,'apps/utils/success.html',{'wishlist_count':Wishlist.objects.filter(user=self.request.user).count()})

class CreateThreadView(View):
    def post(self, *args, **kwargs):
        title = self.request.POST.get('title')
        product_id = self.request.POST.get('product_id')
        discount = self.request.POST.get('discount')
        if not discount:
            discount=0
        else:
            discount=int(discount)
        product=Product.objects.filter(id=product_id).first()
        if title=='':
            title=product.name
        if product.discount>=discount and discount>=0:
            Thread.objects.create(title=title,product=product,discount_price=discount,user=self.request.user)
        else:
            messages.error(self.request,"Chegirma belgilangan chegaradan oshib ketdi yoki 0 (nol) dan kichik")
            print(True)
            return render(self.request,'apps/utils/market.html')
        context={
            'threads':Thread.objects.filter(user=self.request.user)
        }
        return render(self.request, 'apps/utils/thread-list.html', context)

class ThreadListView(View):
    def get(self, request, *args, **kwargs):
        threads = Thread.objects.filter(user=request.user)
        context={'threads': threads,
                 'wishlist_count': Wishlist.objects.filter(user=self.request.user).count()}
        return render(request, 'apps/utils/thread-list.html', context)


class ThreadProduct(ListView):
    model = Product
    context_object_name = 'products'
    template_name = 'apps/utils/market.html'

    def get_queryset(self):
        if self.kwargs['slug'] != 'barchasi' and self.kwargs['slug'] != 'top_tovarlar':
            return Product.objects.filter(category__slug=self.kwargs['slug'],reserve__gt=0)
        if self.kwargs['slug'] == 'top_tovarlar':
            print(True,1)
            return Product.objects.annotate(
    total_quantity=Sum('orders__quantity')
).order_by('-total_quantity')[:2]
        return Product.objects.filter(reserve__gt=0)

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categorys'] = Category.objects.all()
        if self.kwargs['slug'] != 'barchasi':
            context['current_category'] = self.kwargs.get('slug')
        else:
            context['current_category'] = 'barchasi'
        context['wishlist_count'] = Wishlist.objects.filter(user_id=self.request.user.id).count()
        return context

class SearchFormView(FormView):
    template_name = 'home.html'
    form_class = SearchForm
    success_url = reverse_lazy('home')
    def form_valid(self, form):
        search_field=form.cleaned_data['search_field']
        context={}
        context['products']=Product.objects.filter(Q(name__icontains=search_field),reserve__gt=0)
        context['search_field']=search_field
        return render(self.request, self.template_name, context)


class ThreadToProductView(View):
    def get(self, *args, **kwargs):
        thread=Thread.objects.filter(id=kwargs.get('id')).first()
        product=Product.objects.filter(id=thread.product.id).first()
        new_visit=int(thread.visit)+1
        Thread.objects.filter(id=thread.id).update(visit=new_visit)
        context={
            'product':product,
            'thread_id':thread.id,
        }
        if thread.discount_price>0:
            new_price=product.price-thread.discount_price
            context['new_price']=new_price
        return render(self.request,'apps/utils/thread-product-detail.html',context)

class StatisticView(View):
    def get(self, *args, **kwargs):
        jami_tashrif = Thread.objects.filter(user=self.request.user).aggregate(total_visits=Sum('visit'))
        jami_bekor = Thread.objects.filter(user=self.request.user).aggregate(cancel_count=Sum('cancel_count'))

        context={
            'threads':Thread.objects.filter(user=self.request.user),
            'jami_tashrif':jami_tashrif['total_visits'],
            'jami_bekor':jami_bekor['cancel_count'],
            'wishlist_count': Wishlist.objects.filter(user=self.request.user).count(),
        }
        return render(self.request,'apps/utils/statistic.html',context)

class QuestionsView(View):
    def get(self, *args, **kwargs):
        context={
            'wishlist_count': Wishlist.objects.filter(user=self.request.user).count()
        }
        return render(self.request,'apps/utils/questions.html',context)
class CompetitionListView(ListView):
    template_name = 'apps/utils/competition.html'
    context_object_name = 'competitions'
    model = Thread
    def get_context_data(self, *args, **kwargs):
        data=super().get_context_data( **kwargs)
        data['competitions'] = Thread.objects.annotate(
            sold_product_count=Count('orders', filter=Q(orders__status=Order.StatusChoices.completed))
        ).select_related('user').order_by('-sold_product_count')
        data['wishlist_count']= Wishlist.objects.filter(user=self.request.user).count()
        return data

class CreateOrderViaThreadView(View):
    def post(self, *args, **kwargs):
        thread_id=self.request.POST.get('thread_id')
        full_name = self.request.POST.get('full_name')
        phone_number = self.request.POST.get('phone_number')
        quantity = self.request.POST.get('quantity')
        cleaned_phone_number = re.sub(r'\D', '', phone_number)[3:]
        slug = kwargs.get('slug')
        product = Product.objects.filter(slug=slug).first()
        new_reserve = int(product.reserve) - int(quantity)

        if new_reserve >= 0:
            Product.objects.filter(slug=slug).update(reserve=new_reserve)
            thread = Thread.objects.filter(id=thread_id).first()




            if thread:
                new_trade_count = int(thread.trade_count) + int(quantity)
                Thread.objects.filter(user=self.request.user, product=product).update(trade_count=new_trade_count)


            new_price=int(product.price)-int(thread.discount_price)
            all_price=int(quantity)*int(new_price)
            Order.objects.create(user=self.request.user, phone_number=cleaned_phone_number, product=product,
                                 fullname=full_name, quantity=quantity, thread=thread,price=all_price)

            context={
                'product': product,
                'quantity': quantity,
                'thread':thread,
                'all_price':all_price,
            }
            return render(self.request,'apps/utils/success.html',context)
        return render(self.request, 'apps/utils/error.html',{'product_reserve':Product.objects.filter(id=product.id).first().reserve,
                        'product':Product.objects.filter(id=product.id).first()})

class PaymentView(View):
    def get(self, *args, **kwargs):
        user_transactions=Transaction.objects.filter(user=self.request.user)
        all_sum=0
        for transaction in user_transactions:
            if transaction.payment.status==Payment.StatusChoices.completed:
                all_sum+=transaction.amount

        payments=Payment.objects.filter(receiver=self.request.user)
        context={
            'wishlist_count': Wishlist.objects.filter(user=self.request.user).count(),
            'balance': User.objects.filter(id=self.request.user.id).first().balance,
            'all_sum':all_sum,
            'payments':payments,
        }
        return render(self.request,'apps/utils/payment.html',context)
    def post(self, *args, **kwargs):
        user=User.objects.filter(pk=self.request.user.id)
        if user.first() :
            card_number=self.request.POST.get('card_number')
            amount=int(self.request.POST.get('amount'))
            # check=self.request.POST.get('check')

            context = {
                'card_number': card_number,
                'amount': amount,
                'wishlist_count': Wishlist.objects.filter(user=self.request.user).count(),
            }

            if user.first().balance>=amount:
                Payment.objects.create(amount=amount, receiver=user.first(),card_number=card_number,)
                old_balance=user.first().balance
                new_balance=old_balance-amount
                user.update(balance=new_balance)
                # Transaction.objects.create(amount=amount, user=self.request.user,card_number=card_number)
            else:
                return render(self.request,'apps/utils/error-payment.html',context)


            return render(self.request,'apps/utils/success-payment.html',context)
        else:
            return redirect('settings')


class DiagramTemplateView(TemplateView):
    template_name = 'apps/utils/diagramms.html'
    def get_context_data(self,*args, **kwargs):
        data=super().get_context_data(**kwargs)
        data['wishlist_count']= Wishlist.objects.filter(user=self.request.user).count()
        return data

class OperatorView(View):
    def get(self, *args, **kwargs):

        current_orders=''

        status=self.request.GET.get('status')
        category = self.request.GET.get('category')
        region = self.request.GET.get('region')
        district = self.request.GET.get('district')

        if category:
            current_category = Category.objects.get(slug=category)
        if region:
            current_region = Region.objects.get(id=region)
        if district:
            current_district = District.objects.get(id=district)

        status_choices = Order.StatusChoices.choices

        if status and not region and not category:
            current_orders=Order.objects.filter(status=status)
        elif status and not region and category:
            current_orders=Order.objects.filter(status=status, product__category__slug=category)
        elif status and not category and region and not district:
            current_orders=Order.objects.filter(status=status,user__district__region_id=region)
        elif status and not category and district:
            current_orders=Order.objects.filter(status=status, user__district_id=district)



        if region:
            districts=District.objects.filter(region_id=region)


        statuses = [{'key': key, 'name': name} for key, name in status_choices]
        context={
            'categories': Category.objects.all(),
            'regions': Region.objects.all(),
            'status': statuses,
            'current_status': status,
        }
        # if current_orders!='':
        #     context['orders'] = current_orders
        if category:
            current_category = Category.objects.get(slug=category)
            context['current_category'] = current_category
        if region:
            context['districts']=districts
        if category:
            context['current_category'] = Category.objects.get(slug=category)
        if region:
            context['current_region'] = Region.objects.get(id=region)
        if district:
            context['current_district'] = District.objects.get(id=district)
        return render(self.request,'apps/operator/operator-page (1).html',context)
    def post(self, *args, **kwargs):
        status=self.request.POST.get('status')
        product__category_id=self.request.POST.get('product__category_id')
        region_id=self.request.POST.get('region')
        district_id=self.request.POST.get('district_id')



        if status and not product__category_id and not region_id and not district_id:
            orders=Order.objects.filter(status=status)



        if product__category_id and region_id and not district_id:
            orders=Order.objects.filter(user__district__region=region_id,product__category__slug=product__category_id)
            if status!='hammasi' and status!='':
                orders=Order.objects.filter(user__district__region=region_id,product__category__slug=product__category_id,status=status)
            else:
                orders = Order.objects.filter(user__district__region=region_id,
                                              product__category__slug=product__category_id)
        if product__category_id and not region_id and status!='hammasi':
            orders=Order.objects.filter(product__category__slug=product__category_id)
            if status != 'hammasi' and status != '':
                orders=Order.objects.filter(product__category__slug=product__category_id,status=status)
            else:
                orders = Order.objects.filter(product__category__slug=product__category_id)
        if product__category_id and district_id:
            orders=Order.objects.filter(product__category__slug=product__category_id,user__district_id=district_id)


        if not status:
            if not product__category_id:
                if not region_id:
                    if not district_id:
                        orders=Order.objects.all()




        if product__category_id:
            current_category=Category.objects.get(slug=product__category_id)
        if region_id:
            current_region=Region.objects.get(id=region_id)



        if district_id:
            current_district=District.objects.get(id=district_id)
            orders = Order.objects.filter(user__district=current_district)
            if product__category_id:
                orders = Order.objects.filter(product__category__slug=product__category_id,user__district_id=current_district)
        status_choices = Order.StatusChoices.choices
        statuses = [{'key': key, 'name': name} for key, name in status_choices]

        if status!='hammasi':
            if district_id:
                if status!='':
                    orders=Order.objects.filter(user__district=current_district,status=status)
            current_status=status
        else:
            if not district_id:
                orders=Order.objects.all()
                if region_id and not district_id:
                    orders=Order.objects.filter(user__district__region_id=region_id)
            else:
                orders=Order.objects.filter(user__district=current_district)
            current_status='hammasi'
        if not product__category_id and not district_id and region_id:
            orders=Order.objects.filter(user__district__region=current_region)
            if status!='hammasi':
                orders=Order.objects.filter(user__district__region=current_region,status=status)

        # ===================
        if region_id:
            districts=District.objects.filter(region_id=region_id)

        if status=='hammasi' and product__category_id:
            orders=Order.objects.filter(product__category__slug=product__category_id)
            if region_id and district_id:
                orders = Order.objects.filter(user__district__region_id=region_id,
                                              product__category__slug=product__category_id)
                if district_id:
                    orders = Order.objects.filter(user__district__region_id=region_id,
                                                  product__category__slug=product__category_id,user__district_id=district_id)
            if region_id and not district_id:
                orders=Order.objects.filter(user__district__region_id=region_id,product__category__slug=product__category_id)

        if status!='hammasi' and product__category_id and region_id and district_id:
            orders=Order.objects.filter(status=status,product__category__slug=product__category_id,user__district_id=district_id)

        if status=='' and product__category_id and region_id and district_id:
            orders=Order.objects.filter(product__category__slug=product__category_id,user__district_id=district_id)





        context={
            'categories': Category.objects.all(),
            'regions': Region.objects.all(),
            'orders': orders,
            'status':statuses,
            'current_status': current_status,
        }
        if product__category_id:
            context['current_category'] = current_category
        if region_id:
            context['current_region'] = current_region
        if district_id:
            context['current_district'] = current_district
        if region_id:
            context['districts'] = districts

        return render(self.request,'apps/operator/operator-page (1).html',context)


class OpratorChangeView(LoginRequiredMixin,View):
    login_url = reverse_lazy('auth')
    def get(self,*args,**kwargs):
        id=kwargs.get('pk')
        order=Order.objects.filter(id=id).first()
        print(order.user.first_name)
        context={
            'order':order,
            'regions':Region.objects.all(),
        }
        return render(self.request,'apps/operator/order-change.html',context)

    def post(self,*args,**kwargs):

        id=kwargs.get('pk')

        status=self.request.POST.get('status')
        quantity=self.request.POST.get('quantity')
        send_order_date=self.request.POST.get('send_order_date')
        region_id=self.request.POST.get('region')
        district_id=self.request.POST.get('district')
        comment_operator=self.request.POST.get('comment_operator')

        order = Order.objects.filter(id=id).first()
        order_quantity=order.quantity
        product_price=order.product.price
        price=product_price*order_quantity

        if status == Order.StatusChoices.completed:
            if order.thread:

                money=(int(order.product.discount)-int(order.thread.discount_price))*order_quantity
                old_balance=User.objects.filter(id=order.user.id).first().balance
                new_balance=old_balance+money
                User.objects.filter(id=order.user.id).update(balance=new_balance)

        Order.objects.filter(id=id).update(status=status,quantity=quantity,send_order_date=send_order_date)
        context={
            'order':order,
            'price':price,

        }
        if comment_operator:
            OperatorComment.objects.create(operator=self.request.user,comment=comment_operator,order=order)

        return render(self.request,'apps/operator/success.html',context)

class OperatorPayment(ListView):
    model=Payment
    template_name = 'apps/operator/questions-for-payment.html'
    context_object_name = 'payments'

    def get_context_data(self, *args, **kwargs):
        data = super().get_context_data(**kwargs)
        data['wishlist_count']=Wishlist.objects.filter(user_id=self.request.user.id).count()
        return data

class OperatorTransaction(DetailView):
    model=Payment
    template_name = 'apps/operator/transaction.html'
    context_object_name = 'payment'

    def post(self,*args,**kwargs):
        comment_operator=self.request.POST.get('comment_operator')
        payment=Payment.objects.get(id=kwargs.get('pk'))
        status=self.request.POST.get('status')
        check=self.request.POST.get('check')
        if status == Payment.StatusChoices.completed:
            if payment.status == Payment.StatusChoices.canceled:
                user = User.objects.filter(id=payment.receiver.id)
                old_balance = user.first().balance
                new_balance = old_balance - payment.amount
                user.update(balance=new_balance)
            Transaction.objects.create(user=payment.receiver,amount=payment.amount,card_number=payment.card_number,payment=payment,check_image=check)
            if comment_operator:
                Payment.objects.filter(id=payment.id).update(status=status,message=comment_operator,check_image=check)
            else:
                Payment.objects.filter(id=payment.id).update(status=status,check_image=check)
            context = {
                'payment': payment,
                'wishlist_count': Wishlist.objects.filter(user_id=self.request.user.id).count(),
            }
            return render(self.request, 'apps/operator/success-transaction.html', context=context)
        elif status == Payment.StatusChoices.canceled:

            user=User.objects.filter(id=payment.receiver.id)
            old_balance=user.first().balance
            new_balance=old_balance+payment.amount
            user.update(balance=new_balance)

            if comment_operator:
                Payment.objects.filter(id=payment.id).update(status=status,message=comment_operator,check_image=check)
            else:
                Payment.objects.filter(id=payment.id).update(status=status,check_image=check)

            context={
                'payment':payment,
                'wishlist_count':Wishlist.objects.filter(user_id=self.request.user.id).count(),
            }
            return render(self.request,'apps/operator/error-transaction.html',context=context)

        elif status == Payment.StatusChoices.accepted:
            Payment.objects.filter(id=payment.id).update(status=status)
            if comment_operator:
                Payment.objects.filter(id=payment.id).update(status=status,message=comment_operator,check_image=check)








@login_required
@csrf_exempt
def like_product(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        product_id = data.get('product_id')
        try:
            product = Product.objects.get(id=product_id)
        except Product.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'Product not found'}, status=404)
        user = request.user
        if user in product.liked_by_users.all():
            product.liked_by_users.remove(user)
            liked = False
        else:
            product.liked_by_users.add(user)
            liked = True

        return JsonResponse({'success': True, 'liked': liked})

    return JsonResponse({'success': False}, status=400)


def remove_from_wishlist(request, id):
    if id:
        Wishlist.objects.filter(id=id).delete()
        return redirect('wishlist')


def get_district_view(request):
    region_id = request.GET.get('region_id')
    districts = District.objects.filter(region_id=region_id)

    district_data = [{"id": district.id, "name": district.name} for district in districts]

    return JsonResponse(district_data, safe=False)









class TempTemplateView(TemplateView):
    template_name = 'apps/operator/transaction.html'
class TempTemplateView2(TemplateView):
    template_name = 'apps/product/order-detail.html'
