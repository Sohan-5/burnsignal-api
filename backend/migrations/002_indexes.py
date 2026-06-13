# Key indexes
INDEXES = """
CREATE INDEX idx_projects_org ON projects(org_id);
CREATE INDEX idx_time_entries_project_date ON time_entries(project_id, entry_date);
CREATE INDEX idx_forecast_snapshots_project ON forecast_snapshots(project_id, snapshot_at DESC);
CREATE INDEX idx_imported_tasks_project ON imported_tasks(project_id, status);
CREATE INDEX idx_contractor_costs_project ON contractor_costs(project_id, start_date);
"""
