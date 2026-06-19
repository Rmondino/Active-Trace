# Spec: analisis-export

## Overview
Export uncorrected textual assignments as a downloadable xlsx file. Only textual-scale activities with no grade are included (RN-07/RN-08). Computation in Services.

## Requirements

### REQ-EXP-001: Export uncorrected submissions
The system MUST generate an xlsx file listing uncorrected textual submissions.

**Scenarios:**

**Scenario: Export lists textual activities without grade**
- Given: a student completed a textual TP but has no grade
- When: `GET /api/analisis/exportar-sin-corregir?materia_id=X`
- Then: the student's submission is in the exported xlsx

**Scenario: Numeric activities excluded from export**
- Given: a numeric activity has no grade (student didn't submit)
- When: export is generated
- Then: the numeric activity is NOT included (RN-08)

**Scenario: Export returns valid xlsx**
- When: export endpoint is called
- Then: response has `Content-Type: application/vnd.openxmlformats-officedocument.spreadsheetml.sheet` and valid xlsx bytes
