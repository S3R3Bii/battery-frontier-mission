CREATE TABLE IF NOT EXISTS data_sources (
    source_id VARCHAR PRIMARY KEY,
    name VARCHAR NOT NULL,
    url VARCHAR NOT NULL,
    access_date DATE,
    license_status VARCHAR NOT NULL,
    license_note VARCHAR NOT NULL,
    variables_json JSON NOT NULL,
    reliability_rating INTEGER NOT NULL CHECK (reliability_rating BETWEEN 1 AND 5),
    update_frequency VARCHAR NOT NULL,
    limitations VARCHAR NOT NULL,
    ingestion_status VARCHAR NOT NULL,
    citation_ids_json JSON NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS citations (
    citation_id VARCHAR PRIMARY KEY,
    title VARCHAR NOT NULL,
    authors_json JSON NOT NULL,
    publication_year INTEGER,
    doi VARCHAR,
    url VARCHAR NOT NULL,
    source_type VARCHAR NOT NULL,
    peer_reviewed BOOLEAN NOT NULL,
    metadata_status VARCHAR NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS claims (
    claim_id VARCHAR PRIMARY KEY,
    claim_text VARCHAR NOT NULL,
    evidence_class VARCHAR NOT NULL CHECK (
        evidence_class IN (
            'known_experimental',
            'literature_projection',
            'simulation_estimate',
            'theoretical_limit',
            'speculative_hypothesis'
        )
    ),
    system_boundary VARCHAR NOT NULL,
    review_status VARCHAR NOT NULL,
    uncertainty_json JSON NOT NULL,
    citation_ids_json JSON NOT NULL,
    source_record_ids_json JSON NOT NULL,
    reviewer VARCHAR,
    reviewed_at TIMESTAMP,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS assumptions (
    assumption_id VARCHAR NOT NULL,
    version INTEGER NOT NULL,
    name VARCHAR NOT NULL,
    category VARCHAR NOT NULL,
    system_boundary VARCHAR NOT NULL,
    value_json JSON NOT NULL,
    unit VARCHAR NOT NULL,
    evidence_class VARCHAR NOT NULL,
    status VARCHAR NOT NULL,
    uncertainty_json JSON NOT NULL,
    citation_ids_json JSON NOT NULL,
    rationale VARCHAR NOT NULL,
    sensitivity VARCHAR NOT NULL,
    owner VARCHAR NOT NULL,
    review_due DATE NOT NULL,
    PRIMARY KEY (assumption_id, version)
);

CREATE TABLE IF NOT EXISTS chemistry_families (
    chemistry_family_id VARCHAR PRIMARY KEY,
    name VARCHAR NOT NULL,
    evidence_class VARCHAR NOT NULL,
    status VARCHAR NOT NULL,
    scope VARCHAR NOT NULL,
    known_constraints_json JSON NOT NULL,
    required_metrics_json JSON NOT NULL,
    citation_ids_json JSON NOT NULL
);

CREATE TABLE IF NOT EXISTS materials (
    material_id VARCHAR PRIMARY KEY,
    preferred_name VARCHAR NOT NULL,
    formula VARCHAR,
    composition_json JSON NOT NULL,
    structure_id VARCHAR,
    chemistry_family_id VARCHAR,
    source_id VARCHAR NOT NULL,
    source_record_id VARCHAR NOT NULL,
    evidence_class VARCHAR NOT NULL,
    provenance_json JSON NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS measurements (
    measurement_id VARCHAR PRIMARY KEY,
    subject_id VARCHAR NOT NULL,
    metric_name VARCHAR NOT NULL,
    value DOUBLE NOT NULL,
    unit VARCHAR NOT NULL,
    system_boundary VARCHAR NOT NULL,
    evidence_class VARCHAR NOT NULL,
    conditions_json JSON NOT NULL,
    uncertainty_json JSON NOT NULL,
    citation_ids_json JSON NOT NULL,
    source_id VARCHAR NOT NULL,
    source_record_id VARCHAR NOT NULL,
    extraction_method VARCHAR NOT NULL,
    reviewed_by VARCHAR,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS experimental_source_snapshots (
    snapshot_id VARCHAR PRIMARY KEY,
    source_id VARCHAR NOT NULL,
    source_name VARCHAR NOT NULL,
    source_url VARCHAR NOT NULL,
    doi VARCHAR,
    license_status VARCHAR NOT NULL,
    license_name VARCHAR NOT NULL,
    retrieval_timestamp TIMESTAMP NOT NULL,
    row_count INTEGER NOT NULL,
    metadata_only BOOLEAN NOT NULL,
    system_boundary VARCHAR NOT NULL,
    limitations VARCHAR NOT NULL,
    manifest_sha256 VARCHAR NOT NULL,
    manifest_json JSON NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS raw_file_manifests (
    raw_file_id VARCHAR PRIMARY KEY,
    snapshot_id VARCHAR NOT NULL,
    source_id VARCHAR NOT NULL,
    file_name VARCHAR NOT NULL,
    url VARCHAR NOT NULL,
    local_path VARCHAR NOT NULL,
    supplied_md5 VARCHAR,
    computed_md5 VARCHAR,
    computed_sha256 VARCHAR,
    expected_size_bytes BIGINT,
    local_size_bytes BIGINT,
    retrieval_timestamp TIMESTAMP NOT NULL,
    parser_status VARCHAR NOT NULL,
    system_boundary VARCHAR NOT NULL,
    license_status VARCHAR NOT NULL,
    limitations VARCHAR NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS parsed_cell_timeseries (
    parsed_timeseries_id VARCHAR PRIMARY KEY,
    raw_file_id VARCHAR NOT NULL,
    source_id VARCHAR NOT NULL,
    file_name VARCHAR NOT NULL,
    row_count INTEGER NOT NULL,
    units_json JSON NOT NULL,
    column_summary_json JSON NOT NULL,
    sign_conventions_json JSON NOT NULL,
    quality_status VARCHAR NOT NULL,
    system_boundary VARCHAR NOT NULL,
    pack_level_evidence BOOLEAN NOT NULL,
    candidate_ranking_evidence BOOLEAN NOT NULL,
    parsed_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS cell_cycle_summaries (
    cycle_summary_id VARCHAR PRIMARY KEY,
    parsed_timeseries_id VARCHAR NOT NULL,
    source_id VARCHAR NOT NULL,
    file_name VARCHAR NOT NULL,
    cycle_scope VARCHAR NOT NULL,
    metrics_json JSON NOT NULL,
    caveats_json JSON NOT NULL,
    system_boundary VARCHAR NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS impedance_summaries (
    impedance_summary_id VARCHAR PRIMARY KEY,
    raw_file_id VARCHAR NOT NULL,
    source_id VARCHAR NOT NULL,
    file_name VARCHAR NOT NULL,
    row_count INTEGER NOT NULL,
    columns_json JSON NOT NULL,
    missing_values_json JSON NOT NULL,
    quality_status VARCHAR NOT NULL,
    system_boundary VARCHAR NOT NULL,
    pack_level_evidence BOOLEAN NOT NULL,
    candidate_ranking_evidence BOOLEAN NOT NULL,
    parsed_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS measurement_quality_reports (
    report_id VARCHAR PRIMARY KEY,
    source_id VARCHAR NOT NULL,
    report_path VARCHAR NOT NULL,
    report_sha256 VARCHAR NOT NULL,
    quality_status VARCHAR NOT NULL,
    parsed_timeseries_count INTEGER NOT NULL,
    parsed_impedance_count INTEGER NOT NULL,
    failed_file_count INTEGER NOT NULL,
    system_boundary VARCHAR NOT NULL,
    pack_level_evidence BOOLEAN NOT NULL,
    candidate_ranking_evidence BOOLEAN NOT NULL,
    generated_at TIMESTAMP NOT NULL,
    report_json JSON NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS aviation_scenarios (
    scenario_id VARCHAR NOT NULL,
    version INTEGER NOT NULL,
    name VARCHAR NOT NULL,
    evidence_class VARCHAR NOT NULL,
    status VARCHAR NOT NULL,
    parameters_json JSON NOT NULL,
    uncertainty_note VARCHAR NOT NULL,
    citation_ids_json JSON NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (scenario_id, version)
);

CREATE TABLE IF NOT EXISTS simulation_runs (
    run_id VARCHAR PRIMARY KEY,
    model_name VARCHAR NOT NULL,
    model_version VARCHAR NOT NULL,
    code_commit VARCHAR NOT NULL,
    input_hash VARCHAR NOT NULL,
    config_hash VARCHAR NOT NULL,
    environment_json JSON NOT NULL,
    started_at TIMESTAMP NOT NULL,
    completed_at TIMESTAMP,
    status VARCHAR NOT NULL,
    error_message VARCHAR
);

CREATE TABLE IF NOT EXISTS physics_reference_cases (
    reference_case_id VARCHAR NOT NULL,
    version INTEGER NOT NULL,
    name VARCHAR NOT NULL,
    evidence_class VARCHAR NOT NULL,
    status VARCHAR NOT NULL,
    definition_json JSON NOT NULL,
    citation_ids_json JSON NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (reference_case_id, version)
);

CREATE TABLE IF NOT EXISTS physics_reference_results (
    calculation_id VARCHAR PRIMARY KEY,
    reference_case_id VARCHAR NOT NULL,
    reference_case_version INTEGER NOT NULL,
    package_version VARCHAR NOT NULL,
    code_snapshot_sha256 VARCHAR NOT NULL,
    config_sha256 VARCHAR NOT NULL,
    result_json JSON NOT NULL,
    evidence_class VARCHAR NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS aviation_mission_cases (
    mission_case_id VARCHAR NOT NULL,
    version INTEGER NOT NULL,
    name VARCHAR NOT NULL,
    evidence_class VARCHAR NOT NULL,
    status VARCHAR NOT NULL,
    definition_json JSON NOT NULL,
    citation_ids_json JSON NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (mission_case_id, version)
);

CREATE TABLE IF NOT EXISTS aviation_mission_results (
    calculation_id VARCHAR PRIMARY KEY,
    mission_case_id VARCHAR NOT NULL,
    mission_case_version INTEGER NOT NULL,
    package_version VARCHAR NOT NULL,
    code_snapshot_sha256 VARCHAR NOT NULL,
    config_sha256 VARCHAR NOT NULL,
    converged BOOLEAN NOT NULL,
    feasible BOOLEAN NOT NULL,
    result_json JSON NOT NULL,
    evidence_class VARCHAR NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS simulation_results (
    result_id VARCHAR PRIMARY KEY,
    run_id VARCHAR NOT NULL,
    subject_id VARCHAR NOT NULL,
    metric_name VARCHAR NOT NULL,
    value DOUBLE NOT NULL,
    unit VARCHAR NOT NULL,
    system_boundary VARCHAR NOT NULL,
    evidence_class VARCHAR NOT NULL DEFAULT 'simulation_estimate',
    uncertainty_json JSON NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS candidate_assessments (
    assessment_id VARCHAR PRIMARY KEY,
    subject_id VARCHAR NOT NULL,
    assessment_version VARCHAR NOT NULL,
    objectives_json JSON NOT NULL,
    uncertainty_json JSON NOT NULL,
    evidence_summary_json JSON NOT NULL,
    pareto_status VARCHAR NOT NULL,
    reality_filter_status VARCHAR NOT NULL,
    limitations_json JSON NOT NULL,
    reproducibility_score DOUBLE,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS failed_hypotheses (
    hypothesis_id VARCHAR PRIMARY KEY,
    title VARCHAR NOT NULL,
    hypothesis_text VARCHAR NOT NULL,
    test_method VARCHAR NOT NULL,
    result_summary VARCHAR NOT NULL,
    failure_reason VARCHAR NOT NULL,
    evidence_class VARCHAR NOT NULL,
    run_ids_json JSON NOT NULL,
    citation_ids_json JSON NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS artifacts (
    artifact_id VARCHAR PRIMARY KEY,
    artifact_type VARCHAR NOT NULL,
    path_or_url VARCHAR NOT NULL,
    sha256 VARCHAR NOT NULL,
    generated_by VARCHAR NOT NULL,
    input_hashes_json JSON NOT NULL,
    publication_status VARCHAR NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);
