#!/usr/bin/env python3
"""
WolfPy Blog Example

A complete blog application demonstrating:
- User authentication and registration
- CRUD operations for blog posts
- Template rendering with Mako
- Database models and relationships
- Admin interface
- Static file serving
"""

import os
import sys
from pathlib import Path

# Add WolfPy to path for development
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from wolfpy import WolfPy
from wolfpy.core.response import Response
from wolfpy.core.database import Model
from wolfpy.auth.decorators import login_required
from datetime import datetime


# Database Models
class User(Model):
    """User model for authentication."""
    table_name = 'users'
    fields = {
        'id': 'INTEGER PRIMARY KEY AUTOINCREMENT',
        'username': 'TEXT UNIQUE NOT NULL',
        'email': 'TEXT UNIQUE NOT NULL',
        'password_hash': 'TEXT NOT NULL',
        'is_admin': 'BOOLEAN DEFAULT FALSE',
        'created_at': 'TIMESTAMP DEFAULT CURRENT_TIMESTAMP'
    }


class Post(Model):
    """Blog post model."""
    table_name = 'posts'
    fields = {
        'id': 'INTEGER PRIMARY KEY AUTOINCREMENT',
        'title': 'TEXT NOT NULL',
        'content': 'TEXT NOT NULL',
        'author_id': 'INTEGER NOT NULL',
        'slug': 'TEXT UNIQUE NOT NULL',
        'published': 'BOOLEAN DEFAULT FALSE',
        'created_at': 'TIMESTAMP DEFAULT CURRENT_TIMESTAMP',
        'updated_at': 'TIMESTAMP DEFAULT CURRENT_TIMESTAMP'
    }


class Comment(Model):
    """Comment model for blog posts."""
    table_name = 'comments'
    fields = {
        'id': 'INTEGER PRIMARY KEY AUTOINCREMENT',
        'post_id': 'INTEGER NOT NULL',
        'author_name': 'TEXT NOT NULL',
        'author_email': 'TEXT NOT NULL',
        'content': 'TEXT NOT NULL',
        'approved': 'BOOLEAN DEFAULT FALSE',
        'created_at': 'TIMESTAMP DEFAULT CURRENT_TIMESTAMP'
    }


# Create WolfPy application
app = WolfPy(
    debug=True,
    database_url='sqlite:///blog.db',
    template_folder=str(Path(__file__).parent / 'templates'),
    static_folder=str(Path(__file__).parent / 'static'),
    secret_key='your-secret-key-change-in-production'
)


# Helper functions
def create_slug(title: str) -> str:
    """Create URL-friendly slug from title."""
    import re
    slug = re.sub(r'[^\w\s-]', '', title.lower())
    slug = re.sub(r'[-\s]+', '-', slug)
    return slug.strip('-')


def get_post_with_author(post_id: int):
    """Get post with author information."""
    post = Post.find(post_id)
    if post:
        author = User.find(post.author_id)
        post.author = author
    return post


# Routes
@app.route('/')
def home(request):
    """Home page with recent blog posts."""
    posts = Post.where('published = ?', [True])
    
    # Add author information to posts
    for post in posts:
        author = User.find(post.author_id)
        post.author = author
    
    return app.template_engine.render('home.html', {
        'posts': posts,
        'title': 'WolfPy Blog'
    })


@app.route('/post/<slug>')
def view_post(request, slug):
    """View individual blog post."""
    post = Post.where('slug = ? AND published = ?', [slug, True])
    if not post:
        return Response('Post not found', status=404)
    
    post = post[0]
    author = User.find(post.author_id)
    post.author = author
    
    # Get approved comments
    comments = Comment.where('post_id = ? AND approved = ?', [post.id, True])
    
    return app.template_engine.render('post.html', {
        'post': post,
        'comments': comments,
        'title': post.title
    })


@app.route('/about')
def about(request):
    """About page."""
    return app.template_engine.render('about.html', {
        'title': 'About WolfPy Blog'
    })


@app.route('/contact', methods=['GET', 'POST'])
def contact(request):
    """Contact form."""
    if request.method == 'POST':
        # In a real app, you'd send an email here
        return app.template_engine.render('contact.html', {
            'title': 'Contact Us',
            'message': 'Thank you for your message! We\'ll get back to you soon.'
        })
    
    return app.template_engine.render('contact.html', {
        'title': 'Contact Us'
    })


# Authentication routes
@app.route('/login', methods=['GET', 'POST'])
def login(request):
    """User login."""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if app.auth.authenticate(username, password):
            return Response.redirect('/admin')
        else:
            return app.template_engine.render('login.html', {
                'title': 'Login',
                'error': 'Invalid username or password'
            })
    
    return app.template_engine.render('login.html', {
        'title': 'Login'
    })


@app.route('/register', methods=['GET', 'POST'])
def register(request):
    """User registration."""
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        
        if app.auth.register(username, email, password):
            return Response.redirect('/login')
        else:
            return app.template_engine.render('register.html', {
                'title': 'Register',
                'error': 'Username or email already exists'
            })
    
    return app.template_engine.render('register.html', {
        'title': 'Register'
    })


@app.route('/logout')
def logout(request):
    """User logout."""
    app.auth.logout(request)
    return Response.redirect('/')


# Admin routes
@app.route('/admin')
@login_required
def admin_dashboard(request):
    """Admin dashboard."""
    posts = Post.all()
    users = User.all()
    comments = Comment.where('approved = ?', [False])
    
    return app.template_engine.render('admin/dashboard.html', {
        'title': 'Admin Dashboard',
        'posts': posts,
        'users': users,
        'pending_comments': comments
    })


@app.route('/admin/posts')
@login_required
def admin_posts(request):
    """Manage posts."""
    posts = Post.all()
    for post in posts:
        author = User.find(post.author_id)
        post.author = author
    
    return app.template_engine.render('admin/posts.html', {
        'title': 'Manage Posts',
        'posts': posts
    })


@app.route('/admin/posts/new', methods=['GET', 'POST'])
@login_required
def admin_new_post(request):
    """Create new post."""
    if request.method == 'POST':
        title = request.form.get('title')
        content = request.form.get('content')
        published = bool(request.form.get('published'))
        
        slug = create_slug(title)
        
        Post.create(
            title=title,
            content=content,
            author_id=request.user.id,
            slug=slug,
            published=published
        )
        
        return Response.redirect('/admin/posts')
    
    return app.template_engine.render('admin/post_form.html', {
        'title': 'New Post',
        'post': None
    })


@app.route('/admin/posts/<int:post_id>/edit', methods=['GET', 'POST'])
@login_required
def admin_edit_post(request, post_id):
    """Edit existing post."""
    post = Post.find(post_id)
    if not post:
        return Response('Post not found', status=404)
    
    if request.method == 'POST':
        post.title = request.form.get('title')
        post.content = request.form.get('content')
        post.published = bool(request.form.get('published'))
        post.slug = create_slug(post.title)
        post.updated_at = datetime.now()
        
        post.save()
        return Response.redirect('/admin/posts')
    
    return app.template_engine.render('admin/post_form.html', {
        'title': 'Edit Post',
        'post': post
    })


@app.route('/admin/posts/<int:post_id>/delete', methods=['POST'])
@login_required
def admin_delete_post(request, post_id):
    """Delete post."""
    post = Post.find(post_id)
    if post:
        post.delete()
    return Response.redirect('/admin/posts')


# Initialize database and create admin user
def init_database():
    """Initialize database with tables and sample data."""
    app.database.create_tables([User, Post, Comment])
    
    # Create admin user if it doesn't exist
    admin = User.where('username = ?', ['admin'])
    if not admin:
        app.auth.register('admin', 'admin@example.com', 'admin123', is_admin=True)
        print("Created admin user: admin/admin123")
    
    # Create sample post if no posts exist
    if not Post.all():
        admin_user = User.where('username = ?', ['admin'])[0]
        Post.create(
            title='Welcome to WolfPy Blog!',
            content='''
# Welcome to WolfPy Blog!

This is a sample blog post created with the WolfPy web framework.

## Features

- User authentication
- CRUD operations
- Template rendering
- Admin interface
- Static file serving

Enjoy exploring the WolfPy framework!
            '''.strip(),
            author_id=admin_user.id,
            slug='welcome-to-wolfpy-blog',
            published=True
        )
        print("Created sample blog post")


if __name__ == '__main__':
    init_database()
    print("🐺 WolfPy Blog starting...")
    print("📝 Admin login: admin/admin123")
    print("🌐 Visit: http://localhost:8000")
    app.run(host='0.0.0.0', port=8000)
