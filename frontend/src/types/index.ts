export type User = {
  id: string;
  name: string;
  email: string;
  company?: string;
  role: "ADMIN" | "PROCUREMENT_MANAGER" | "ANALYST" | "VIEWER";
  is_active: boolean;
  created_at: string;
};

export type Project = {
  id: string;
  name: string;
  description?: string;
  category?: string;
  budget?: number;
  currency: string;
  deadline?: string;
  status: "DRAFT" | "ACTIVE" | "EVALUATION" | "COMPLETED" | "CANCELLED";
  weight_price: number;
  weight_technical: number;
  weight_security: number;
  weight_support: number;
  weight_implementation: number;
  weight_contract: number;
  created_by_id: string;
  created_at: string;
  updated_at: string;
  vendor_count?: number;
  proposal_count?: number;
  requirement_count?: number;
};

export type Vendor = {
  id: string;
  company_name: string;
  contact_name?: string;
  email?: string;
  phone?: string;
  website?: string;
  industry?: string;
  description?: string;
  status: string;
  created_at: string;
};

export type ProjectVendor = Vendor & {
  project_vendor_id: string;
  proposal_count: number;
  project_status: string;
  notes?: string;
};

export type Requirement = {
  id: string;
  project_id: string;
  name: string;
  description?: string;
  category: string;
  priority: "LOW" | "MEDIUM" | "HIGH" | "CRITICAL";
  weight: number;
  mandatory: boolean;
  expected_value?: string;
  comparison_operator?: string;
  order_index: number;
};

export type Proposal = {
  id: string;
  project_id: string;
  vendor_id: string;
  project_vendor_id: string;
  title: string;
  status:
    | "UPLOADED" | "QUEUED" | "PROCESSING" | "EXTRACTING"
    | "ANALYZING" | "SCORING" | "COMPLETED" | "FAILED";
  progress: number;
  current_stage?: string;
  error_message?: string;
  proposal_date?: string;
  valid_until?: string;
  created_at: string;
  updated_at: string;
  analyzed_at?: string;
  vendor_name?: string;
  vendor_company?: string;
  score?: number;
  rank?: number;
};

export type PricingDetail = {
  id: string;
  currency?: string;
  total_cost?: number;
  annual_cost?: number;
  monthly_cost?: number;
  implementation_cost?: number;
  license_cost?: number;
  support_cost?: number;
  maintenance_cost?: number;
  training_cost?: number;
  migration_cost?: number;
  additional_fees?: number;
  discounts?: number;
  taxes?: number;
  year1_total?: number;
  year3_total?: number;
  year5_total?: number;
  recurring_annual_cost?: number;
  pricing_model?: string;
  billing_frequency?: string;
  price_escalation_pct?: number;
  assumptions?: Record<string, any>;
  raw_breakdown?: Record<string, any>;
  [key: string]: any;
};

export type ExtractedField = {
  id: string;
  field_name: string;
  field_group: string;
  value?: string;
  value_type: string;
  confidence: number;
  is_fact: boolean;
  is_inferred: boolean;
  source_document?: string;
  source_page?: number;
  source_section?: string;
  source_quote?: string;
};

export type RequirementEvaluation = {
  id: string;
  requirement_id: string;
  requirement_name?: string;
  status: "MEETS" | "PARTIALLY_MEETS" | "DOES_NOT_MEET" | "UNKNOWN";
  score: number;
  reason: string;
  confidence: number;
  evidence_document?: string;
  evidence_page?: number;
  evidence_section?: string;
  evidence_quote?: string;
  evaluated_value?: string;
};

export type Risk = {
  id: string;
  category: string;
  severity: "LOW" | "MEDIUM" | "HIGH" | "CRITICAL";
  title: string;
  description: string;
  evidence_quote?: string;
  evidence_document?: string;
  evidence_page?: number;
  recommendation?: string;
};

export type MissingInfo = {
  id: string;
  field_name: string;
  importance: string;
  why_it_matters?: string;
};

export type ClarificationQuestion = {
  id: string;
  question: string;
  category?: string;
  priority: string;
};

export type ScoringComponent = {
  name: string;
  weight: number;
  raw_score: number;
  weighted_score: number;
  explanation?: string;
};

export type VendorScore = {
  id: string;
  proposal_id: string;
  total_score: number;
  price_score: number;
  technical_score: number;
  security_score: number;
  support_score: number;
  implementation_score: number;
  contract_score: number;
  is_eligible: boolean;
  ineligibility_reasons?: string[];
  rank?: number;
  components: ScoringComponent[];
  notes?: string;
};

export type Recommendation = {
  id: string;
  proposal_id: string;
  recommended: boolean;
  rank?: number;
  summary: string;
  reasoning: string;
  strengths: string[];
  weaknesses: string[];
  next_steps: string[];
  decision?: string;
};

export type ProposalDetail = Proposal & {
  documents: any[];
  pricing?: PricingDetail;
  extracted_fields: ExtractedField[];
  evaluations: RequirementEvaluation[];
  risks: Risk[];
  missing_info: MissingInfo[];
  clarification_questions: ClarificationQuestion[];
  score?: VendorScore;
  recommendation?: Recommendation;
  current_job?: AnalysisJob;
};

export type AnalysisJob = {
  id: string;
  proposal_id: string;
  status: string;
  current_stage?: string;
  progress: number;
  stage_message?: string;
  error_message?: string;
  started_at?: string;
  completed_at?: string;
  created_at: string;
};

export type ComparisonResponse = {
  project_id: string;
  project_name: string;
  vendors: {
    vendor_id: string;
    vendor_name: string;
    proposal_id?: string;
    pricing?: PricingDetail;
    score?: VendorScore;
    recommendation?: Recommendation;
    risk_counts: Record<string, number>;
    compliance_pct: number;
    meets_mandatory: number;
    total_mandatory: number;
  }[];
  weights: Record<string, number>;
  ranking: { vendor_id: string; vendor_name: string; score: number; rank?: number; eligible: boolean }[];
};
