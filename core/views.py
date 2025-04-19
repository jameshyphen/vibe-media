from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import get_user_model, login, authenticate
from django.contrib.auth.views import LoginView, LogoutView
from django.views.generic.edit import CreateView
from django.urls import reverse_lazy
from django.db.models import Q, Count, F
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponseForbidden
from django.utils import timezone
from datetime import timedelta
from .forms import CustomUserCreationForm, CustomAuthenticationForm, PostForm, ProfileEditForm, CommentForm
from .models import Post, Like, Comment
import random

User = get_user_model()


@login_required
def index(request):
    form = PostForm()
    comment_form = CommentForm()

    # Get posts with engagement metrics
    posts = Post.objects.annotate(
        like_count=Count('like'),
        comment_count=Count('comments'),
        engagement_score=Count('like') + Count('comments') * 2  # Comments weighted more than likes
    ).select_related('user')

    # Get recent posts (last 24 hours)
    recent_posts = posts.filter(
        created_at__gte=timezone.now() - timedelta(days=1)
    ).order_by('-created_at')[:10]

    # Get trending posts (high engagement in last 7 days)
    trending_posts = posts.filter(
        created_at__gte=timezone.now() - timedelta(days=7)
    ).order_by('-engagement_score')[:10]

    # Get some random posts for discovery
    random_posts = list(posts.filter(
        created_at__gte=timezone.now() - timedelta(days=30)
    )[:20])
    random.shuffle(random_posts)
    random_posts = random_posts[:5]

    # Combine and deduplicate posts
    combined_posts = list(recent_posts) + list(trending_posts) + random_posts
    seen_ids = set()
    unique_posts = []
    for post in combined_posts:
        if post.id not in seen_ids:
            seen_ids.add(post.id)
            unique_posts.append(post)

    # Get likes for all posts
    user_likes = set()
    if request.user.is_authenticated:
        user_likes = set(Like.objects.filter(
            user=request.user,
            post_id__in=[post.id for post in unique_posts]
        ).values_list('post_id', flat=True))

    return render(request, 'core/index.html', {
        'form': form,
        'comment_form': comment_form,
        'posts': unique_posts,
        'user_likes': user_likes
    })


def search_users(request):
    query = request.GET.get('q', '')
    users = []

    if query:
        users = User.objects.filter(
            Q(username__icontains=query) |
            Q(first_name__icontains=query) |
            Q(last_name__icontains=query)
        ).exclude(id=request.user.id)[:10]

    return render(request, 'core/search_results.html', {
        'users': users,
        'query': query
    })


class CustomLoginView(LoginView):
    form_class = CustomAuthenticationForm
    template_name = 'core/login.html'
    redirect_authenticated_user = True

    def get_success_url(self):
        return reverse_lazy('core:index')

    def form_invalid(self, form):
        messages.error(self.request, 'Invalid username or password')
        return super().form_invalid(form)


from django.contrib.auth import logout
from django.shortcuts import redirect

def custom_logout(request):
    logout(request)
    return redirect('core:index')

@login_required
def profile(request, username):
    user = get_object_or_404(User, username=username)
    form = PostForm() if request.user == user else None
    edit_form = ProfileEditForm(instance=user) if request.user == user else None
    comment_form = CommentForm()
    
    posts = Post.objects.filter(user=user).select_related('user')
    
    # Get likes for all posts
    user_likes = set()
    if request.user.is_authenticated:
        user_likes = set(Like.objects.filter(
            user=request.user,
            post_id__in=posts.values_list('id', flat=True)
        ).values_list('post_id', flat=True))
    
    return render(request, 'core/profile.html', {
        'profile_user': user,
        'form': form,
        'edit_form': edit_form,
        'comment_form': comment_form,
        'posts': posts,
        'user_likes': user_likes
    })

@login_required
def edit_profile(request):
    if request.method == 'POST':
        try:
            form = ProfileEditForm(request.POST, request.FILES, instance=request.user)
            if form.is_valid():
                form.save()
                messages.success(request, 'Profile updated successfully!')
                return redirect('core:profile', username=request.user.username)
            else:
                return JsonResponse({'errors': form.errors}, status=400)
        except Exception as e:
            return JsonResponse({'errors': {'server': str(e)}}, status=500)
    return HttpResponseForbidden()

@login_required
def create_post(request):
    if request.method == 'POST':
        form = PostForm(request.POST)
        if form.is_valid():
            post = form.save(commit=False)
            post.user = request.user
            post.save()
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'status': 'success',
                    'id': post.id,
                    'content': post.content,
                    'created_at': post.created_at.strftime('%b %d, %Y, %I:%M %p'),
                    'user': {
                        'username': post.user.username,
                        'full_name': post.user.get_full_name(),
                        'avatar_url': post.user.get_avatar_url()
                    },
                    'likes_count': 0,
                    'comments_count': 0
                })
            return redirect(request.META.get('HTTP_REFERER', 'core:index'))
    return redirect('core:index')

@login_required
def toggle_like(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    like, created = Like.objects.get_or_create(user=request.user, post=post)
    
    if not created:
        like.delete()
        is_liked = False
    else:
        is_liked = True
    
    return JsonResponse({
        'status': 'success',
        'is_liked': is_liked,
        'likes_count': post.get_likes_count()
    })

@login_required
def create_comment(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    if request.method == 'POST':
        form = CommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.user = request.user
            comment.post = post
            
            parent_id = form.cleaned_data.get('parent')
            if parent_id:
                parent_comment = get_object_or_404(Comment, id=parent_id)
                if parent_comment.post != post:
                    return JsonResponse({'status': 'error', 'message': 'Invalid parent comment'}, status=400)
                comment.parent = parent_comment
            
            comment.save()
            
            return JsonResponse({
                'status': 'success',
                'id': comment.id,
                'content': comment.content,
                'created_at': comment.created_at.strftime('%b %d, %Y, %I:%M %p'),
                'user': {
                    'username': comment.user.username,
                    'full_name': comment.user.get_full_name(),
                    'avatar_url': comment.user.get_avatar_url()
                },
                'parent_id': comment.parent_id
            })
        return JsonResponse({'status': 'error', 'errors': form.errors}, status=400)
    return JsonResponse({'status': 'error', 'message': 'Invalid request'}, status=400)

@login_required
def load_comments(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    comments = Comment.objects.filter(post=post, parent=None).select_related('user').prefetch_related(
        'replies__user'
    )
    
    comments_data = []
    for comment in comments:
        comment_data = {
            'id': comment.id,
            'content': comment.content,
            'created_at': comment.created_at.strftime('%b %d, %Y, %I:%M %p'),
            'user': {
                'username': comment.user.username,
                'full_name': comment.user.get_full_name(),
                'avatar_url': comment.user.get_avatar_url()
            },
            'replies': [{
                'id': reply.id,
                'content': reply.content,
                'created_at': reply.created_at.strftime('%b %d, %Y, %I:%M %p'),
                'user': {
                    'username': reply.user.username,
                    'full_name': reply.user.get_full_name(),
                    'avatar_url': reply.user.get_avatar_url()
                }
            } for reply in comment.replies.all()]
        }
        comments_data.append(comment_data)
    
    return JsonResponse({
        'status': 'success',
        'comments': comments_data
    })


class RegisterView(CreateView):
    form_class = CustomUserCreationForm
    template_name = 'core/register.html'
    success_url = reverse_lazy('core:index')

    def form_valid(self, form):
        response = super().form_valid(form)
        username = form.cleaned_data['username']
        password = form.cleaned_data['password1']
        user = authenticate(username=username, password=password)
        login(self.request, user)
        messages.success(self.request, f'Welcome to VIBE, {user.first_name}!')
        return response

    def form_invalid(self, form):
        messages.error(self.request, 'Please correct the errors below')
        return super().form_invalid(form)
