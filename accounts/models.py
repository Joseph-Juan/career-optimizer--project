# accounts/models.py
from django.db import models
from django.contrib.auth.models import AbstractUser
from positions.models import Position  # and Skill/Requirement live there
from django.utils import timezone

class User(AbstractUser):
    is_admin = models.BooleanField(default=False)


class StudentProfile(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="student_profile",
    )

    def __str__(self):
        return f"Profile for {self.user.username}"


class StudentSkill(models.Model):
    PROFICIENCY_CHOICES = [
        ("low",    "Low"),
        ("medium", "Medium"),
        ("high",   "High"),
    ]

    profile     = models.ForeignKey(
                      StudentProfile,
                      on_delete=models.CASCADE,
                      related_name="student_skills",
                  )
    skill       = models.ForeignKey(
                      'positions.Skill',
                      on_delete=models.CASCADE,
                  )
    proficiency = models.CharField(
                      max_length=10,
                      choices=PROFICIENCY_CHOICES,
                  )

    class Meta:
        unique_together = ("profile", "skill")

    def __str__(self):
        return f"{self.profile.user.username}: {self.skill.name} ({self.proficiency})"


class SavedPosition(models.Model):
    profile  = models.ForeignKey(
                   StudentProfile,
                   on_delete=models.CASCADE,
                   related_name="saved_positions",
               )
    position = models.ForeignKey(
                   Position,
                   on_delete=models.CASCADE,
               )
    saved_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-saved_at"]

    def __str__(self):
        return f"{self.profile.user.username} saved {self.position}"

    @property
    def match_score(self):
        """
        Compute and return the % match based on the student's skills
        versus the position's requirements.
        """
        # build map of skill_id -> level code
        prof_map = {
            ss.skill_id: ss.proficiency
            for ss in self.profile.student_skills.all()
        }
        reqs = self.position.requirements.all()
        total_weight = sum(r.importance for r in reqs)
        if total_weight == 0:
            return 0.0

        # numeric ordering of proficiency
        LEVEL_ORDER = {"low": 1, "medium": 2, "high": 3}

        matched = 0
        for r in reqs:
            student_lvl = prof_map.get(r.skill_id)
            req_lvl     = r.required_proficiency_code if hasattr(r, 'required_proficiency_code') else r.level_pct
            if student_lvl and LEVEL_ORDER.get(student_lvl,0) >= LEVEL_ORDER.get(req_lvl, 0):
                matched += r.importance

        return 100.0 * matched / total_weight


# ───────────────────────────────────────────────────────────────────────────────
# CV persistence models (new)
# ───────────────────────────────────────────────────────────────────────────────

class StudentCV(models.Model):
    """
    One CV per student profile (OneToOne). If you prefer multiple CVs per user
    change this to ForeignKey. I used OneToOne for simple edit/save reuse.
    """
    profile = models.OneToOneField(
        StudentProfile,
        on_delete=models.CASCADE,
        related_name='cv',
    )
    full_name = models.CharField(max_length=200, blank=True)
    email     = models.EmailField(blank=True)
    phone     = models.CharField(max_length=50, blank=True)
    address   = models.TextField(blank=True)
    objective = models.TextField(blank=True)  # "Job applied for / Personal statement"
    updated_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        verbose_name = "Student CV"
        verbose_name_plural = "Student CVs"

    def __str__(self):
        return f"CV for {self.profile.user.username}"


class CVExperience(models.Model):
    cv = models.ForeignKey(
        StudentCV,
        on_delete=models.CASCADE,
        related_name='experiences'
    )
    job_title = models.CharField(max_length=200)
    company   = models.CharField(max_length=200, blank=True)
    city      = models.CharField(max_length=100, blank=True)
    country   = models.CharField(max_length=100, blank=True)
    start_date = models.DateField()
    end_date   = models.DateField(null=True, blank=True)  # blank => Present
    description = models.TextField(blank=True)

    class Meta:
        ordering = ['-start_date']

    def __str__(self):
        return f"{self.job_title} @ {self.company}"


class CVLanguage(models.Model):
    CEFR_CHOICES = [
        ('A1', 'A1'),
        ('A2', 'A2'),
        ('B1', 'B1'),
        ('B2', 'B2'),
        ('C1', 'C1'),
        ('C2', 'C2'),
    ]

    cv = models.ForeignKey(
        StudentCV,
        on_delete=models.CASCADE,
        related_name='languages'
    )
    language = models.CharField(max_length=100)
    mother_tongue = models.BooleanField(default=False)
    listening = models.CharField(max_length=2, choices=CEFR_CHOICES, blank=True)
    reading = models.CharField(max_length=2, choices=CEFR_CHOICES, blank=True)
    spoken_interaction = models.CharField(max_length=2, choices=CEFR_CHOICES, blank=True)
    spoken_production = models.CharField(max_length=2, choices=CEFR_CHOICES, blank=True)
    writing = models.CharField(max_length=2, choices=CEFR_CHOICES, blank=True)

    class Meta:
        ordering = ['-mother_tongue']

    def __str__(self):
        return f"{self.language} ({'mother' if self.mother_tongue else 'other'})"
