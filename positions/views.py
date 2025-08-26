from django.shortcuts               import render, get_object_or_404, redirect
from django.views                   import View
from django.views.generic           import ListView, FormView, DetailView, DeleteView
from django.contrib.auth.mixins     import UserPassesTestMixin
from django.http                    import JsonResponse, Http404, HttpResponseBadRequest
from django.views.decorators.http   import require_POST
from django.urls                    import reverse_lazy
from django.utils.decorators        import method_decorator
from django.views.decorators.cache  import never_cache

from .models import Position, Tag, Skill, PositionSkillRequirement
from .forms  import PositionStep1Form, SkillForm, TagForm


class AdminRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.is_admin

    def handle_no_permission(self):
        return redirect('accounts:admin_login')


@method_decorator(never_cache, name='dispatch')
class PositionListView(AdminRequiredMixin, ListView):
    model               = Position
    template_name       = 'positions/position_list.html'
    context_object_name = 'positions'

    def get_queryset(self):
        qs = super().get_queryset().order_by('-created_at')
        status = self.request.GET.get('status')
        valid_statuses = dict(Position.STATUS_CHOICES).keys()
        if status in valid_statuses:
            qs = qs.filter(status=status)
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['current_status'] = self.request.GET.get('status', '')
        ctx['status_choices'] = Position.STATUS_CHOICES
        return ctx


@method_decorator(never_cache, name='dispatch')
class PositionStep1View(AdminRequiredMixin, FormView):
    """
    Step 1: Title, Company, Description, Status & Tags
    """
    template_name = 'positions/position_step1.html'
    form_class    = PositionStep1Form

    def dispatch(self, request, *args, **kwargs):
        self.position = None
        if 'pk' in kwargs:
            self.position = get_object_or_404(Position, pk=kwargs['pk'])
        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        if self.position:
            kwargs['instance'] = self.position
        return kwargs

    def get_initial(self):
        if not self.position:
            return {}
        return {
            'title':       self.position.title,
            'company':     self.position.company,
            'description': self.position.description,
            'status':      self.position.status,
            'tags':        self.position.tags.all(),
        }

    def form_valid(self, form):
        pos = form.save()
        return redirect('positions:new_skills', pk=pos.pk)


@method_decorator(never_cache, name='dispatch')
class PositionSkillsView(AdminRequiredMixin, View):
    """
    Step 2: Add/edit/remove skills, importance & proficiency
    """
    template_name = 'positions/position_step2.html'

    def get(self, request, pk):
        pos = get_object_or_404(Position, pk=pk)
        used = pos.requirements.values_list('skill_id', flat=True)
        available_skills = Skill.objects.exclude(pk__in=used)
        return render(request, self.template_name, {
            'position':         pos,
            'available_skills': available_skills,
            'skill_form':       SkillForm(),
        })

    def post(self, request, pk):
        pos = get_object_or_404(Position, pk=pk)

        # AJAX add existing skill
        if 'add_skill_id' in request.POST:
            sid = int(request.POST['add_skill_id'])
            req, created = PositionSkillRequirement.objects.get_or_create(
                position=pos,
                skill_id=sid,
                defaults={'level_pct': 75, 'importance': 3}
            )
            return JsonResponse({
                'pk':               req.pk,
                'skill_name':       req.skill.name,
                'proficiency_vals': dict(PositionSkillRequirement.PROFICIENCY_CHOICES),
                'current_prof':     'medium',
                'importance':       req.importance,
            })

        # Handle edits/removals
        for req in pos.requirements.all():
            if request.POST.get(f'delete_{req.pk}') == 'on':
                req.delete()
                continue

            prof = request.POST.get(f'prof_{req.pk}')
            if prof in dict(PositionSkillRequirement.PROFICIENCY_CHOICES):
                mapping = {'low': 40, 'medium': 75, 'high': 100}
                req.level_pct = mapping.get(prof, req.level_pct)

            imp = request.POST.get(f'importance_{req.pk}')
            if imp and imp.isdigit():
                req.importance = max(1, min(5, int(imp)))

            req.save()

        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'status': 'ok'})
        return redirect('positions:new_review', pk=pk)


@method_decorator(never_cache, name='dispatch')
class PositionReviewView(AdminRequiredMixin, DetailView):
    """
    Step 3: Review & Post or Save Draft
    """
    model         = Position
    template_name = 'positions/position_review.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        reqs  = list(self.object.requirements.all())
        total = sum(r.importance for r in reqs)
        for r in reqs:
            r.weight_norm = round((r.importance / total * 100) if total else 0, 1)
        ctx['requirements_with_weight'] = reqs
        ctx['total_importance']        = total
        return ctx

    def post(self, request, *args, **kwargs):
        pos    = self.get_object()
        action = request.POST.get('action')
        pos.status = 'posted' if action == 'post' else 'draft'
        pos.save()
        return redirect('positions:list')


@method_decorator(never_cache, name='dispatch')
class PositionDeleteView(AdminRequiredMixin, DeleteView):
    model         = Position
    template_name = 'positions/position_confirm_delete.html'
    success_url   = reverse_lazy('positions:list')

    def get(self, request, *args, **kwargs):
        try:
            return super().get(request, *args, **kwargs)
        except Http404:
            return redirect('positions:list')


@method_decorator(never_cache, name='dispatch')
class PositionStatusView(AdminRequiredMixin, View):
    """
    POST to change status (draft/posted/retracted)
    """
    def post(self, request, pk):
        pos = get_object_or_404(Position, pk=pk)
        new = request.POST.get('status')
        if new in dict(Position.STATUS_CHOICES):
            pos.status = new
            pos.save()
        return redirect('positions:list')


@require_POST
def create_tag(request):
    form = TagForm(request.POST)
    if form.is_valid():
        t = form.save()
        return JsonResponse({'id': t.pk, 'name': t.name})
    return JsonResponse({'errors': form.errors}, status=400)


@require_POST
def create_skill(request):
    form = SkillForm(request.POST)

    # If not AJAX, redirect back instead of dumping JSON
    if request.headers.get('x-requested-with') != 'XMLHttpRequest':
        if form.is_valid():
            form.save()
            return redirect(request.META.get('HTTP_REFERER', '/'))
        return HttpResponseBadRequest("Invalid input", content_type="text/plain")

    # AJAX path
    if form.is_valid():
        skill = form.save()
        return JsonResponse({
            'id':       skill.pk,
            'name':     skill.name,
            'category': skill.category,
        })
    return JsonResponse({'errors': form.errors}, status=400)
