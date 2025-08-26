import { Asset } from './asset';
import { Portfolio } from './portfolio';

export interface GoalLink {
  id:string;
  goal_id: string;
  portfolio_id?: string;
  asset_id?: string;
  user_id: string;
  portfolio?: Portfolio;
  asset?: Asset;
}

export interface Goal {
  id: string;
  name: string;
  target_amount: number;
  target_date: string; // ISO date string
  created_at: string; // ISO datetime string
  user_id: string;
  links: GoalLink[];
  current_value?: number;
  progress?: number;
}

export type GoalCreate = Omit<Goal, "id" | "user_id" | "created_at" | "links">;
export type GoalUpdate = Partial<GoalCreate>;

export interface GoalLinkCreateIn {
    portfolio_id?: string;
    asset_id?: string;
}
