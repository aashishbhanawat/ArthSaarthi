import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import * as goalApi from "../services/goalApi";
import { GoalCreate, GoalUpdate, GoalLinkCreate } from "../types/goal";

export const useGoals = () => {
  return useQuery({
    queryKey: ["goals"],
    queryFn: goalApi.getGoals,
  });
};

export const useCreateGoal = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: GoalCreate) => goalApi.createGoal(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["goals"] });
    },
  });
};

export const useUpdateGoal = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: GoalUpdate }) =>
      goalApi.updateGoal(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["goals"] });
    },
  });
};

export const useDeleteGoal = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => goalApi.deleteGoal(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["goals"] });
    },
  });
};

export const useCreateGoalLink = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({
      goalId,
      data,
    }: {
      goalId: string;
      data: GoalLinkCreate;
    }) => goalApi.createGoalLink(goalId, data),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ["goals"] });
      queryClient.invalidateQueries({ queryKey: ["goal", variables.goalId] });
    },
  });
};

export const useDeleteGoalLink = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({
      goalId,
      linkId,
    }: {
      goalId: string;
      linkId: string;
    }) => goalApi.deleteGoalLink(goalId, linkId),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ["goals"] });
      queryClient.invalidateQueries({ queryKey: ["goal", variables.goalId] });
    },
  });
};
