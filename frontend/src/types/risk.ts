export interface UserRiskProfile {
    id: string;
    user_id: string;
    answers: Record<string, string>;
    score: number | null;
    risk_category: string | null;
    updated_at: string;
}

export interface UserRiskProfileCreate {
    answers: Record<string, string>;
}
