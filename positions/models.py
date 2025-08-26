# positions/models.py

from django.db import models

class Skill(models.Model):
    CATEGORY_CHOICES = [
        ('coding', 'Coding'),
        ('management', 'Management'),
        ('ai', 'AI'),
    ]

    name = models.CharField(max_length=100, unique=True)
    category = models.CharField(
        max_length=20,
        choices=CATEGORY_CHOICES,
        default='coding',
    )

    def __str__(self):
        return f"{self.name} ({self.get_category_display()})"



class Tag(models.Model):
    name = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.name

class Position(models.Model):
    STATUS_CHOICES = [
        ('draft',     'Draft'),
        ('posted',    'Posted'),
        ('retracted', 'Retracted'),
        ('deleted',   'Deleted'),
    ]

    title       = models.CharField(max_length=200)
    company     = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    tags        = models.ManyToManyField(Tag, blank=True)
    status      = models.CharField(
                     max_length=10,
                     choices=STATUS_CHOICES,
                     default='draft'
                  )
    created_at  = models.DateTimeField(auto_now_add=True)
    updated_at  = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.title} at {self.company}"

class PositionSkillRequirement(models.Model):
    PROFICIENCY_CHOICES = [
        ('low',    'Low'),
        ('medium', 'Medium'),
        ('high',   'High'),
    ]

    position   = models.ForeignKey(
                   Position,
                   on_delete=models.CASCADE,
                   related_name='requirements'
                 )
    skill      = models.ForeignKey(Skill, on_delete=models.PROTECT)
    level_pct  = models.PositiveIntegerField(
                   default=50,
                   help_text="Required proficiency % (0–100)"
                 )

    # **New field**: relative importance rating (1–5)
    importance = models.PositiveSmallIntegerField(
                   default=1,
                   help_text="Relative importance (1–5)"
                 )

    class Meta:
        unique_together = ('position', 'skill')

    def __str__(self):
        return (
            f"{self.skill.name}: "
            f"{self.level_pct}% @ importance={self.importance} "
            f"for {self.position.title}"
        )
