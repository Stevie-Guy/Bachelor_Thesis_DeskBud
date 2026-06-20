package com.filimon_stefan.deskbudhydra.notifications;

import android.content.BroadcastReceiver;
import android.content.Context;
import android.content.Intent;

public class NotificareDimineataReceiver extends BroadcastReceiver {
    @Override
    public void onReceive(Context context, Intent intent){
        NotificationHelper.trimiteNotificare(
                context,
                NotificationHelper.ID_NOTIFICARE_DIMINEATA,
                "Este ora 9 dimineața ☀",
                "O zi bună începe cu un pahar de apă!"
        );

        NotificationScheduler.programeazaNotificareDimineata(context);
    }
}
