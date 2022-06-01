from django.contrib.postgres.aggregates import ArrayAgg
from django.db.models import Q
from django.http import JsonResponse
from django.views.generic.list import BaseListView
from django.views.generic.detail import BaseDetailView
from movies.models import Filmwork, RoleType


class MoviesApiMixin:
    model = Filmwork
    http_method_names = ['get']

    def get_queryset(self):
        fields = (
            'id', 'title', 'description', 'creation_date',
            'rating', 'type',
        )
        qs = Filmwork.objects.values(*fields).prefetch_related(
            'genres', 'persons'
        )
        qs = qs.annotate(
            genres=ArrayAgg('genres__name', distinct=True),
            actors=self.aggregate_person(RoleType.ACTOR),
            directors=self.aggregate_person(RoleType.DIRECTOR),
            writers=self.aggregate_person(RoleType.WRITER)
        )
        return qs

    def aggregate_person(self, role):
        return ArrayAgg(
            'persons__full_name',
            filter=Q(personfilmwork__role=role),
            distinct=True
        )

    def render_to_response(self, context, **response_kwargs):
        return JsonResponse(context)


class MoviesListApi(MoviesApiMixin, BaseListView):
    paginate_by = 50

    def get_context_data(self, *, object_list=None, **kwargs):
        queryset = self.get_queryset()

        paginator, page, queryset, is_paginated = self.paginate_queryset(
            queryset,
            self.paginate_by
        )

        context = {
            'count': paginator.count,
            'total_pages': paginator.num_pages,
            'prev': self.prev_page(page),
            'next': self.next_page(page),
            'results': list(page.object_list),
        }
        return context

    def prev_page(self, page):
        if page.has_previous():
            num = page.previous_page_number()
        else:
            num = None
        return num

    def next_page(self, page):
        if page.has_next():
            num = page.next_page_number()
        else:
            num = None
        return num

    def render_to_response(self, context, **response_kwargs):
        return JsonResponse(context)


class MoviesDetailApi(MoviesApiMixin, BaseDetailView):

    def get_context_data(self, **kwargs):
        return kwargs['object']
