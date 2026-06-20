package com.filimon_stefan.deskbudhydra.notifications;

import android.content.BroadcastReceiver;
import android.content.Context;
import android.content.Intent;

import com.filimon_stefan.deskbudhydra.preparation.PrefsHelper;

import java.util.Calendar;

public class NotificareInactivitateReceiver extends BroadcastReceiver {
    @Override
    public void onReceive(Context context, Intent intent){
        int oraAcum = Calendar.getInstance().get(Calendar.HOUR_OF_DAY);
        if (oraAcum < 9){
            return;
        }

        PrefsHelper prefs = new PrefsHelper(context);
        int mlAzi = prefs.getMlBautiAzi();
        int goal = prefs.getGoal();

        if(mlAzi >= goal) return;

        int procent = (int) Math.floor((mlAzi * 100f) / goal);
        int procentRamas = 100 - procent;

        String mesaj = "Mai ai " + procentRamas + "% până atingi obiectivul. Keep going!";

        NotificationHelper.trimiteNotificare(
                context,
                NotificationHelper.ID_NOTIFICARE_INACTIVITATE,
                "Pauză de hidratare 🥤",
                mesaj
        );
    }
}
