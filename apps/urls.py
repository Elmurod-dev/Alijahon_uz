from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path

from FalconModuleSeven import settings
from apps import views

urlpatterns = [
    path('', views.HomeListView.as_view(),name='home'),
    path('admin-page', views.AdminTemplateView.as_view(),name='admin_page'),
    path('like-product/', views.like_product, name='like_product'),
    path('product-detail/<slug:slug>', views.ProductDetailView.as_view(), name='product_detail'),
    path('mahsulotlar', views.ProductListView.as_view(), name='mahsulotlar'),
    path('category/<slug:slug>', views.CategoryProduct.as_view(), name='category_product'),
    path('favorite-products/<slug:slug>', views.MyFavorites.as_view(), name='favorite_products'),
    path('add-to-wishlist/<slug:slug>', views.wishlist, name='add_to_wishlist'),
    path('wishlist', views.WishListView.as_view(), name='wishlist'),
    path('auth', views.AuthView.as_view(), name='auth'),
    path('remove-from-wishlist/<int:id>', views.remove_from_wishlist, name='remove_from_wishlist'),
    path('orders', views.OrderView.as_view(), name='orders'),
    path('order-placing/<slug:slug>', views.CreateOrderView.as_view(), name='create_order'),
    path('profile', views.ProfileView.as_view(), name='profile'),
    path('settings', views.SettingsFormView.as_view(), name='settings'),
    path('update-password', views.UpdatePasswordFromView.as_view(), name='update_password'),
    path('cancel-order/<int:id>', views.CancelOrderView.as_view(), name='cancel_order'),
    path('recover-order/<int:id>', views.RecoverOrder.as_view(), name='recover_order'),
    path('wishlist-order/', views.WishlistOrderView.as_view(), name='wishlist_order'),
    path('search-product', views.SearchFormView.as_view(), name='search_product'),

]+ static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

urlpatterns+=[
path('market', views.MarketListview.as_view(), name='market'),
path('create-thread/', views.CreateThreadView.as_view(), name='create-thread'),
path('thread-list/', views.ThreadListView.as_view(), name='thread-list'),
path('thread-product/<slug:slug>', views.ThreadProduct.as_view(), name='thread_product'),
path('thread/<int:id>', views.ThreadToProductView.as_view(), name='thread_to_product'),
path('statistic', views.StatisticView.as_view(), name='statistic'),
path('questions', views.QuestionsView.as_view(), name='question'),
path('competition', views.CompetitionListView.as_view(), name='competition'),
path('create-order-via-thread/<slug:slug>', views.CreateOrderViaThreadView.as_view(), name='create_order_via_thread'),
path('payment', views.PaymentView.as_view(), name='payment'),
path('diagramms', views.DiagramTemplateView.as_view(), name='diagramms'),
]

urlpatterns+=[
    path('operator-page/',views.OperatorView.as_view(), name='operator_page'),
    path('get-districts',views.get_district_view, name='get_districts'),
    path('order-change/<int:pk>',views.OpratorChangeView.as_view(), name='order_change'),
    path('questions-for-paymant',views.OperatorPayment.as_view(), name='questions_for_paymant'),
    path('transaction/<int:pk>',views.OperatorTransaction.as_view(), name='transaction'),
]

urlpatterns+=[
    path('temp',views.TempTemplateView.as_view(), name='temp'),
    path('temp2',views.TempTemplateView2.as_view(), name='temp2'),
]