# interfaces/skills/__init__.py
"""
Sprint 56 — Skills package.

Skills eru endurnýtanleg async föll sem departments og pipeline nota.
Sérhvert skill erfir BaseSkill og útfærir run().

Tiltæk skills:
  ClassifySkill   — domain flokkun (legal/finance/writing/research/general)
  TranslateSkill  — þýðing/fágun á íslensku (polish lag)
  SummarizeSkill  — texta samantekt
  ExtractSkill    — citations + entities úr texta
"""
from interfaces.skills.base import BaseSkill
from interfaces.skills.classify import ClassifySkill
from interfaces.skills.translate import TranslateSkill
from interfaces.skills.summarize import SummarizeSkill
from interfaces.skills.extract import ExtractSkill

__all__ = [
    "BaseSkill",
    "ClassifySkill",
    "TranslateSkill",
    "SummarizeSkill",
    "ExtractSkill",
]
