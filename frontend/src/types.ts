// types.ts — mirrors schemas.py Pydantic models

export type PaymentMethod = 'stars' | 'ton' | 'stripe' | 'xmr' | 'btc' | 'eth' | 'ltc' | 'usdt' | 'token' | 'crypto'

export type RedemptionType = 'ton_payout' | 'hour_booking'

export interface InvoiceRequest {
  method: PaymentMethod
  amount_usd: number
  coin?: string
  user_id: number
}

export interface InvoiceResponse {
  payment_id: string
  method: PaymentMethod
  amount_usd: number
  order_id?: number
  invoice_link?: string
  ton_address?: string
  ton_amount?: string
  checkout_url?: string
  pay_address?: string
  pay_amount?: string
  pay_currency?: string
}

export interface CreditBalance {
  user_id: number
  balance_usd: number
  token_count: number
  tokens_minted_total: number
  tokens_redeemed_total: number
}

export interface MintRequest {
  token_count: number
  ton_wallet_address: string
}

export interface MintResponse {
  minted: number
  jetton_tx_hash: string
  remaining_credit_usd: number
}

export interface RedeemRequest {
  token_count: number
  redemption_type: RedemptionType
  ton_wallet_address?: string
}

export interface RedeemResponse {
  redeemed: number
  redemption_type: RedemptionType
  ton_tx_hash?: string
  booking_url?: string
}

export interface LedgerEntry {
  id: number
  amount_usd: number
  kind: string
  ref_id: string
  created_at: string
}

export interface LedgerResponse {
  entries: LedgerEntry[]
  total: number
}

export interface OrderEntry {
  id: number
  sku: string
  amount_usd: number
  payment_method: string
  status: string
  created_at: string
  paid_at?: string
}

export interface OrdersResponse {
  orders: OrderEntry[]
  total: number
}

export interface IntakeRequest {
  kind: 'audit' | 'pentest'
  company: string
  contact_email: string
  scope: string
  assets?: string
  timeline?: string
}

export interface IntakeResponse {
  id: number
  kind: string
  status: string
}

export interface BookingSlot {
  start: string
  end: string
  available: boolean
}

export interface SlotsResponse {
  slots: BookingSlot[]
}

export interface BookingRequest {
  slot_start: string
  hours: number
  notes?: string
}

export interface BookingResponse {
  id: number
  slot_start: string
  slot_end: string
  hours: number
  status: string
}

export interface Product {
  id: string
  name: string
  description: string
  price_usd: number
  icon: string
  sku: string
  badge?: string
}
