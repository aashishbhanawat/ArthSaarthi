export interface Goal {
  id: string;
  name: string;
  target_amount: number;
  target_date: string; // or Date
  user_id: string;
}

export interface GoalLink {
  id: string;
  goal_id: string;
  portfolio_id?: string;
  asset_id?: string;
  user_id: string;
}

export type GoalCreate = Omit<Goal, 'id' | 'user_id'>;
export type GoalUpdate = Partial<GoalCreate>;

export type GoalLinkCreate = Omit<GoalLink, 'id' | 'user_id'>;
