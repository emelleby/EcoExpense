from functools import wraps
from flask import flash, redirect, url_for
from flask_login import current_user

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            flash('You need administrator privileges to access this page.', 'danger')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function

def same_organization_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('login'))
        
        if 'user_id' in kwargs:
            from models import User
            target_user = User.query.get_or_404(kwargs['user_id'])
            if target_user.organization_id != current_user.organization_id and not current_user.is_admin:
                flash('You can only access resources within your organization.', 'danger')
                return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function
