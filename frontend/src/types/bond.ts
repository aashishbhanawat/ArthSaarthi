export enum BondType {
    CORPORATE = 'CORPORATE',
    GOVERNMENT = 'GOVERNMENT',
    SGB = 'SGB',
    TBILL = 'TBILL',
}

export enum PaymentFrequency {
    ANNUALLY = 'ANNUALLY',
    SEMI_ANNUALLY = 'SEMI_ANNUALLY',
    QUARTERLY = 'QUARTERLY',
    MONTHLY = 'MONTHLY',
}

export interface Bond {
    id: string;
    asset_id: string;
    bond_type: BondType;
    face_value: number | null;
    coupon_rate: number | null;
    maturity_date: string;
    isin: string | null;
    payment_frequency: PaymentFrequency | null;
    first_payment_date: string | null;
}

export interface BondCreate extends Omit<Bond, 'id' | 'asset_id'> {
    // For creating a bond, we might link it via asset_id if the asset already exists
}

export interface BondUpdate extends Partial<BondCreate> {}