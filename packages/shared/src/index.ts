/**
 * SellerFlow AI - Canonical Financial Domain Types & Contracts
 * (c) 2026 SellerFlow AI. All monetary amounts represented as decimal strings.
 */

export type MarketplaceCode = 'amazon_in' | 'flipkart' | 'meesho';

export type DiscrepancyCategory = 
  | 'fee_overcharge'
  | 'fee_undercharge'
  | 'missing_payout'
  | 'unmatched_order'
  | 'weight_slab_overcharge'
  | 'return_uncredited'
  | 'variance';

export type DiscrepancySeverity = 'low' | 'medium' | 'high' | 'critical';

export type ReconciliationMatchStatus = 'matched' | 'partial' | 'unmatched' | 'disputed';

export type ImportStatus = 'PENDING' | 'PARSING' | 'COMPLETED' | 'FAILED';

export interface WorkspaceSummary {
  id: string;
  name: string;
  subscription_tier: 'free' | 'pro' | 'enterprise';
  created_at: string;
}

export interface StoreSummary {
  id: string;
  workspace_id: string;
  display_name: string;
  marketplace_code: MarketplaceCode;
  currency: string;
  is_active: boolean;
}

export interface CanonicalTransaction {
  id: string;
  external_order_id?: string;
  sku?: string;
  transaction_type: string;
  amount_type?: string;
  amount: string; // Decimal string e.g. "1250.50"
  currency: string;
  posted_date?: string;
  order_date?: string;
  source_row: number;
}

export interface DiscrepancyRecord {
  id: string;
  workspace_id: string;
  run_id: string;
  category: DiscrepancyCategory;
  severity: DiscrepancySeverity;
  title: string;
  explanation: string;
  external_order_id?: string;
  difference_amount: string; // Decimal string
  source_row_number?: number;
  status: 'OPEN' | 'INVESTIGATING' | 'DISPUTED' | 'RESOLVED' | 'IGNORED';
  created_at: string;
}

export interface ReconciliationSummary {
  ruleset_version: string;
  rate_card_version: string;
  total_orders: number;
  matched_count: number;
  partial_count: number;
  unmatched_count: number;
  discrepancy_count: number;
  total_expected: string;
  total_actual: string;
  total_difference: string;
  recoverable_amount: string;
}

export interface RateCardRule {
  id: string;
  marketplace_code: MarketplaceCode;
  category: string;
  price_min: string;
  price_max?: string;
  weight_slab_max_grams: number;
  referral_fee_percent: string;
  closing_fee_flat: string;
  shipping_fee_flat: string;
  pick_pack_fee_flat: string;
  effective_from: string;
  effective_to?: string;
}

export interface DisputePackage {
  order_id: string;
  marketplace: string;
  amount_claimed: string;
  ticket_text: string;
  evidence_manifest_csv: string;
  created_at: string;
}

export interface AuditEvent {
  id: string;
  workspace_id: string;
  user_id?: string;
  action: string;
  resource_type: string;
  resource_id?: string;
  details: Record<string, any>;
  ip_address?: string;
  created_at: string;
}
