# Attendance: Editable Over Time

Makes `overtime_hours` ("Over Time") editable — and multi-editable — in the
Attendances list view (`hr_attendance.view_attendance_tree`).

Exists because the same override lived in the partner's
`arplama_custom_test` (`view_hr_attendance_tree_inherit`, `noupdate=False`)
and was dropped on every update of that module (2026-09-04, 09-10, 10-15).

After installing, archive the hand-made stopgap view `ir.ui.view` id 11217
("hr.attendance.list.overtime.editable (ARPLAMA)") — it does the same thing.
