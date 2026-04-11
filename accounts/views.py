from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from .models import UserProfile
from django.conf import settings

# Owner registration code — set this in .env
OWNER_REGISTER_CODE = getattr(settings, 'OWNER_REGISTER_CODE', 'LOCO2026')


def _redirect_by_role(user):
    if user.is_superuser:
        return redirect('dashboard:overview')
    role = getattr(getattr(user, 'profile', None), 'role', 'kitchen')
    if role == 'owner':
        return redirect('dashboard:overview')
    else:
        return redirect('kitchen')


def login_view(request):
    if request.user.is_authenticated:
        return _redirect_by_role(request.user)

    error = None
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')
        user     = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            return _redirect_by_role(user)
        else:
            error = '❌ اسم المستخدم أو كلمة المرور غير صحيحة'

    return render(request, 'accounts/login.html', {'error': error})


def register_view(request):
    if request.method != 'POST':
        return redirect('accounts:login')

    username   = request.POST.get('username', '').strip()
    full_name  = request.POST.get('full_name', '').strip()
    password1  = request.POST.get('password1', '')
    password2  = request.POST.get('password2', '')
    role       = request.POST.get('role', 'kitchen')
    reg_code   = request.POST.get('register_code', '').strip()

    # Validations
    if not username or not password1:
        return render(request, 'accounts/login.html', {
            'error': '❌ يرجى تعبئة جميع الحقول المطلوبة',
            'show_register': True
        })

    if password1 != password2:
        return render(request, 'accounts/login.html', {
            'error': '❌ كلمتا المرور غير متطابقتين',
            'show_register': True
        })

    if len(password1) < 8:
        return render(request, 'accounts/login.html', {
            'error': '❌ كلمة المرور يجب أن تكون 8 أحرف على الأقل',
            'show_register': True
        })

    if User.objects.filter(username=username).exists():
        return render(request, 'accounts/login.html', {
            'error': '❌ اسم المستخدم مستخدم بالفعل',
            'show_register': True
        })

    # Owner requires special code
    if role == 'owner' and reg_code != OWNER_REGISTER_CODE:
        return render(request, 'accounts/login.html', {
            'error': '❌ كود التسجيل غير صحيح للمدير',
            'show_register': True
        })

    # Create user
    name_parts = full_name.split(' ', 1) if full_name else ['', '']
    user = User.objects.create_user(
        username   = username,
        password   = password1,
        first_name = name_parts[0],
        last_name  = name_parts[1] if len(name_parts) > 1 else '',
    )

    # Create profile
    UserProfile.objects.create(user=user, role=role)

    # Auto login
    login(request, user)
    return _redirect_by_role(user)


@login_required
def logout_view(request):
    logout(request)
    return redirect('accounts:login')