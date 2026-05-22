package com.filimon_stefan.deskbudhydration.adapters;

import androidx.annotation.NonNull;
import androidx.fragment.app.Fragment;
import androidx.fragment.app.FragmentActivity;
import androidx.viewpager2.adapter.FragmentStateAdapter;

import com.filimon_stefan.deskbudhydration.fragments.FragmentCalculator;
import com.filimon_stefan.deskbudhydration.fragments.FragmentDailyGoal;
import com.filimon_stefan.deskbudhydration.fragments.FragmentHistory;

public class ViewPageAdapter extends FragmentStateAdapter {
    public ViewPageAdapter(@NonNull FragmentActivity activity){
        super(activity);
    }

    @NonNull
    @Override
    public Fragment createFragment(int position) {
        switch (position){
            case 0:
                return new FragmentDailyGoal();
            case 1:
                return new FragmentHistory();
            case 2:
                return new FragmentCalculator();
            default:
                return new FragmentDailyGoal();
        }
    }

    @Override
    public int getItemCount() {
        return 3; // numar de taburi
    }
}
