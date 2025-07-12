from django.contrib import admin
from .models import Comment

@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
	list_display = ('video', 'user', 'text', 'created_at', 'status')
	list_filter = ('status', 'created_at')
	search_fields = ('name', 'email', 'body')
	actions = ['approve_comments']

	def approve_comments(self, request, queryset):
		queryset.update(status=True)

