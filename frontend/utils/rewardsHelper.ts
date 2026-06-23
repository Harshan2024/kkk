import { VirtualReward } from "../services/api";

export function getSafeRewards(rewards: any): VirtualReward[] {
  if (!Array.isArray(rewards)) {
    console.warn("Invalid rewards payload", rewards);
    return [];
  }
  return rewards;
}
