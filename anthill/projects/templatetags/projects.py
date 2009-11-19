from django import template
from django.db.models import Count
from anthill.utils import chart_from_tags, _extract_chart_params, ChartNode
from anthill.projects.models import Project

register = template.Library()

@register.tag
def project_skills_piechart(parser, token):
    return chart_from_tags(Project, token)

@register.tag
def project_official_piechart(parser, token):
    width, height, args = _extract_chart_params(token)
    args = [arg.split(':') for arg in args]
    items = Project.objects.values('official').annotate(num=Count('id'))
    for item in items:
        if item.pop('official'):
            item['name'] = args[0][0]
            item['color'] = args[0][1]
        else:
            item['name'] = args[1][0]
            item['color'] = args[1][1]
    return ChartNode(items, width, height, chart_type='bhs')
