import logging
import os
import json

import Levenshtein as levenshtein

import icubam.predicu.data

logging.getLogger().setLevel(logging.INFO)

api_key = os.getenv("ICUBAM_API_KEY")
icubam_host = os.getenv("ICUBAM_HOST")

france_departments = set(
  list(icubam.predicu.data.load_france_departments().departmentName.unique())
)
bedcounts = icubam.predicu.data.load_icubam(
  api_key=api_key, icubam_host=icubam_host, preprocess=False
)
icubam_departments = set(list(bedcounts.icu_dept.unique()))

suspects = icubam_departments - france_departments
candidates = france_departments - icubam_departments

fixes = dict()
for suspect in suspects:
  best_candidate = None
  best_candidate_dist = int(1e6)
  for candidate in candidates:
    dist = levenshtein.distance(suspect, candidate)
    if dist < best_candidate_dist:
      best_candidate = candidate
      best_candidate_dist = dist
  fixes[suspect] = best_candidate
  print(suspect, '->', best_candidate, '( dist =', best_candidate_dist, ')')

with open('icubam/predicu/data/icubam_department_typo_fixes.json', 'w') as f:
  json.dump(fixes, f)
