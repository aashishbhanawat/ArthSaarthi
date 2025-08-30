export interface Goal {
  id: string;
  name: string;
  target_amount: number;
  target_date: string; // or Date
  user_id: string;
  links: GoalLink[];
  current_amount: number;
  progress: number;
}

interface LinkedAsset {
    id: string;
    name: string;
    ticker_symbol: string;
}

interface LinkedPortfolio {
    id: string;
    name: string;
}

export interface GoalLink {
  id: string;
  goal_id: string;
  portfolio_id?: string;
  asset_id?: string;
  user_id: string;
  asset?: LinkedAsset;
  portfolio?: LinkedPortfolio;
}

export type GoalCreate = Omit<Goal, 'id' | 'user_id'>;
export type GoalUpdate = Partial<GoalCreate>;

export type GoalLinkCreate = Omit<GoalLink, 'id' | 'user_id'>;
