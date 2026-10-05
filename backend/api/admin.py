from django.contrib import admin

from .models import Category, UserWord, Word, WordCategory


@admin.register(Word)
class WordAdmin(admin.ModelAdmin):
    list_display = ("chinese", "pinyin", "english_basic")
    search_fields = ("chinese", "pinyin", "english_basic")


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name",)
    search_fields = ("name",)
    filter_horizontal = ("words",)


@admin.register(WordCategory)
class WordCategoryAdmin(admin.ModelAdmin):
    list_display = ("category", "word")
    list_select_related = ("category", "word")
    autocomplete_fields = ("category", "word")


@admin.register(UserWord)
class UserWordAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "word",
        "mode",
        "easy_streak",
        "easy_count",
        "due_on",
        "last_practiced_at",
    )
    list_filter = ("mode",)
    list_select_related = ("user", "word")
    autocomplete_fields = ("user", "word")
    search_fields = ("word__chinese", "word__pinyin", "word__english_basic", "user__username")
