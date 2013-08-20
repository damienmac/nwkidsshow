from django.contrib import admin
from nwkidsshow.models import Exhibitor, Retailer, Show, Registration, RetailerRegistration

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
                    'venue',
                    'late_date',
                    'closed_date',
                    'start_date',
                    'end_date',
                    'registration_fee',
                    'assistant_fee',
                    'late_fee',
                    'rack_fee',
                    )
    search_fields = ['name']
    # date_hierarchy = 'start_date' CRASHES ADMIN for some reason now...
    ordering = ('start_date',)
    # list_filter = ('start_date', 'venue')
    list_filter = ('venue',)
    filter_horizontal = ('exhibitors','retailers',)


class RegistrationAdmin(admin.ModelAdmin):
    list_display = (
        'exhibitor',
        'show',
        'date_registered',
        'is_late',
        'has_paid',
        'total',
        'num_racks',
        'num_tables',
        'booked_room',
        'room',
    )
    list_display_links = (
        'exhibitor',
        'show',
    )
    search_fields = ['show', 'exhibitor', 'is_late', 'has_paid']
    list_filter = ('show', 'is_late', 'has_paid', 'booked_room',)


class RetailerRegistrationAdmin(admin.ModelAdmin):
    list_display = (
        'retailer',
        'show',
    )
    list_display_links = (
        'retailer',
        'show',
    )
    search_fields = ['show', 'retailer',]
    list_filter = ('show',)

admin.site.register(Exhibitor, ExhibitorAndRetailerAdmin)
admin.site.register(Retailer,  ExhibitorAndRetailerAdmin)
admin.site.register(Show, ShowAdmin)
admin.site.register(Registration, RegistrationAdmin)
admin.site.register(RetailerRegistration, RetailerRegistrationAdmin)
