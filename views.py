from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import login
from django.http import HttpResponse
from bookalay.utils.mongo import db
import hashlib
import cloudinary.uploader
from datetime import datetime
from django.contrib import messages
from django.views.decorators.cache import never_cache
from bson import ObjectId

# ==================================================✅ 🔐 Authentication Functions==================================#
# ================= REGISTER =================
@never_cache
def register_view(request):

    if request.method == "POST":

        username = request.POST.get("username", "")
        email = request.POST.get("email", "")
        dob = request.POST.get("dob", "")
        state = request.POST.get("state", "")
        password1 = request.POST.get("password1", "")
        c_password = request.POST.get("c_password", "")

        # empty validation
        if not username or not email or not password1 or not c_password:
            messages.error(request, "All fields are required")
            return render(request, "register.html")

        # password match
        if password1 != c_password:
            messages.error(request, "Password and Confirm Password must match")
            return render(request, "register.html")

        # username exist
        if db.User_register_data.find_one({"username": username}):
            messages.error(request, "Username already exists")
            return render(request, "register.html")

        # hash password
        hashed_password = hashlib.sha256(password1.encode()).hexdigest()

        user_data = {
            "username": username,
            "email": email,
            "dob": dob,
            "state": state,
            "password": hashed_password,
            "created_at": datetime.utcnow()
        }

        db.User_register_data.insert_one(user_data)

        messages.success(request, "Registration successful. Please login.")
        return redirect("login")

    return render(request, "register.html")


# ================= LOGIN =================
@never_cache
def login_view(request):

    if request.session.get("is_logged_in"):
        return redirect("home")

    if request.method == "POST":

        username = request.POST.get("username", "")
        password = request.POST.get("password", "")

        if not username or not password:
            messages.error(request, "Enter username and password")
            return render(request, "login.html")

        hashed_password = hashlib.sha256(password.encode()).hexdigest()

        user = db.User_register_data.find_one({"username": username})

        if not user:
            messages.error(request, "Account not found")
            return render(request, "login.html")

        if user["password"] != hashed_password:
            messages.error(request, "Wrong password")
            return render(request, "login.html")

        # LOGIN SUCCESS
        request.session.flush()
        request.session["user_id"] = str(user["_id"])
        request.session["username"] = user["username"]
        request.session["is_logged_in"] = True

        return redirect("home")

    return render(request, "login.html")

#======================Logout================#
from django.shortcuts import redirect
from django.views.decorators.cache import never_cache

@never_cache
def logout_view(request):
    # Clear all session data
    request.session.flush()

    return redirect("login")  # redirect to login page


#========================================================== ✅ 🏠 Main Pages======================================#
# ================= HOME =================
@never_cache
def home_view(request):

    if not request.session.get("is_logged_in"):
        return redirect("login")

    return render(request, "home.html", {
        "username": request.session.get("username")
    })

#==================ABOUT US================#
def about_view(request):
    if not request.session.get("is_logged_in"):
        return redirect("login")

    return render(request, 'aboutus.html', {
        "username": request.session.get("username")
    })

#==================CONTACT US================#
from django.shortcuts import render
from django.core.mail import send_mail

def contact_view(request):
    if not request.session.get("is_logged_in"):
        return redirect("login")

    if request.method == 'POST':
        name = request.POST.get('name')
        email = request.POST.get('email')
        message = request.POST.get('message')

        subject = f"New message from {name}"
        full_message = f"Name: {name}\nEmail: {email}\nMessage:\n{message}"

        send_mail(
            subject,
            full_message,
            'sakshirakeshgond@gmail.com',   # sender (IMPORTANT)
            ['sakshigond26@gmail.com'],     # 👈 admin email
        )

        return render(request, 'contactus.html', {'success': True})

    return render(request, 'contactus.html')

print("FORM SUBMITTED")

#============================================================ ✅ 💰 Price Calculator===============================#
#==================PRICE CALCULATOR================#

def pricecalculate_view(request):
    if not request.session.get("is_logged_in"):
        return redirect("login")

    return render(request, 'price_calculate.html', {
        "username": request.session.get("username")
    })

#==================PRICE CALCULATOR LOGIC================#
def p_calculator_view(request):
    context = {
        'show_result': False
    }

    if request.method == 'POST':
        print("POST DATA:", request.POST)
        try:
            mrp = float(request.POST.get('mrp'))
            book_age = request.POST.get('bookAge')
            book_condition = request.POST.get('bookCondition')

            resale_price = calculate_resale_price(mrp, book_age, book_condition)

            context.update({
                'mrp': mrp,
                'book_age': book_age,
                'book_condition': book_condition,
                'resale_price': resale_price,
                'show_result': True
            })

        except Exception as e:
            print("ERROR:", e)

    return render(request, 'p_calculator.html', context)

#==================NEW PRICE===============#
def calculate_resale_price(mrp, age, condition):
    age_factor = {
        '0-1': 0.80,
        '1-2': 0.70,
        '2-3': 0.60,
        '3+': 0.50
    }
    

    condition_factor = {
        'new': 0.90,
        'good': 0.80,
        'average': 0.70,
        'poor': 0.60
    }

    final_factor = age_factor.get(age, 0.40) * condition_factor.get(condition, 0.50)
    final_factor = max(final_factor, 0.10)

    return round(mrp * final_factor, 2)



# ======================================================✅ 📤 Upload System===================================================#

#==================UPLOAD ================#

def upload_view(request):
    if not request.session.get("is_logged_in"):
        return redirect("login")

    if request.method == "POST":
        try:
            title = request.POST.get("title")
            author = request.POST.get("author")
            mrp = request.POST.get("mrp")
            new_price = request.POST.get("new_price")
            category = request.POST.getlist("category")
            condition = request.POST.get("condition")
            book_age = request.POST.get("book_age")
            image_file = request.FILES.get("book_image")

             #✅ Get logged-in user from session
            username = request.session.get("username")
            user_id = request.session.get("user_id")


            # ---------- REQUIRED ----------
            if not all([title, author, mrp, new_price, category, condition, book_age, image_file]):
                messages.error(request, "All fields are required.")
                return redirect("upload")

            mrp = float(mrp)
            new_price = float(new_price)

            if mrp <= 0 or new_price <= 0:
                messages.error(request, "Prices must be greater than zero.")
                return redirect("upload")

            # ---------- PRICE RULE ----------
            condition_factor = {
                "Like New": 0.80,
                "Good": 0.70,
                "Average": 0.60,
                "Poor": 0.50
            }

            age_factor = {
                "Less than 1 year": 0.90,
                "1-2 years": 0.80,
                "2-3 years": 0.70,
                "More than 3 years": 0.60
            }

            allowed_price = mrp * condition_factor[condition] * age_factor[book_age]
            allowed_price = round(allowed_price, 2)

            # ❗ CORRECT VALIDATION
            if new_price > allowed_price:
                messages.error(
                    request,
                    f"Invalid New Price ,Please Enter Valid Price or Try Price Calculator"
                )
                return redirect("upload")

            # ---------- IMAGE UPLOAD ----------
            upload_result = cloudinary.uploader.upload(
                image_file,
                folder="bookalay_books"
            )

            image_url = upload_result.get("secure_url")

            db.books.insert_one({
                "title": title,
                "author": author,
                "mrp": mrp,
                "new_price": new_price,
                "category": category,
                "condition": condition,
                "book_age": book_age,
                "uploaded_by": username,    
                "user_id": user_id,       
                "image_url": image_url,
                "status": False,
            })

            messages.success(request, "📚 Book uploaded successfully!")
            

        except Exception as e:
            messages.error(request, f"Upload failed: {e}")
            return redirect("upload")

    return render(request, "upload.html")


# ========================================================✅ 📚 Category System============================================#

#==================CATEGORY================#

def category_view(request):
    if not request.session.get("is_logged_in"):
        return redirect("login")

    return render(request, 'category.html',{
        "username": request.session.get("username")
    })

#=====================================CATRGORY PAGES===========================#

def academic_view(request):
    if not request.session.get("is_logged_in"):
        return redirect("login")

    try:
        books_collection = db["books"]

        academic_books_cursor = books_collection.find({
            "category": {"$regex": "^academic$", "$options": "i"},
            "status": True
        })

        academic_books = []

        for book in academic_books_cursor:
            academic_books.append({
                "id": str(book.get("_id")),
                "title": book.get("title"),
                "author": book.get("author"),
                "new_price": book.get("new_price"),
                "image_url": book.get("image_url"),
                "category": book.get("category"),
                "condition": book.get("condition"),
                "book_age": book.get("book_age"),
            })

        return render(request, 'academic.html', {
            "username": request.session.get("username"),
            "academic_books": academic_books
        })

    except Exception as e:
        print("Error fetching academic books:", e)
        return render(request, 'academic.html', {
            "username": request.session.get("username"),
            "academic_books": []
        })

def historical_view(request):
    if not request.session.get("is_logged_in"):
        return redirect("login")

    try:
        books_collection = db["books"]

        cursor = books_collection.find({
            "category": {"$regex": "^historical$", "$options": "i"},
            "status": True
        })

        books = []
        for book in cursor:
            books.append({
                "id": str(book.get("_id")),
                "title": book.get("title"),
                "author": book.get("author"),
                "new_price": book.get("new_price"),
                "image_url": book.get("image_url"),
                "category": book.get("category"),
                "condition": book.get("condition"),
                "book_age": book.get("book_age"),
            })

        return render(request, 'historical.html', {
            "username": request.session.get("username"),
            "historical_books": books
        })

    except Exception as e:
        print("Error:", e)
        return render(request, 'historical.html', {
            "username": request.session.get("username"),
            "historical_books": []
        })

def science_view(request):
    if not request.session.get("is_logged_in"):
        return redirect("login")

    try:
        books_collection = db["books"]

        cursor = books_collection.find({
            "category": {"$regex": "^science$", "$options": "i"},
            "status": True
        })

        books = []
        for book in cursor:
            books.append({
                "id": str(book.get("_id")),
                "title": book.get("title"),
                "author": book.get("author"),
                "new_price": book.get("new_price"),
                "image_url": book.get("image_url"),
                "category": book.get("category"),
                "condition": book.get("condition"),
                "book_age": book.get("book_age"),
            })

        return render(request, 'science.html', {
            "username": request.session.get("username"),
            "science_books": books
        })

    except Exception as e:
        print("Error:", e)
        return render(request, 'science.html', {
            "username": request.session.get("username"),
            "science_books": []
        })

def biography_view(request):
    if not request.session.get("is_logged_in"):
        return redirect("login")

    try:
        books_collection = db["books"]

        cursor = books_collection.find({
            "category": {"$regex": "^biography$", "$options": "i"},
            "status": True
        })

        books = []
        for book in cursor:
            books.append({
                "id": str(book.get("_id")),
                "title": book.get("title"),
                "author": book.get("author"),
                "new_price": book.get("new_price"),
                "image_url": book.get("image_url"),
                "category": book.get("category"),
                "condition": book.get("condition"),
                "book_age": book.get("book_age"),
            })

        return render(request, 'biography.html', {
            "username": request.session.get("username"),
            "biography_books": books
        })

    except Exception as e:
        print("Error:", e)
        return render(request, 'biography.html', {
            "username": request.session.get("username"),
            "biography_books": []
        })

def recipie_view(request):
    if not request.session.get("is_logged_in"):
        return redirect("login")

    try:
        books_collection = db["books"]

        cursor = books_collection.find({
            "category": {"$regex": "^recipe$", "$options": "i"},
            "status": True
        })

        books = []
        for book in cursor:
            books.append({
                "id": str(book.get("_id")),
                "title": book.get("title"),
                "author": book.get("author"),
                "new_price": book.get("new_price"),
                "image_url": book.get("image_url"),
                "category": book.get("category"),
                "condition": book.get("condition"),
                "book_age": book.get("book_age"),
            })

        return render(request, 'recipie.html', {
            "username": request.session.get("username"),
            "recipie_books": books
        })

    except Exception as e:
        print("Error:", e)
        return render(request, 'recipie.html', {
            "username": request.session.get("username"),
            "recipie_books": []
        })
    

def fictional_view(request):
    if not request.session.get("is_logged_in"):
        return redirect("login")

    try:
        books_collection = db["books"]

        cursor = books_collection.find({
            "category": {"$regex": "^fictional$", "$options": "i"},
            "status": True
        })

        books = []
        for book in cursor:
            books.append({
                "id": str(book.get("_id")),
                "title": book.get("title"),
                "author": book.get("author"),
                "new_price": book.get("new_price"),
                "image_url": book.get("image_url"),
                "category": book.get("category"),
                "condition": book.get("condition"),
                "book_age": book.get("book_age"),
            })

        return render(request, 'fictional.html', {
            "username": request.session.get("username"),
            "fictional_books": books
        })

    except Exception as e:
        print("Error:", e)
        return render(request, 'fictional.html', {
            "username": request.session.get("username"),
            "fictional_books": []
        })
    

def comic_view(request):
    if not request.session.get("is_logged_in"):
        return redirect("login")

    try:
        books_collection = db["books"]

        cursor = books_collection.find({
            "category": {"$regex": "^comic$", "$options": "i"},
            "status": True
        })

        books = []
        for book in cursor:
            books.append({
                "id": str(book.get("_id")),
                "title": book.get("title"),
                "author": book.get("author"),
                "new_price": book.get("new_price"),
                "image_url": book.get("image_url"),
                "category": book.get("category"),
                "condition": book.get("condition"),
                "book_age": book.get("book_age"),
            })

        return render(request, 'comic.html', {
            "username": request.session.get("username"),
            "comic_books": books
        })

    except Exception as e:
        print("Error:", e)
        return render(request, 'comic.html', {
            "username": request.session.get("username"),
            "comic_books": []
        })
    
def fairy_view(request):
    if not request.session.get("is_logged_in"):
        return redirect("login")

    try:
        books_collection = db["books"]

        cursor = books_collection.find({
            "category": {"$regex": "^fairy$", "$options": "i"},
            "status": True
        })

        books = []
        for book in cursor:
            books.append({
                "id": str(book.get("_id")),
                "title": book.get("title"),
                "author": book.get("author"),
                "new_price": book.get("new_price"),
                "image_url": book.get("image_url"),
                "category": book.get("category"),
                "condition": book.get("condition"),
                "book_age": book.get("book_age"),
            })

        return render(request, 'fairy.html', {
            "username": request.session.get("username"),
            "fairy_books": books
        })

    except Exception as e:
        print("Error:", e)
        return render(request, 'fairy.html', {
            "username": request.session.get("username"),
            "fairy_books": []
        })


#=====================================# ✅ 👤 User Dashboard Pages=================================================#

#==================USER DASHBOARD================#
def user_dashboard(request):
    if not request.session.get("is_logged_in"):
        return redirect("login")

    username = request.session.get("username")

    # ✅ Correct collection names
    orders_collection = db["order_collection"]
    wishlist_collection = db["wishlist_collection"]
    books_collection = db["books"]

    # ✅ Counts
    total_orders = orders_collection.count_documents({"username": username})
    total_wishlist = wishlist_collection.count_documents({"username": username})
    total_uploads = books_collection.count_documents({"uploaded_by": username})

    print("USERNAME:", username)
    print("ORDERS:", total_orders)
    print("WISHLIST:", total_wishlist)
    print("UPLOADS:", total_uploads)

    context = {
        "total_orders": total_orders,
        "total_wishlist": total_wishlist,
        "total_uploads": total_uploads
    }

    return render(request, 'user_dashboard.html', context)

#==================ORDER================#
from django.shortcuts import render, redirect
from bookalay.utils.mongo import db
from bson import ObjectId

def order_view(request):
    if not request.session.get("is_logged_in"):
        return redirect("login")

    username = request.session.get("username")

    orders_collection = db["order_collection"]   # ✅ FIXED
    books_collection = db["books"]

    orders_cursor = orders_collection.find({"username": username})

    books = []

    for order in orders_cursor:
        book_id = order.get("book_id")

        try:
            book = books_collection.find_one({"_id": ObjectId(book_id)})
        except:
            book = None   # agar ObjectId fail ho

        if book:
            book_data = {
                "id": str(book["_id"]),
                "title": book.get("title"),
                "author": book.get("author"),
                "condition": book.get("condition"),
                "age": book.get("age"),
                "image_url": book.get("image_url"),
            }

            books.append(book_data)

    return render(request, "order.html", {"books": books})

#==================CART================#
def cart_view(request):
    # Check login
    if not request.session.get("is_logged_in"):
        return redirect("login")

    # Get user_id from session
    user_id = request.session.get("user_id")

    if not user_id:
        return redirect("login")

    # Access cart collection
    cart_collection = db["cart_collection"]

    # Fetch cart data for the user
    cart_data = list(
        cart_collection.find({"user_id": user_id})
    )

    # Render cart page with data
    return render(request, "cart.html", {
        "books": cart_data
    })

#==================MY UPLOAD================#
def myupload_view(request):
    if not request.session.get("is_logged_in"):
        return redirect("login")

    user_id = request.session.get("user_id")

    if not user_id:
        return redirect("login")

    books_collection = db["books"]

    user_books_cursor = books_collection.find({
        "user_id": user_id
    })

    user_books = []

    for book in user_books_cursor:
        user_books.append({
            "id": str(book.get("_id")),
            "title": book.get("title"),
            "author": book.get("author"),
            "new_price": book.get("new_price"),
            "image_url": book.get("image_url"),
            "condition": book.get("condition"),
            "book_age": book.get("book_age"),
            "status": book.get("status"),
        })

    return render(request, "myupload.html", {
        "books": user_books
    })
#========================wishlist=============================#

def wishlist_view(request):
    if not request.session.get("is_logged_in"):
        return redirect("login")

    user_id = request.session.get("user_id")

    if not user_id:
        return redirect("login")

    wishlist_collection = db["wishlist_collection"]

    wishlist_data = list(
        wishlist_collection.find({"user_id": user_id})
    )

    return render(request, "wishlist.html", {
        "books": wishlist_data
    })

#================Remove From Cart===========#
def removeCart(request, book_id):
    try:
        user_id = request.session.get("user_id")

        if not user_id:
            return redirect("login")

        cart_collection = db["cart_collection"]

        # Delete that book from user's cart
        result = cart_collection.delete_one({
            "user_id": user_id,
            "book_id": book_id
        })

        if result.deleted_count > 0:
            messages.success(request, "🗑️ Book removed from cart")
        else:
            messages.error(request, "Item not found in cart")

        return redirect("cart")

    except Exception as e:
        messages.error(request, f"Error removing item: {e}")
        return redirect("cart")

#==============Remove from WishList============#
from django.contrib import messages
from django.shortcuts import redirect
from bookalay.utils.mongo import db

def removeWishlist(request, book_id):
    try:
        user_id = request.session.get("user_id")

        if not user_id:
            return redirect("login")

        wishlist_collection = db["wishlist_collection"]

        # Delete book from wishlist
        result = wishlist_collection.delete_one({
            "user_id": user_id,
            "book_id": book_id
        })

        if result.deleted_count > 0:
            messages.success(request, "❤️ Removed from wishlist")
        else:
            messages.error(request, "Item not found in wishlist")

        return redirect("wishlist")

    except Exception as e:
        messages.error(request, f"Error removing item: {e}")
        return redirect("wishlist")


#======================================================================= ✅ 🛠 ADMIN PAGES===========================#

@never_cache
def adminlogin_view(request):

    if request.session.get("is_admin_logged_in"):
        return redirect("admin_dashboard")

    if request.method == "POST":

        username = request.POST.get("a_username", "")
        password = request.POST.get("a_password", "")

        if not username or not password:
            messages.error(request, "Enter admin username and password")
            return redirect("adminlogin")

        admin = db.Admin.find_one({"a_username": username})

        if not admin:
            messages.error(request, "Admin account not found")
            return redirect("adminlogin")

        # Hash password before checking
        hashed_password = hashlib.sha256(password.encode()).hexdigest()

        if admin["password"] != hashed_password:
            messages.error(request, "Wrong password")
            return redirect("adminlogin")

        # SUCCESS
        request.session.flush()
        request.session["admin_id"] = str(admin["_id"])
        request.session["admin_username"] = admin["a_username"]
        request.session["is_admin_logged_in"] = True

        return redirect("admin_dashboard")

    return render(request, "adminlogin.html")




def base_admin(request):
    return render(request,'base_admin.html')

#==========admin dashboard========#

def admin_dashboard(request):

    users_collection = db["User_register_data"]
    books_collection = db["books"]
    orders_collection = db["order_collection"]

    # ✅ Counts
    total_users = users_collection.count_documents({})
    total_books = books_collection.count_documents({"status": True})
    pending_books = books_collection.count_documents({"status": False})
    total_orders = orders_collection.count_documents({})

    context = {
        "total_users": total_users,
        "total_books": total_books,
        "pending_books": pending_books,
        "total_orders": total_orders
    }

    return render(request, 'admin_dashboard.html', context)


#==========book_orders========#d

def book_orders(request):

    orders_collection = db["order_collection"]
    books_collection = db["books"]

    orders_cursor = orders_collection.find()

    orders_list = []

    for order in orders_cursor:
        book = None

        try:
            book = books_collection.find_one({
                "_id": ObjectId(order.get("book_id"))
            })
        except:
            book = None

        order_data = {
            "order_id": str(order.get("_id")),
            "buyer": order.get("username"),   # 👈 buyer = username
            "book_name": book.get("title") if book else "N/A",
            "price": order.get("price"),
            "date": order.get("created_at"),
        }

        orders_list.append(order_data)

    return render(request, 'book_orders.html', {"orders": orders_list})

#==========book_approval=========#
def book_approval(request):

    if not request.session.get("is_admin_logged_in"):
        return redirect("adminlogin")

    books_collection = db["books"]

    # ✅ Fetch ONLY pending books
    books_cursor = books_collection.find({"status": False})

    books = []
    for book in books_cursor:
        books.append({
            "id": str(book["_id"]),
            "name": book.get("title"),
            "seller": book.get("uploaded_by"),
            "price": book.get("new_price" ),
            "status": book.get("status", False)
        })

    return render(request, "book_approval.html", {"books": books})

from bson import ObjectId

def approve_book(request, book_id):

    db["books"].update_one(
        {"_id": ObjectId(book_id)},
        {"$set": {"status": True}}
    )

    return redirect("book_approval")

def reject_book(request, book_id):
    db["books"].delete_one({"_id": ObjectId(book_id)})
    return redirect("book_approval")

#==========manage_books=========#
def manage_books(request):

    if not request.session.get("is_admin_logged_in"):
        return redirect("adminlogin")
    
    admin_username = request.session.get("admin_username")

    books_collection = db["books"]
    books_cursor = books_collection.find({"status": True})

    books_list = []

    # ✅ Extract and store in variables
    for book in books_cursor:
        book_data = {
            "id": str(book["_id"]),
            "name": book.get("title"),        # safe access
            "seller": book.get("uploaded_by"),
            "price": book.get("new_price"),
            "status": book.get("status")
        }
        books_list.append(book_data)

    return render(request, 'manage_books.html', {
        "books": books_list,
        "admin_username": admin_username
    })

#=======manage_users===========#
def manage_users(request):

    # ✅ Admin authentication check
    if not request.session.get("is_admin_logged_in"):
        return redirect("adminlogin")
    
    admin_username = request.session.get("admin_username")

    users_collection = db["User_register_data"]

    # 👉 Fetch all users (you can filter if needed)
    users_cursor = users_collection.find()

    users_list = []

    # ✅ Extract required fields safely
    for user in users_cursor:
        user_data = {
            "id": str(user.get("_id")),
            "name": user.get("username"),
            "email": user.get("email"),
            "state": user.get("state")  # or status if you use that
        }
        users_list.append(user_data)

    return render(request, 'manage_users.html', {
        "users": users_list,
        "admin_username": admin_username
    })


# ====================== Set Book ID in Session ===================== #
def set_book_session_view(request, book_id):
    try:
        request.session["selected_book_id"] = book_id

        category = request.GET.get("category")
        if category:
            request.session["current_category"] = category

        return redirect("book_detail")

    except Exception as e:
        print("Error setting book session:", e)

        category = request.session.get("current_category", "academic")
        return redirect(category)

# ====================== Book Detail View ===================== #
def books_detail_view(request):
    if not request.session.get("is_logged_in"):
        return redirect("login")

    try:
        books_collection = db["books"]
 
        # Get book id from session
        book_id = request.session.get("selected_book_id")

        if not book_id:
            category = request.session.get("current_category", "academic")
            return redirect(category)


        # Search database using session book id
        book_obj = books_collection.find_one({"_id": ObjectId(book_id)})

        if not book_obj:
            category = request.session.get("current_category", "academic")
            return redirect(category)


        # Store data in variables
        book_title = book_obj.get("title")
        book_author = book_obj.get("author")
        book_new_price = book_obj.get("new_price")
        book_image_url = book_obj.get("image_url")
        book_condition = book_obj.get("condition")
        book_book_age = book_obj.get("book_age")

        # Send data to template
        context = {
            "book": {
                "id": str(book_obj.get("_id")),
                "title": book_title,
                "author": book_author,
                "new_price": book_new_price,
                "image_url": book_image_url,
                "condition": book_condition,
                "book_age": book_book_age,
            }
        }

        return render(request, "book.html", context)

    except Exception as e:
        print("Error fetching book detail:", e)
        category = request.session.get("current_category", "academic")
        return redirect(category)



# ===========================================================✅ 🛒 Cart & Wishlist=========================================#

def addCart_view(request):
    try:
        username = request.session.get("username")
        user_id = request.session.get("user_id")
        book_id = request.session.get("selected_book_id")

        if not username or not user_id or not book_id:
            return redirect("book_detail")

        books_collection = db["books"]
        cart_collection = db["addToCart"]

        book_obj = books_collection.find_one({"_id": ObjectId(book_id)})

        if not book_obj:
            return redirect("book_detail")

        # Prevent duplicate
        existing = cart_collection.find_one({
            "user_id": user_id,
            "book_id": str(book_obj.get("_id"))
        })

        if not existing:
            db.cart_collection.insert_one({
                "user_id": user_id,
                "username": username,
                "book_id": str(book_obj.get("_id")),
                "title": book_obj.get("title"),
                "author": book_obj.get("author"),
                "new_price": book_obj.get("new_price"),
                "image_url": book_obj.get("image_url"),
                "condition": book_obj.get("condition"),
                "book_age": book_obj.get("book_age"),
                "category": book_obj.get("category"),
                "added_at": datetime.now()
            })

        messages.success(request, "🛒 Book added to cart successfully!")
        return redirect("book_detail")

    except Exception as e:
        messages.error(request, f"Error adding to cart: {e}")
        return redirect("book_detail")


# ====================== Buy Now ===================== #
def buyNow_view(request):
    try:
        book_id = request.session.get("selected_book_id")

        if not book_id:
            return redirect("book_detail")

        books_collection = db["books"]

        # ✅ Book fetch
        book = books_collection.find_one({"_id": ObjectId(book_id), "status": True})

        if not book:
            messages.error(request, "Book not found")
            return redirect("book_detail")

        # ✅ session me save karo (payment page ke liye)
        request.session["buy_now_book"] = str(book["_id"])

        return redirect("payment_page")

    except Exception as e:
        messages.error(request, f"Error: {e}")
        return redirect("book_detail")



# ====================== Add to wishlist===================== #
def addWishlist_view(request):
    try:
        username = request.session.get("username")
        user_id = request.session.get("user_id")
        book_id = request.session.get("selected_book_id")

        if not username or not user_id or not book_id:
            return redirect("book_detail")

        books_collection = db["books"]
        wishlist_collection = db["whishlist"]

        book_obj = books_collection.find_one({"_id": ObjectId(book_id)})

        if not book_obj:
            return redirect("book_detail")

        # Prevent duplicate
        existing = wishlist_collection.find_one({
            "user_id": user_id,
            "book_id": str(book_obj.get("_id"))
        })

        if not existing:
            db.wishlist_collection.insert_one({
                "user_id": user_id,
                "username": username,
                "book_id": str(book_obj.get("_id")),
                "title": book_obj.get("title"),
                "author": book_obj.get("author"),
                "new_price": book_obj.get("new_price"),
                "image_url": book_obj.get("image_url"),
                "condition": book_obj.get("condition"),
                "book_age": book_obj.get("book_age"),
                "category": book_obj.get("category"),
                "added_at": datetime.now()
            })

        messages.success(request, "❤️ Added to wishlist successfully!")
        return redirect("book_detail")

    except Exception as e:
        messages.error(request, f"Error adding to wishlist: {e}")
        return redirect("book_detail")
    

# ======================================================✅ 💳 Payment System==================================================#
#####=======================payment page===========####
from django.shortcuts import render, redirect
from bson import ObjectId
from bookalay.utils.mongo import db

def payment_page(request):
    try:
        book_id = request.session.get("buy_now_book")

        if not book_id:
            return redirect("book_detail")

        books_collection = db["books"]
        book = books_collection.find_one({"_id": ObjectId(book_id)})

        if not book:
            return redirect("book_detail")

        price = float(book.get("new_price", 0))
        delivery = 30
        handling = 5
        convenience = 15

        total = price + delivery + handling + convenience

        context = {
            "book": book,
            "price": price,
            "delivery": delivery,
            "handling": handling,
            "convenience": convenience,
            "total": total
        }

        return render(request, "payment.html", context)

    except Exception as e:
        print("ERROR:", e)
        return redirect("book_detail")
    

    
############start payment========#
import razorpay
from django.http import JsonResponse
from django.conf import settings
from bson import ObjectId
from bookalay.utils.mongo import db
import json

def start_payment(request):
    try:
        data = json.loads(request.body)
        address = data.get("address")

        if not address:
            return JsonResponse({"error": "Address required"})

        book_id = request.session.get("buy_now_book")
        user_id = request.session.get("user_id")
        username = request.session.get("username")

        books_collection = db["books"]
        book = books_collection.find_one({"_id": ObjectId(book_id)})

        if not book:
            return JsonResponse({"error": "Book not found"})

        price = float(book.get("new_price", 0))
        total = price + 30 + 5 + 15

        # ✅ session save
        request.session["order_data"] = {
            "user_id": user_id,
            "username": username,
            "book_id": str(book["_id"]),
            "title": book.get("title"),
            "price": price,
            "total_price": total,
            "address": address
        }

        amount = int(total * 100)

        client = razorpay.Client(
            auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET)
        )

        payment = client.order.create({
            "amount": amount,
            "currency": "INR"
        })

        return JsonResponse({
            "key": settings.RAZORPAY_KEY_ID,
            "amount": amount,
            "order_id": payment["id"]
        })

    except Exception as e:
        return JsonResponse({"error": str(e)})
    
#==================payment Success===============#
from django.shortcuts import redirect
from datetime import datetime
from bookalay.utils.mongo import db

def payment_success(request):
    try:
        order_data = request.session.get("order_data")

        if not order_data:
            return redirect("home")

        payment_id = request.GET.get("payment_id")

        orders_collection = db["order_collection"]

        order_data["payment_id"] = payment_id
        order_data["status"] = "Paid"
        order_data["created_at"] = datetime.now()

        orders_collection.insert_one(order_data)


        # session clear
        del request.session["order_data"]

        return redirect("user_dashboard")

    except Exception as e:
        print("PAYMENT ERROR:", e)
        return redirect("home")
    




# ======================================================✅🔍 Search System==================================================#
import re
from django.shortcuts import render
from django.contrib import messages   # ✅ ADD THIS
from bookalay.utils.mongo import db

def search(request):
    books_collection = db["books"]

    query = request.GET.get("query", "").strip()
    category = request.GET.get("category", "all")

    normalized_query = re.sub(r"\s+", "", query.lower())

    filter_query = {
        "status": True
    }

    if category != "all":
        filter_query["category"] = {"$regex": f"^{category}$", "$options": "i"}

    books = books_collection.find(filter_query)

    results = []

    for book in books:
        title = book.get("title", "").lower()
        author = book.get("author", "").lower()

        normalized_title = re.sub(r"\s+", "", title)
        normalized_author = re.sub(r"\s+", "", author)

        if normalized_query in normalized_title or normalized_query in normalized_author:
            results.append({
                "id": str(book["_id"]),
                "title": book.get("title"),
                "author": book.get("author"),
                "new_price": book.get("new_price"),
                "image_url": book.get("image_url"),
            })

    # ✅ IMPORTANT: EMPTY RESULT MESSAGE
    if query and len(results) == 0:
        messages.error(request, "No search data found")

    return render(request, "category.html", {
        "search_results": results,
        "query": query
    })



