from django.contrib import admin
from nwkidsshow.models import Exhibitor, Retailer, Show

class ExhibitorAndRetailerAdmin(admin.ModelAdmin):
    list_display = ('username_display',
                    'first_name_display',
                    'last_name_display',
                    'email_display',
                    'company',
                    'website',
                    'address',
                    'address2',
                    'city',
                    'state',
                    'zip',
                    'phone',
                    'fax',
                    )
    
    list_display_links = ('username_display',
                          'first_name_display',
                          'last_name_display',
                          )
    
    search_fields = ['user__username',
                     'user__first_name',
                     'user__last_name',
                     'user__email',
                     'company',
                     'state',
                     ]

    # I don't want us to unlink the user info by accident.
    readonly_fields = ('user',)

class ShowAdmin(admin.ModelAdmin):
    list_display = ('name',
                    'late_date',
                    'closed_date',
                    'start_date',
                    'end_date',
                    )
    search_fields = ['name']
    date_hierarchy = 'start_date'
    ordering = ('start_date',)
    list_filter = ('start_date',)
    filter_horizontal = ('exhibitors','retailers',)

admin.site.register(Exhibitor, ExhibitorAndRetailerAdmin)
admin.site.register(Retailer,  ExhibitorAndRetailerAdmin)
admin.site.register(Show, ShowAdmin)