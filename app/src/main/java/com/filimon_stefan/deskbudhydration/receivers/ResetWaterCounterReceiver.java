package com.filimon_stefan.deskbudhydration.receivers;

import android.content.BroadcastReceiver;
import android.content.Context;
import android.content.Intent;
import android.util.Log;

import com.filimon_stefan.deskbudhydration.preparation.PrefsHelper;

public class ResetWaterCounterReceiver extends BroadcastReceiver {
    @Override
    public void onReceive(Context context, Intent intent){
        Log.d("ResetReceiver", "Reset declansat. Este 12 noaptea.");

        PrefsHelper prefsHelper = new PrefsHelper(context);
        prefsHelper.verificaNouaZi();

        AlarmScheduler.programeazaAlarma(context);
    }
}
