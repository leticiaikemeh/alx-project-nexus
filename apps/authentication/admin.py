from django.contrib import admin
from .models import User, Role, UserRole
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin


class UserRoleInline(admin.TabularInline):
    model = UserRole
    extra = 1  # show 1 empty form by default
    autocomplete_fields = ['role']  # helpful if you have many roles
    verbose_name = "User Role"
    verbose_name_plural = "User Roles"


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    inlines = [UserRoleInline]

    # remove 'roles' from fieldsets, filter_horizontal, etc.
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal info', {'fields': ('username', 'first_name', 'last_name')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser')}),
        ('Important dates', {'fields': ('last_login',)}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'username', 'password1', 'password2'),
        }),
    )
    list_display = ('email', 'username', 'is_staff', 'is_superuser')
    search_fields = ('email', 'username')
    ordering = ('email',)


@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ('id', 'name')
    search_fields = ('name',)


@admin.register(UserRole)
class UserRoleAdmin(admin.ModelAdmin):
    list_display = ('user', 'role')
    autocomplete_fields = ['user', 'role']
