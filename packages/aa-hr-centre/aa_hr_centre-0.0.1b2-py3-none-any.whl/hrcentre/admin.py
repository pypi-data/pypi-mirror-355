from django.contrib import admin

from .models import CorporationSetup, AllianceSetup, Label, UsersCheck


@admin.register(CorporationSetup)
class CorporationSetupAdmin(admin.ModelAdmin):
    pass


@admin.register(AllianceSetup)
class AllianceSetupAdmin(admin.ModelAdmin):
    pass


@admin.register(Label)
class LabelAdmin(admin.ModelAdmin):
    list_display = ('name', 'color',)
    search_fields = ('name',)
    ordering = ('name',)


@admin.register(UsersCheck)
class UsersCheckAdmin(admin.ModelAdmin):
    list_display = ('name', 'description', )
    search_fields = ('name', 'description', )
