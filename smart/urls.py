from django.urls import path
from .import views


urlpatterns = [
    
    #-------------------------General(Dashboards,Widgets & Layout)---------------------------------------
    
    
    # #-----------------------Dashboards
    path('', views.dashboard, name='dashboard'),
    path('index/', views.index, name='index'),
    path('regions/', views.regions, name='regions'),
    
    #autentication
    path('signup_home', views.signup_home, name="signup_home"),
    path('login_home', views.login_home, name="login_home"),
    path('logout_view', views.logout_view, name="logout_view"),
    
    # Home Content
    path('sliders/', views.sliders, name='sliders'),
    # Home Content
    
    # User accounts
    path('user-accounts/', views.user_accounts, name='user_accounts'),
    path('add-user-account/', views.add_user_account, name='add_user_account'),
    path('edit-user-account/', views.edit_user_account, name='edit_user_account'), 
    path('delete-user-account/', views.delete_user_account, name='delete_user_account'),
    # User accounts
    
    # Users 
    path('user-list/', views.user_list, name='user_list'),
    path('add-user/', views.add_user, name='add_user'),
    # Users
    
    # products
    # path('products/', views.product_list, name='product_list'),
    # path('add-product/', views.add_product, name='add_product'),
    # path('edit-product/<int:id>/', views.edit_product, name='edit_product'),
    # path('delete-product/', views.delete_product, name='delete_product'),
    
    # Category
    path('category/', views.category, name="category"),
    
    # products
    path('add_products',views.add_products, name="add_products"),    
    path('product_grid',views.product_grid, name="product_grid"),   
    path('list_products', views.list_products, name="list_products"),
    path('product_details',views.product_details, name="product_details"),
    path('edit-product/<int:id>/', views.edit_product, name='edit_product'),
    path('product-review',views.product_review,name='product_review'),
    
    path('pending-products',views.pending_products,name='pending_products'),
    path('single-product-request/<int:id>/', views.single_product_request, name='single_product_request'),
    path('reject-product/', views.reject_product, name='reject_product'),
    path('update-approval-status/', views.update_approval_status, name='update_approval_status'),
    # products
    
    #About Us
    path('aboutUs_header/', views.aboutUs_header, name='aboutUs_header'),
    path('aboutus_content',views.aboutus_content,name='aboutus_content'),
    path('delete/<int:pk>/', views.delete_about_page_content, name='delete_about_page_content'),
    #About Us
    
    
    #delivery charge
    path('deliveryCharge',views.deliveryCharge,name='deliveryCharge'),
    path('get_delivery_types',views.get_delivery_types,name='get_delivery_types'),
    path('deliverytype',views.deliverytype,name='deliverytype'),
    #delivery charge
    
    
    #Faqs
    path('faqs_header/', views.faqs_header, name='faqs_header'),
    #Faqs
    
    #wishlist
    path('wishlist_header/', views.wishlist_header, name='wishlist_header'),
    #wishlist
    
    # vendors
    path('update_vendor_header',views.update_vendor_header,name="update_vendor_header"),
    path('vendors', views.vendors, name="vendors"),
    path('vendor/<int:id>/', views.vendor, name="vendor"),
    path('vendor-list',views.vendor_list,name="vendor_list"),
    path('add-vendor',views.add_vendor,name="add_vendor"),
    path('save-vendor',views.save_vendor,name="save_vendor"),
    path('get-user-data/<int:user_id>/',views.get_user_data,name="get_user_data"),
    path('update-vendor/<int:id>/',views.update_vendor,name="update_vendor"),
    
    # contact
    path('update_contact_header',views.update_contact_header,name='update_contact_header'),
    path('contact_messages/', views.contact_messages, name='contact_messages'),
    path('contactUs_location',views.contactUs_location,name='contactUs_location'),
    
    # blogs
    path('blogList_header',views.blogList_header,name="blogList_header"),
    path('blog_header',views.blog_header,name="blog_header"),
     
    # packages
    path('packages/', views.packages, name='packages'),
    
    # Category
    # Category
    path('category/', views.category, name="category"),
    path('category-types/', views.category_type, name='category_type'),
    path('get-subcategories/<int:parent_id>/', views.get_subcategories, name='get_subcategories'),



    #clients home page 
    path('clientBrands',views.clientBrands,name='clientBrands'),
    path('brands/add/', views.add_client_brand, name='add_client_brand'),
    path('brands/edit/', views.edit_client_brand, name='edit_client_brand'),
    path('brands/delete/', views.delete_client_brand, name='delete_client_brand'),
    #clients Home page
    
    #category Banner
    path('categorybanner',views.categorybanner,name='categorybanner'),
    path('category-banners/add/', views.add_category_banner, name='add_category_banner'),
    path('category-banners/edit/<int:banner_id>/', views.edit_category_banner, name='edit_category_banner'),
    path('category-banners/delete/<int:banner_id>/', views.delete_category_banner, name='delete_category_banner'),
    #category Banner
    
    
    
    #ad banner
    path('adBanner',views.adBanner,name='adBanner'),
    path('ad-banners/add/', views.add_ad_banner, name='add_ad_banner'),
    path('ad-banners/edit/<int:banner_id>/', views.edit_ad_banner, name='edit_ad_banner'),
    path('ad-banners/delete/<int:banner_id>/', views.delete_ad_banner, name='delete_ad_banner'),
    #ad banner
    
    
    #offer banner
    path('offerbanner',views.offerbanner,name='offerbanner'),
    path('add-offer-banner', views.add_offer_banner, name='add_offer_banner'),
    path('edit-offer-banner/<int:banner_id>/', views.edit_offer_banner, name='edit_offer_banner'),
    path('delete-offer-banner/<int:banner_id>/', views.delete_offer_banner, name='delete_offer_banner'),
    #ofer banner
    
    #vendors order
    path('vendorOrder',views.vendorOrder,name='vendorOrder'),
    path("orders/notify-item/", views.notify_vendor_item, name="notify_vendor_item"),
    path("api/vendor/orders/", views.vendor_orders_api, name="vendor_orders_api"),
    
    
    
     # 🔔 Order notifications (admin side)
    path("orders/get-order-count/", views.get_order_count, name="get_order_count"),
    path("orders/mark-viewed/", views.mark_order_viewed, name="mark_order_viewed"),

    # 🔔 Vendor order notifications
    path("vendor-orders/get-order-count/", views.get_vendor_order_count, name="get_vendor_order_count"),
    path("vendor-orders/mark-viewed/", views.mark_vendor_order_viewed, name="mark_vendor_order_viewed"),
    
    
    #vendors order
        #invoice
    path('invoice/<int:order_id>/', views.invoice, name='invoice'),

    #invoice
    
    
    path('products/create/', views.create_product, name='create_product'),
    
    path('order_history', views.order_history, name="order_history"),
    path('orders/<int:order_id>/details/', views.order_details, name='order_details'),
    # path('api/order-count/', views.get_order_count, name='get_order_count'),
    path("orders/mark-viewed/", views.mark_order_viewed, name="mark_order_viewed"),
    
    
    # ðŸ”¥ NEW URLs for order editing
    path('orders/<int:order_id>/edit/', views.edit_order, name='edit_order'),
    path('orders/<int:order_id>/update/', views.update_order, name='update_order'),
    path('orders/<int:order_id>/remove-item/<int:item_id>/', views.remove_order_item, name='remove_order_item'),
    
    
    # built-in views
    path('dashboard_02', views.dashboard_02, name="dashboard_02"),
    path('dashboard_03', views.dashboard_03, name="dashboard_03"),
    path('dashboard_04', views.dashboard_04, name="dashboard_04"),
    path('dashboard_05', views.dashboard_05, name="dashboard_05"),
    path('dashboard_06', views.dashboard_06, name="dashboard_06"),
    path('dashboard_07', views.dashboard_07, name="dashboard_07"),
    path('dashboard_08', views.dashboard_08, name="dashboard_08"),
    path('dashboard_09', views.dashboard_09, name="dashboard_09"),
    path('dashboard_10', views.dashboard_10, name="dashboard_10"),
    path('dashboard_11', views.dashboard_11, name="dashboard_11"),
    
    
    # #-----------------------Widgets
    path('general_widget', views.general_widget, name="general_widget"),
    path('chart_widget', views.chart_widget, name="chart_widget"),
    
    
    # #------------------------Layout
    path('box_layout', views.box_layout, name="box_layout"),
    path('layout_rtl', views.layout_rtl, name="layout_rtl"),
    path('layout_dark', views.layout_dark, name="layout_dark"),
    path('hide_on_scroll', views.hide_on_scroll, name="hide_on_scroll"),
    path('footer_light', views.footer_light, name="footer_light"),
    path('footer_dark', views.footer_dark, name="footer_dark"),
    path('footer_fixed', views.footer_fixed, name="footer_fixed"),
    
    
    # #--------------------------------Applications---------------------------------

    # #---------------------Project 

    path('project_details', views.project_details, name="project_details"),
    path('projects', views.projects, name="projects"),
    path('projectcreate', views.projectcreate, name="projectcreate"), 

    # #-------------------File Manager
    path('file_manager', views.file_manager, name="file_manager"),

    # #------------------Kanban Board
    path('kanban', views.kanban, name="kanban"),
    
    
    
    
    path('seller_list', views.seller_list, name="seller_list"),
    path('seller_details', views.seller_details, name="seller_details"),
    


    
    path('invoice_1', views.invoice_1, name="invoice_1"),
    path('invoice_2', views.invoice_2, name="invoice_2"),
    path('invoice_3', views.invoice_3, name="invoice_3"),
    path('invoice_4', views.invoice_4, name="invoice_4"),
    path('invoice_5', views.invoice_5, name="invoice_5"),
    path('invoice_6', views.invoice_6, name="invoice_6"),
    
    path('cart', views.cart, name="cart"),
    path('list_wish', views.list_wish, name="list_wish"),
    path('checkout', views.checkout, name="checkout"),
    
    path('mail_box', views.mail_box, name="mail_box"),
    
    
    # #----------------------Chat
    path('private_chat', views.private_chat, name="private_chat"),
    path('group_chat', views.group_chat, name="group_chat"),
    
    
    # #---------------------------------user
    path('user_profile', views.user_profile, name="user_profile"),
    path('edit_profile', views.edit_profile, name="edit_profile"),
    path('user_cards', views.user_cards, name="user_cards"),
    
    
    # #------------------------bookmark
    path('bookmark', views.bookmark, name="bookmark"),
    
    
    # #------------------------contacts
    path('contacts', views.contacts, name="contacts"),

    # #------------------------task
    path('task', views.task, name="task"),

    # #------------------------calendar
    path('calendar_basic', views.calendar_basic, name="calendar_basic"),

    # #------------------------social-app
    path('social_app', views.social_app, name="social_app"),
    
    # #------------------------to-do
    path('to_do', views.to_do, name="to_do"),
    
    
    # #------------------------search
    path('search', views.search, name="search"),
    
    
#--------------------------------Forms & Table-----------------------------------------------

    #--------------------------------Forms------------------------------------

    #------------------------form-controls
    path('form_validation', views.form_validation, name="form_validation"),
    path('base_input', views.base_input, name="base_input"),
    path('radio_checkbox_control', views.radio_checkbox_control, name="radio_checkbox_control"),
    path('input_group', views.input_group, name="input_group"),
    path('input_mask', views.input_mask, name="input_mask"),
    path('megaoptions', views.megaoptions, name="megaoptions"),
    
    
    #---------------------------form widgets
    path('datepicker', views.datepicker, name="datepicker"),
    path('touchspin', views.touchspin, name="touchspin"),
    path('select2', views.select2, name="select2"),
    path('switch', views.switch, name="switch"),
    path('typeahead', views.typeahead, name="typeahead"),
    path('clipboard', views.clipboard, name="clipboard"),
    
    
   #--------------------------------form layout
    path('form_wizard_one', views.form_wizard_one, name="form_wizard_one"),
    path('form_wizard_two', views.form_wizard_two, name="form_wizard_two"),
    path('two_factor', views.two_factor, name="two_factor"),
    
    
    #--------------------------------------Table--------------------------------------------------

    #------------------------bootstrap table
    path('basic_table', views.basic_table, name="basic_table"),
    path('table_components', views.table_components, name="table_components"),
    
    
    #-------------------------data table
    path('datatable_basic_init', views.datatable_basic_init, name="datatable_basic_init"),
    path('datatable_advance', views.datatable_advance, name="datatable_advance"),
    path('datatable_API', views.datatable_API, name="datatable_API"),
    path('datatable_data_source', views.datatable_data_source, name="datatable_data_source"),
    
    
    #---------------------------Exdata table
    path('ext_autofill', views.ext_autofill, name="ext_autofill"),  
    
    #-----------------------------jsgrid_table
    path('jsgrid_table', views.jsgrid_table, name="jsgrid_table"),      
    
    
    #------------------Components------UI Components-----Elements ----------->

    #-----------------------------Ui kits
    path('typography', views.typography, name="typography"),
    path('avatars', views.avatars, name="avatars"),
    path('divider', views.divider, name="divider"),
    path('helper_classes', views.helper_classes, name="helper_classes"),
    path('grid', views.grid, name="grid"),
    path('tag-pills', views.tagpills, name="tag-pills"),
    path('progressbar', views.progressbar, name="progressbar"),
    path('modal', views.modal, name="modal"),
    path('alert', views.alert, name="alert"),
    path('popover', views.popover, name="popover"),
    path('placeholder', views.placeholder, name="placeholder"),
    path('tooltip', views.tooltip, name="tooltip"),
    path('dropdown', views.dropdown, name="dropdown"),
    path('accordion', views.accordion, name="accordion"),
    path('bootstraptab', views.bootstraptab, name="bootstraptab"),
    path('offcanvas', views.offcanvas, name="offcanvas"),
    path('navigate_links', views.navigate_links, name="navigate_links"),
    path('lists', views.lists, name="lists"),
    
    
    #-------------------------------Bonus Ui    
    path('scrollable/', views.scrollable, name="scrollable"),
    path('tree/', views.tree, name="tree"),
    path('toasts/', views.toasts, name="toasts"),
    path('blockUi/', views.blockUi, name="blockUi"),
    path('rating/', views.rating, name="rating"),
    path('dropzone/', views.dropzone, name="dropzone"),
    path('tour/', views.tour, name="tour"),
    path('sweetalert2/', views.sweetalert2, name="sweetalert2"),
    path('animatedmodal/', views.animatedmodal, name="animatedmodal"),
    path('owlcarousel/', views.owlcarousel, name="owlcarousel"),
    path('ribbons/', views.ribbons, name="ribbons"),
    path('breadcrumb/', views.breadcrumb, name="breadcrumb"),
    path('pagination/', views.pagination, name="pagination"),
    path('scrollspy/', views.scrollspy, name="scrollspy"),
    path('rangeslider/', views.rangeslider, name="rangeslider"),
    path('ratios/', views.ratios, name="ratios"),
    path('imagecropper/', views.imagecropper, name="imagecropper"),
    path('basiccard/', views.basiccard, name="basiccard"),
    path('creativecard/', views.creativecard, name="creativecard"),
    path('draggablecard/', views.draggablecard, name="draggablecard"),
    path('timeline/', views.timeline, name="timeline"),  
    
    
    #---------------------------------Animation    
    path('animate/', views.animate, name="animate"),
    path('scrollreval/', views.scrollreval, name="scrollreval"),
    path('AOS/', views.AOS, name="AOS"),
    path('tilt/', views.tilt, name="tilt"),
    path('wow/', views.wow, name="wow"),
    path('flashicon/', views.flashicon, name="flashicon"),
    
    
    #--------------------------Icons
    path('flagicon/', views.flagicon, name="flagicon"),
    path('fontawesome/', views.fontawesome, name="fontawesome"),
    path('feather/', views.feather, name="feather"),
    path('icoicon/', views.icoicon, name="icoicon"),
    path('themify/', views.themify, name="themify"),
    path('whether/', views.whether, name="whether"),
    
    
    #--------------------------------Buttons
    path('buttons/', views.buttons, name="buttons"),

    #--------------------------------Charts 
    path('apex', views.apex, name="apex"),
    path('chartjs', views.chartjs, name="chartjs"),
    path('chartist', views.chartist, name="chartist"),
    path('flot', views.flot, name="flot"),
    path('google', views.google, name="google"),
    path('knob', views.knob, name="knob"),
    path('morris', views.morris, name="morris"),
    path('peity', views.peity, name="peity"),
    path('sparkline', views.sparkline, name="sparkline"), 
    
    
    #-----------------------------------Pages-----------------------------------

    #-----------------sample-page
    path('sample_page', views.sample_page , name="sample_page"),

    #-----------------internationalization
    path('internationalization', views.internationalization, name="internationalization"),

    
    #--------------------Errror pae
    path('error_400', views.error_400, name="error_400"),
    path('error_401', views.error_401, name="error_401"),
    path('error_403', views.error_403, name="error_403"),
    path('error_404', views.error_404, name="error_404"),
    path('error_500', views.error_500, name="error_500"),
    path('error_503', views.error_503, name="error_503"),

    #---------------------Authentication
    path('login_simple', views.login_simple, name="login_simple"),
    path('login_one', views.login_one, name="login_one"),
    path('login_two', views.login_two, name="login_two"),
    path('login_bs_validation', views.login_bs_validation, name="login_bs_validation"),
    path('login_tt_validation', views.login_tt_validation, name="login_tt_validation"),
    path('login_validation', views.login_validation, name="login_validation"),
    path('sign_up/', views.sign_up, name="sign_up" ),
    path('sign_one', views.sign_one, name="sign_one" ),
    path('sign_two', views.sign_two, name="sign_two" ),
    path('sign_wizard', views.sign_wizard, name="sign_wizard"),
    path('unlock', views.unlock , name="unlock"),
    path('forget_password', views.forget_password, name="forget_password"),
    path('reset_password', views.reset_password, name="reset_password"),
    path('maintenance', views.maintenance, name="maintenance"),
    
    
    #---------------------------------------comingsoon

    path('comingsoon', views.comingsoon, name="comingsoon"),
    path('comingsoon_video', views.comingsoon_video, name="comingsoon_video"),
    path('comingsoon_img', views.comingsoon_img, name="comingsoon_img"),

    #------------------------------------email template

    path('basic_temp', views.basic_temp, name="basic_temp"),
    path('email_header', views.email_header, name="email_header"),
    path('template_email', views.template_email, name="template_email"),
    path('template_email_2', views.template_email_2, name="template_email_2"),
    path('ecommerce_temp', views.ecommerce_temp, name="ecommerce_temp"),
    path('email_order', views.email_order, name="email_order"),      
    
    
    path('pricing', views.pricing, name="pricing"),
    path('FAQ', views.FAQ, name="FAQ"),
    
    
    
    #------------------------------------------Miscellaneous----------------- -------------------------

    #------------------------gallery

    path('gallery_grid', views.gallery_grid, name="gallery_grid"),
    path('gallery_description', views.gallery_description, name="gallery_description"),
    path('masonry_gallery', views.masonry_gallery, name="masonry_gallery"),
    path('masonry_disc', views.masonry_disc, name="masonry_disc"),
    path('hover', views.hover, name="hover"),

    #-------------------------Blog
    path('blog_details', views.blog_details, name="blog_details"),
    path('blog_single', views.blog_single, name="blog_single"),
    path('add_post', views.add_post, name="add_post"),

    #-------------------------job serch

    path('job_cards', views.job_cards, name="job_cards"),
    path('job_list', views.job_list, name="job_list"),
    path('job_details', views.job_details, name="job_details"),
    path('apply', views.apply, name="apply"),
    
    #-------------------------Learning
    path('course_list', views.course_list, name="course_list"),
    path('course_detailed', views.course_detailed, name="course_detailed"),

    #-------------------------maps
    path('data_map', views.data_map, name="data_map"),
    path('vector_maps', views.vector_maps, name="vector_maps"),


    #------------------------------------Editors
    path('quilleditor', views.quilleditor, name="quilleditor"),
    path('ckeditor', views.ckeditor, name="ckeditor"),
    path('ace_code', views.ace_code, name="ace_code"),


    #-----------------------------knowledgebase
    path('knowledgebase', views.knowledgebase, name="knowledgebase"),

    #-----------------------------support-ticket
    path('support_ticket', views.support_ticket, name="support_ticket"), 
    
    
    
]