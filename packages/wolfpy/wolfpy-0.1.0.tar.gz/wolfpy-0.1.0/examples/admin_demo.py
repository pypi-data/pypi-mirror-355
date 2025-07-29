#!/usr/bin/env python3
"""
WolfPy Admin Dashboard Demo

This example demonstrates the Django-style admin interface for WolfPy.
It shows how to:
- Set up models with the ORM
- Register models with the admin interface
- Create custom admin configurations
- Set up admin users and permissions
- Access the admin dashboard at /admin

Run this example:
    python examples/admin_demo.py

Then visit:
    http://localhost:8000/admin

Default admin credentials:
    Username: admin
    Password: admin123
"""

import os
import sys
from datetime import datetime

# Add the src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from wolfpy import WolfPy
from wolfpy.core.database import Model, IntegerField, StringField, EmailField, DateTimeField, BooleanField, TextField
from wolfpy.core.admin import ModelAdmin, site as admin_site, register as admin_register
from wolfpy.core.response import Response


# Define some example models
class User(Model):
    """User model for the demo."""
    id = IntegerField(primary_key=True)
    username = StringField(max_length=50, unique=True)
    email = EmailField()
    first_name = StringField(max_length=30)
    last_name = StringField(max_length=30)
    is_active = BooleanField(default=True)
    is_staff = BooleanField(default=False)
    date_joined = DateTimeField(auto_now_add=True)
    last_login = DateTimeField()

    def __str__(self):
        return f"{self.username} ({self.email})"

    class Meta:
        verbose_name = "User"
        verbose_name_plural = "Users"


class BlogPost(Model):
    """Blog post model for the demo."""
    id = IntegerField(primary_key=True)
    title = StringField(max_length=200)
    slug = StringField(max_length=200, unique=True)
    content = TextField()
    author_id = IntegerField()  # Foreign key to User
    published = BooleanField(default=False)
    created_at = DateTimeField(auto_now_add=True)
    updated_at = DateTimeField(auto_now=True)
    view_count = IntegerField(default=0)

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = "Blog Post"
        verbose_name_plural = "Blog Posts"


class Category(Model):
    """Category model for the demo."""
    id = IntegerField(primary_key=True)
    name = StringField(max_length=100, unique=True)
    description = TextField()
    created_at = DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Category"
        verbose_name_plural = "Categories"


# Custom admin configurations
class UserAdmin(ModelAdmin):
    """Custom admin for User model."""
    
    def __init__(self, model):
        super().__init__(model)
        self.list_display = ['username', 'email', 'first_name', 'last_name', 'is_active', 'date_joined']
        self.list_filter = ['is_active', 'is_staff']
        self.search_fields = ['username', 'email', 'first_name', 'last_name']
        self.list_per_page = 20
        self.ordering = ['-date_joined']


class BlogPostAdmin(ModelAdmin):
    """Custom admin for BlogPost model."""
    
    def __init__(self, model):
        super().__init__(model)
        self.list_display = ['title', 'author_id', 'published', 'created_at', 'view_count']
        self.list_filter = ['published']
        self.search_fields = ['title', 'content']
        self.list_per_page = 15
        self.ordering = ['-created_at']


class CategoryAdmin(ModelAdmin):
    """Custom admin for Category model."""
    
    def __init__(self, model):
        super().__init__(model)
        self.list_display = ['name', 'description', 'created_at']
        self.search_fields = ['name', 'description']
        self.ordering = ['name']


# Create WolfPy application
app = WolfPy(debug=True, enable_admin=True)

# Set up database
app.database.create_tables(User, BlogPost, Category)

# Register models with admin
admin_register(User, UserAdmin)
admin_register(BlogPost, BlogPostAdmin)
admin_register(Category, CategoryAdmin)

# Register admin routes
admin_site.register_routes(app)

# Create some sample data
def create_sample_data():
    """Create sample data for the demo."""
    try:
        # Check if data already exists
        if User.objects.count() > 0:
            return
        
        # Create sample users
        users_data = [
            {
                'username': 'john_doe',
                'email': 'john@example.com',
                'first_name': 'John',
                'last_name': 'Doe',
                'is_active': True,
                'is_staff': True
            },
            {
                'username': 'jane_smith',
                'email': 'jane@example.com',
                'first_name': 'Jane',
                'last_name': 'Smith',
                'is_active': True,
                'is_staff': False
            },
            {
                'username': 'bob_wilson',
                'email': 'bob@example.com',
                'first_name': 'Bob',
                'last_name': 'Wilson',
                'is_active': False,
                'is_staff': False
            }
        ]
        
        for user_data in users_data:
            user = User(**user_data)
            user.save()
        
        # Create sample categories
        categories_data = [
            {'name': 'Technology', 'description': 'Posts about technology and programming'},
            {'name': 'Lifestyle', 'description': 'Posts about lifestyle and personal development'},
            {'name': 'Travel', 'description': 'Posts about travel and adventures'}
        ]
        
        for cat_data in categories_data:
            category = Category(**cat_data)
            category.save()
        
        # Create sample blog posts
        posts_data = [
            {
                'title': 'Getting Started with WolfPy',
                'slug': 'getting-started-wolfpy',
                'content': 'WolfPy is a powerful Python web framework that makes building web applications easy and fun.',
                'author_id': 1,
                'published': True,
                'view_count': 150
            },
            {
                'title': 'Advanced Database Queries',
                'slug': 'advanced-database-queries',
                'content': 'Learn how to write complex database queries using WolfPy ORM.',
                'author_id': 1,
                'published': True,
                'view_count': 89
            },
            {
                'title': 'Building RESTful APIs',
                'slug': 'building-restful-apis',
                'content': 'A comprehensive guide to building RESTful APIs with WolfPy.',
                'author_id': 2,
                'published': False,
                'view_count': 23
            }
        ]
        
        for post_data in posts_data:
            post = BlogPost(**post_data)
            post.save()
        
        print("✅ Sample data created successfully!")
        
    except Exception as e:
        print(f"❌ Error creating sample data: {e}")


# Create additional admin users
def setup_admin_users():
    """Set up additional admin users."""
    try:
        # Create a content editor with limited permissions
        admin_site.create_admin_user(
            username="editor",
            password="editor123",
            email="editor@example.com",
            is_superuser=False,
            permissions=[
                "view_blogpost", "add_blogpost", "change_blogpost",
                "view_category", "add_category", "change_category",
                "view_user"
            ]
        )
        
        # Create a viewer with read-only access
        admin_site.create_admin_user(
            username="viewer",
            password="viewer123",
            email="viewer@example.com",
            is_superuser=False,
            permissions=["view_user", "view_blogpost", "view_category"]
        )
        
        print("✅ Additional admin users created!")
        print("   - editor/editor123 (can edit posts and categories)")
        print("   - viewer/viewer123 (read-only access)")
        
    except Exception as e:
        print(f"❌ Error creating admin users: {e}")


# Routes for the main application
@app.route('/')
def home(request):
    """Home page with links to admin."""
    return Response("""
    <!DOCTYPE html>
    <html>
    <head>
        <title>WolfPy Admin Demo</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 40px; }
            .container { max-width: 800px; margin: 0 auto; }
            .admin-link { 
                display: inline-block; 
                background: #417690; 
                color: white; 
                padding: 15px 25px; 
                text-decoration: none; 
                border-radius: 5px; 
                margin: 10px 0;
            }
            .admin-link:hover { background: #205067; }
            .credentials { 
                background: #f8f8f8; 
                padding: 15px; 
                border-radius: 5px; 
                margin: 20px 0;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🐺 WolfPy Admin Dashboard Demo</h1>
            <p>This demo showcases the Django-style admin interface for WolfPy.</p>
            
            <h2>Features Demonstrated:</h2>
            <ul>
                <li>Model registration with custom admin configurations</li>
                <li>User authentication and permissions</li>
                <li>CRUD operations for database models</li>
                <li>Search and filtering capabilities</li>
                <li>Pagination and list views</li>
                <li>Form handling and validation</li>
            </ul>
            
            <div class="credentials">
                <h3>Admin Credentials:</h3>
                <p><strong>Superuser:</strong> admin / admin123</p>
                <p><strong>Editor:</strong> editor / editor123 (limited permissions)</p>
                <p><strong>Viewer:</strong> viewer / viewer123 (read-only)</p>
            </div>
            
            <a href="/admin/" class="admin-link">🔧 Access Admin Dashboard</a>
            
            <h2>Sample Data:</h2>
            <p>The demo includes sample users, blog posts, and categories to explore.</p>
        </div>
    </body>
    </html>
    """)


if __name__ == '__main__':
    print("🐺 Starting WolfPy Admin Demo...")
    print("=" * 50)
    
    # Create sample data
    create_sample_data()
    
    # Set up additional admin users
    setup_admin_users()
    
    print("\n📊 Admin Dashboard Information:")
    print(f"   URL: http://localhost:8000/admin/")
    print(f"   Default admin: admin / admin123")
    print(f"   Models registered: {len(admin_site.get_registered_models())}")
    
    print("\n🚀 Starting server on http://localhost:8000")
    print("   Visit http://localhost:8000 for demo info")
    print("   Visit http://localhost:8000/admin for admin dashboard")
    print("=" * 50)
    
    app.run(host='0.0.0.0', port=8000)
