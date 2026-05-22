package com.filimon_stefan.deskbudhydration.preparation;

public class WaterGoalCalculator {

    // Constante pentru ml per kg
    private static final int ML_PER_KG_MEN = 35;
    private static final int ML_PER_KG_WOMEN = 31;

    // Limite European Food Safety Authority
    private static final int MIN_GOAL_MEN = 2000;
    private static final int MIN_GOAL_WOMEN = 1600;
    private static final int MAX_GOAL = 5000;

    public static int calculeazaGoal(float greutate, String sex) {
        int mlPerKg;
        int minGoal;

        if(sex.equals("M")){
            mlPerKg = ML_PER_KG_MEN;
            minGoal = MIN_GOAL_MEN;
        }else {
            mlPerKg = ML_PER_KG_WOMEN;
            minGoal = MIN_GOAL_WOMEN;
        }

        int goal = Math.round(greutate * mlPerKg);
        goal = verificaLimite(goal,minGoal);
        return goal;
    }

    private static int verificaLimite(int goal, int minGoal){
        if(goal < minGoal){
            goal = minGoal;
        }
        if (goal > MAX_GOAL){
            goal = MAX_GOAL;
        }

        return goal;
    }

}
