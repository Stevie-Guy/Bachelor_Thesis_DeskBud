package com.filimon_stefan.deskbudhydra.receivers;

import android.content.BroadcastReceiver;
import android.content.Context;
import android.content.Intent;

import com.filimon_stefan.deskbudhydra.notifications.NotificationScheduler;

public class BootReceiver extends BroadcastReceiver {
    @Override
    public void onReceive(Context context, Intent intent){
        if (Intent.ACTION_BOOT_COMPLETED.equals(intent.getAction())){
            AlarmScheduler.programeazaAlarma(context);
        }
        NotificationScheduler.programeazaNotificareDimineata(context);
    }
}
