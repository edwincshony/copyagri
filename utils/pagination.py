from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

# You can also import from Django settings for configurability
DEFAULT_PER_PAGE = 7

def paginate_queryset(request, queryset):
    """
    Generic pagination function with a globally set items per page.
    Change DEFAULT_PER_PAGE here to update pagination everywhere.
    """
    paginator = Paginator(queryset, DEFAULT_PER_PAGE)
    page_number = request.GET.get('page')

    try:
        page_obj = paginator.page(page_number)
    except PageNotAnInteger:
        page_obj = paginator.page(1)
    except EmptyPage:
        page_obj = paginator.page(paginator.num_pages)

    return page_obj, page_obj.object_list