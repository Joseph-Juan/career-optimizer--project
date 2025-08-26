# accounts/views.py
import io
from types import SimpleNamespace
from django.db import models
from django.db.models import Sum
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.http import require_POST
from django.http import JsonResponse, HttpResponse, HttpResponseBadRequest, HttpResponseServerError
from xhtml2pdf import pisa
from django.template.loader import render_to_string
from django.conf import settings
from django.urls import reverse
from .models import (
    User, StudentProfile, StudentSkill, SavedPosition,
    StudentCV, CVExperience, CVLanguage
)
from .forms import (
    StudentRegistrationForm,
    CVForm, CVExperienceForm, CVLanguageForm,
    CVExperienceFormSet, CVLanguageFormSet
)
from .decorators import admin_required
from positions.models import Position, Skill, PositionSkillRequirement

# ---------- (existing admin/student auth views) ----------
@never_cache
@csrf_protect
def admin_login_view(request):
    if request.method == 'POST':
        ident = request.POST.get('username','').strip()
        pwd   = request.POST.get('password','')
        user  = authenticate(request, username=ident, password=pwd)
        if user is None:
            u = User.objects.filter(email__iexact=ident).first()
            if u:
                user = authenticate(request, username=u.username, password=pwd)
        if user and user.is_active and user.is_admin:
            login(request, user)
            return redirect('accounts:admin_dashboard')
        return render(request, 'accounts/admin_login.html', {
            'error_message': 'Invalid credentials or not an admin.'
        })
    return render(request, 'accounts/admin_login.html')


def admin_logout_view(request):
    logout(request)
    return redirect('accounts:admin_login')


@admin_required
def admin_dashboard(request):
    return render(request, 'accounts/admin_dashboard.html')


@admin_required
def admin_view_matches(request):
    return render(request, 'accounts/admin_matches.html')


# Student auth
def student_register_view(request):
    if request.method == 'POST':
        form = StudentRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            StudentProfile.objects.create(user=user)
            login(request, user)
            return redirect('accounts:student_dashboard')
    else:
        form = StudentRegistrationForm()
    return render(request, 'accounts/student_register.html', {'form': form})


def student_login_view(request):
    error = None
    if request.method == 'POST':
        ident = request.POST.get('username','').strip()
        pwd   = request.POST.get('password','')
        user  = authenticate(request, username=ident, password=pwd)
        if user is None:
            u = User.objects.filter(email__iexact=ident).first()
            if u:
                user = authenticate(request, username=u.username, password=pwd)
        if user and user.is_active and not user.is_admin:
            login(request, user)
            return redirect('accounts:student_dashboard')
        error = "Incorrect credentials."
    return render(request, 'accounts/student_login.html', {'error_message': error})


def student_logout_view(request):
    logout(request)
    return redirect('accounts:student_login')


# Student Dashboard
@login_required(login_url='accounts:student_login')
def student_dashboard(request):
    return render(request, 'accounts/student_dashboard.html')


# ---------------- CV view (persistent + PDF export) -------------------------

def _link_callback(uri, rel):
    """
    Resolve static/media URIs for xhtml2pdf.
    """
    import os
    from django.conf import settings
    s_root = settings.STATIC_ROOT or settings.STATICFILES_DIRS[0] if getattr(settings, 'STATICFILES_DIRS', None) else None
    m_root = settings.MEDIA_ROOT

    if uri.startswith(settings.MEDIA_URL):
        path = os.path.join(m_root, uri.replace(settings.MEDIA_URL, ""))
    elif uri.startswith(settings.STATIC_URL):
        path = os.path.join(s_root, uri.replace(settings.STATIC_URL, ""))
    else:
        path = uri

    if not os.path.exists(path):
        return uri  # fallback to original
    return path


@login_required(login_url='accounts:student_login')
def student_cv_view(request):
    """
    - GET: show the CV form prefilled from StudentCV if present.
    - POST: "save" or "save_and_download" actions:
        * Save: save form+formsets and redirect back to the CV page with a success message
        * Save & Download: same as Save then produce a PDF response for download
    """
    profile, _ = StudentProfile.objects.get_or_create(user=request.user)
    cv, created = StudentCV.objects.get_or_create(profile=profile)

    # instantiate form + formsets bound to existing CV data
    if request.method == 'POST':
        action = request.POST.get('action', 'save')  # 'save' or 'download'
        cv_form = CVForm(request.POST, instance=cv, prefix='cv')

        # Build formsets bound to POST
        exp_qs = CVExperience.objects.filter(cv=cv).order_by('-start_date')
        lang_qs = CVLanguage.objects.filter(cv=cv).order_by('-mother_tongue')

        exp_formset = CVExperienceFormSet(request.POST, queryset=exp_qs, prefix='exp')
        lang_formset = CVLanguageFormSet(request.POST, queryset=lang_qs, prefix='lang')

        if cv_form.is_valid() and exp_formset.is_valid() and lang_formset.is_valid():
            # Save CV
            cv = cv_form.save()

            # Save experiences: handle deletions
            exps = exp_formset.save(commit=False)
            # mark all existing for deletion, we'll undelete ones present
            existing_ids = [e.pk for e in CVExperience.objects.filter(cv=cv)]
            # Delete objects flagged for deletion
            for obj in exp_formset.deleted_objects:
                obj.delete()
            for obj in exps:
                obj.cv = cv
                obj.save()

            # Save languages
            langs = lang_formset.save(commit=False)
            for obj in lang_formset.deleted_objects:
                obj.delete()
            for obj in langs:
                obj.cv = cv
                obj.save()

            # If user clicked download, build PDF
            if action == 'download':
                # render pdf template
                html = render_to_string('accounts/student_cv_pdf.html', {
                    'cv': cv,
                    'experience': cv.experiences.all(),
                    'languages': cv.languages.all(),
                })
                out = io.BytesIO()
                # create pdf
                pdf = pisa.CreatePDF(io.BytesIO(html.encode('utf-8')), dest=out, link_callback=_link_callback)
                if pdf.err:
                    return HttpResponseServerError("Error creating PDF.")
                out.seek(0)
                filename = f"cv-{request.user.username}.pdf"
                response = HttpResponse(out.read(), content_type='application/pdf')
                response['Content-Disposition'] = f'attachment; filename="{filename}"'
                return response

            # Otherwise just save and redirect (standard Post/Redirect/Get)
            return redirect('accounts:student_cv')
        else:
            # invalid — render with errors
            return render(request, 'accounts/student_cv.html', {
                'cv_form': cv_form,
                'exp_formset': exp_formset,
                'lang_formset': lang_formset,
            })
    else:
        # GET: show existing values
        cv_form = CVForm(instance=cv, prefix='cv')

        exp_qs = CVExperience.objects.filter(cv=cv).order_by('-start_date')
        lang_qs = CVLanguage.objects.filter(cv=cv).order_by('-mother_tongue')

        # If empty, show one blank form in each formset by default
        if not exp_qs.exists():
            exp_formset = CVExperienceFormSet(queryset=CVExperience.objects.none(), prefix='exp', initial=[{}])
        else:
            exp_formset = CVExperienceFormSet(queryset=exp_qs, prefix='exp')

        if not lang_qs.exists():
            lang_formset = CVLanguageFormSet(queryset=CVLanguage.objects.none(), prefix='lang', initial=[{}])
        else:
            lang_formset = CVLanguageFormSet(queryset=lang_qs, prefix='lang')

        return render(request, 'accounts/student_cv.html', {
            'cv_form': cv_form,
            'exp_formset': exp_formset,
            'lang_formset': lang_formset,
        })


# ---------- Browse & matching (existing code) ----------
@login_required(login_url='accounts:student_login')
def browse_positions_view(request):
    profile, _  = StudentProfile.objects.get_or_create(user=request.user)
    saved_ids   = set(profile.saved_positions.values_list('position_id', flat=True))
    student_map = { ss.skill_id: ss.proficiency for ss in profile.student_skills.all() }

    positions = []
    for pos in Position.objects.all().order_by('-created_at'):
        reqs      = PositionSkillRequirement.objects.filter(position=pos)
        total_imp = sum(r.importance for r in reqs) or 1
        score     = 0.0
        for r in reqs:
            weight = r.importance / total_imp * 100
            sp     = student_map.get(r.skill_id)
            if sp:
                num   = {'low':40,'medium':75,'high':100}[sp]
                ratio = num / r.level_pct
                score += weight * min(ratio, 1.0)
        pos.match_score = f"{score:.1f}"
        positions.append(pos)

    return render(request, 'accounts/student_positions.html', {
        'positions': positions,
        'saved_ids': saved_ids,
    })


@login_required(login_url='accounts:student_login')
@require_POST
def toggle_save_position(request):
    profile, _ = StudentProfile.objects.get_or_create(user=request.user)
    pos        = get_object_or_404(Position, pk=request.POST.get('position_id'))
    saved, created = SavedPosition.objects.get_or_create(profile=profile, position=pos)
    if not created:
        saved.delete(); action='removed'
    else:
        action='added'
    return JsonResponse({'action': action, 'position_id': pos.pk})


@login_required(login_url='accounts:student_login')
def student_position_detail(request, pk):
    pos         = get_object_or_404(Position, pk=pk)
    reqs        = PositionSkillRequirement.objects.filter(position=pos).select_related('skill')
    profile, _  = StudentProfile.objects.get_or_create(user=request.user)
    student_map = { ss.skill_id: ss.proficiency for ss in profile.student_skills.all() }

    total_imp   = sum(r.importance for r in reqs) or 1
    match_score = 0.0
    pct_to_label= {40:'Low',75:'Medium',100:'High'}

    for r in reqs:
        r.required_proficiency = pct_to_label.get(r.level_pct, f"{r.level_pct}%")
        weight = r.importance / total_imp * 100
        r.weight_pct = f"{weight:.1f}"
        sp = student_map.get(r.skill_id)
        if sp:
            num   = {'low':40,'medium':75,'high':100}[sp]
            ratio = num / r.level_pct
            match_score += weight * min(ratio, 1.0)
            r.your_proficiency = pct_to_label.get(num, f"{num}%")
        else:
            r.your_proficiency = 'None'

    return render(request, 'accounts/student_position_detail.html', {
        'position':     pos,
        'requirements': reqs,
        'match_score':  f"{match_score:.1f}",
    })


# ---------- Student: My Skills (existing) ----------
@login_required(login_url='accounts:student_login')
def my_skills_view(request):
    profile, _  = StudentProfile.objects.get_or_create(user=request.user)
    used_ids    = profile.student_skills.values_list('skill_id', flat=True)
    available   = Skill.objects.exclude(pk__in=used_ids)
    current     = profile.student_skills.select_related('skill').all()
    return render(request, 'accounts/student_skills.html', {
        'current_skills':   current,
        'available_skills': available,
    })


@require_POST
@login_required(login_url='accounts:student_login')
def add_skill_view(request):
    profile, _ = StudentProfile.objects.get_or_create(user=request.user)
    sid        = request.POST.get('add_skill_id')
    prof       = request.POST.get('proficiency','medium')
    if not sid or prof not in dict(StudentSkill.PROFICIENCY_CHOICES):
        return JsonResponse({'error':'Bad request'}, status=400)
    skill = get_object_or_404(Skill, pk=int(sid))
    obj, _ = StudentSkill.objects.get_or_create(
        profile=profile,
        skill=skill,
        defaults={'proficiency':prof}
    )
    return JsonResponse({
        'pk': obj.pk,
        'skill_name': skill.name,
        'proficiency_vals': dict(StudentSkill.PROFICIENCY_CHOICES),
        'current_prof': obj.proficiency,
    })


@require_POST
@login_required(login_url='accounts:student_login')
def update_skill_view(request):
    pk   = request.POST.get('pk')
    prof = request.POST.get('proficiency')
    if not pk or prof not in dict(StudentSkill.PROFICIENCY_CHOICES):
        return JsonResponse({'error':'Bad request'}, status=400)
    obj = get_object_or_404(StudentSkill, pk=pk, profile__user=request.user)
    obj.proficiency = prof
    obj.save()
    return JsonResponse({'success':True})


@require_POST
@login_required(login_url='accounts:student_login')
def delete_skill_view(request):
    pk  = request.POST.get('pk')
    obj = get_object_or_404(StudentSkill, pk=pk, profile__user=request.user)
    obj.delete()
    return JsonResponse({'success':True})


@require_POST
@login_required(login_url='accounts:student_login')
def bulk_save_skills(request):
    try:
        data = __import__('json').loads(request.body)
    except ValueError:
        return HttpResponseBadRequest("Invalid JSON")
    profile, _ = StudentProfile.objects.get_or_create(user=request.user)
    for pk_str, prof in data.items():
        sk = get_object_or_404(StudentSkill, pk=int(pk_str), profile=profile)
        if prof in dict(StudentSkill.PROFICIENCY_CHOICES):
            sk.proficiency = prof
            sk.save()
    return JsonResponse({'status':'ok'})


# ---------- Saved positions (existing) ----------
def _calculate_match_score(profile, position):
    """
    Matches detail‐view logic exactly:
     - weight = importance / total_importance * 100
     - num = {'low':40,'medium':75,'high':100}[student_level]
     - ratio = num / r.level_pct
     - sum weight * min(ratio,1)
    """
    prof_map  = { ss.skill_id: ss.proficiency for ss in profile.student_skills.all() }
    reqs      = position.requirements.all()
    total_imp = reqs.aggregate(sum=Sum('importance'))['sum'] or 0
    if total_imp == 0:
        return 0.0

    score = 0.0
    for r in reqs:
        weight = r.importance / total_imp * 100
        stu    = prof_map.get(r.skill_id)
        if stu:
            num   = {'low':40,'medium':75,'high':100}[stu]
            ratio = num / r.level_pct
            score += weight * min(ratio, 1.0)
    return score


@login_required(login_url='accounts:student_login')
def saved_positions_view(request):
    profile = request.user.student_profile
    qset    = SavedPosition.objects.filter(profile=profile).select_related('position')

    wrapped = [
        SimpleNamespace(
            position    = sp.position,
            saved_at    = sp.saved_at,
            match_score = _calculate_match_score(profile, sp.position),
        )
        for sp in qset
    ]

    return render(request, 'accounts/student_saved_positions.html', {
        'saved_positions': wrapped,
    })
