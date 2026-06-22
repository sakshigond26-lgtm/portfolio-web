from django.urls import path
from django.shortcuts import redirect
from . import views


urlpatterns = [
    path("", lambda request: redirect("register")),
    path("register/", views.register_view, name="register"),

    path("login/", views.login_view, name="login"),
    path("adminlogin/", views.adminlogin_view, name="adminlogin"),
    path("home/", views.home_view, name="home"),
    path("about/", views.about_view, name="about"),
    path("contact/", views.contact_view, name="contact"),
    path("category/", views.category_view, name="category"),
    path("upload/", views.upload_view, name="upload"),
    path("p_calculator/", views.p_calculator_view, name="p_calculator"),

    path('academic/', views.academic_view, name='academic'),
    path("comic/", views.comic_view, name="comic"),
    path("biography/", views.biography_view, name="biography"),
    path("fairy/", views.fairy_view, name="fairy"),
    path("fictional/", views.fictional_view, name="fictional"),
    path("recipie/", views.recipie_view, name="recipie"),
    path('historical/', views.historical_view, name='historical'),
    path('science/', views.science_view, name='science'),
    path("user_dashboard/",views.user_dashboard,name="user_dashboard"),
    path("order/", views.order_view, name="order"),
    path("cart/", views.cart_view, name="cart"),
    path('remove-cart/<str:book_id>/', views.removeCart, name='remove_cart'),
    path("wishlist/", views.wishlist_view, name="wishlist"),
    path('remove-wishlist/<str:book_id>/', views.removeWishlist, name='remove_wishlist'),
    path("myupload/", views.myupload_view, name="myupload"),
    path('book-detail/',views.books_detail_view,name='book_detail'),
    path('payment/', views.payment_page, name='payment_page'),
    path("set-book-session/<str:book_id>/", views.set_book_session_view, name="set_book_session"),
    path("add-to-cart/", views.addCart_view, name="add_to_cart"),
    path("add-to-wishlist/", views.addWishlist_view, name="add_to_wishlist"),
    path("buy-now/", views.buyNow_view, name="buy_now"),
    path("search/", views.search, name="search"),

    
    path("admin_dashboard/",views.admin_dashboard,name="admin_dashboard"),
    path("base_admin/",views.base_admin,name="base_admin"),
    path('book-approval/', views.book_approval, name='book_approval'),
    path('book-orders/', views.book_orders, name='book_orders'),
    path('manage-books/', views.manage_books, name='manage_books'),
    path('manage-users/', views.manage_users, name='manage_users'),
    path("book-approval/", views.book_approval, name="book_approval"),
    path("approve-book/<str:book_id>/", views.approve_book, name="approve_book"),
    path("reject-book/<str:book_id>/", views.reject_book, name="reject_book"),
    path('start-payment/', views.start_payment, name='start_payment'),
    path("logout/", views.logout_view, name="logout"),
    path('payment-success/', views.payment_success, name='payment_success'),
   
    
]
