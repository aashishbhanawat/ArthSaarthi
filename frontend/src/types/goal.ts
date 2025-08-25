export interface GoalLink {
  id: string;
  goal_id: string;
  portfolio_id?: string;
  asset_id?: string;
  user_id: string;
}

export interface Goal {
  id: string;
  name: string;
  target_amount: number;
  target_date: string; // ISO date string
  created_at: string; // ISO datetime string
  user_id: string;
  links: GoalLink[];
}

export type GoalCreate = Omit<Goal, "id" | "user_id" | "created_at" | "links">;
export type GoalUpdate = Partial<GoalCreate>;
