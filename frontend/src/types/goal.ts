export interface GoalLink {
  id: string;
  goal_id: string;
  user_id: string;
  portfolio_id?: string;
  asset_id?: string;
}

export interface Goal {
  id: string;
  user_id: string;
  name: string;
  target_amount: number;
  target_date: string; // ISO date string
  created_at: string; // ISO datetime string
  links: GoalLink[];
}

export type GoalCreate = Omit<Goal, "id" | "user_id" | "created_at" | "links">;

export type GoalUpdate = Partial<GoalCreate>;

export type GoalLinkCreate = Omit<GoalLink, "id" | "goal_id" | "user_id">;
