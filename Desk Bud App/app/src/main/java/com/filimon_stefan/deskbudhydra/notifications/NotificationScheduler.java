package com.filimon_stefan.deskbudhydra.notifications;

import android.app.AlarmManager;
import android.app.PendingIntent;
import android.content.Context;
import android.content.Intent;
import android.util.Log;

import java.util.Calendar;

public class NotificationScheduler {
    private static final int REQUEST_CODE_DIMINEATA = 1001;
    private static final int REQUEST_CODE_INACTIVITATE = 1002;
    private static final long INTERVAL_4_ORE = 3 * 60 * 60 * 1000L;

    public static void programeazaNotificareDimineata(Context context){
        AlarmManager alarmManager = (AlarmManager) context.getSystemService(Context.ALARM_SERVICE);
        Intent intent = new Intent(context, NotificareDimineataReceiver.class);

        PendingIntent notificareExistenta = PendingIntent.getBroadcast(
                context,
                REQUEST_CODE_DIMINEATA,
                intent,
                PendingIntent.FLAG_UPDATE_CURRENT | PendingIntent.FLAG_IMMUTABLE
        );

        if (notificareExistenta != null) {
            Log.d("NotifScheduler", "Notificare de dimineata gasita");
            return;
        }

        PendingIntent pendingIntent = PendingIntent.getBroadcast(
                context,
                REQUEST_CODE_DIMINEATA,
                intent,
                PendingIntent.FLAG_UPDATE_CURRENT | PendingIntent.FLAG_IMMUTABLE
        );

        Calendar calendar = Calendar.getInstance();
        calendar.set(Calendar.HOUR_OF_DAY, 9);
        calendar.set(Calendar.MINUTE, 0);
        calendar.set(Calendar.SECOND, 0);
        calendar.set(Calendar.MILLISECOND, 0);

        // Dacă e deja trecut de 09:00, programăm pentru mâine
        if (calendar.getTimeInMillis() <= System.currentTimeMillis()) {
            calendar.add(Calendar.DAY_OF_YEAR, 1);
        }

        alarmManager.setExactAndAllowWhileIdle(
                AlarmManager.RTC_WAKEUP,
                calendar.getTimeInMillis(),
                pendingIntent
        );

        // Scot codul dupa, momentan sa verific in log ca apare
        Log.d("NotifScheduler", "Notificare dimineata programata: " + calendar.getTime());
    }

    public static void resetTimerInactivitate(Context context) {
        AlarmManager alarmManager = (AlarmManager) context.getSystemService(Context.ALARM_SERVICE);
        Intent intent = new Intent(context, NotificareInactivitateReceiver.class);

        PendingIntent pendingIntent = PendingIntent.getBroadcast(
                context,
                REQUEST_CODE_INACTIVITATE,
                intent,
                PendingIntent.FLAG_UPDATE_CURRENT | PendingIntent.FLAG_IMMUTABLE
        );

        // Anulăm alarma anterioară (dacă exista)
        alarmManager.cancel(pendingIntent);

        long timpDeclansare = System.currentTimeMillis() + INTERVAL_4_ORE;

        alarmManager.setExact(
                AlarmManager.RTC_WAKEUP,
                timpDeclansare,
                pendingIntent
        );

        // Scot codul dupa, momentan sa verific in log ca apare
        Log.d("NotifScheduler", "Timer inactivitate resetat. Notificare peste 4h. " + timpDeclansare);
    }

    public static void anuleazaTimerInactivitate(Context context) {
        AlarmManager alarmManager = (AlarmManager) context.getSystemService(Context.ALARM_SERVICE);
        Intent intent = new Intent(context, NotificareInactivitateReceiver.class);

        PendingIntent pendingIntent = PendingIntent.getBroadcast(
                context,
                REQUEST_CODE_INACTIVITATE,
                intent,
                PendingIntent.FLAG_UPDATE_CURRENT | PendingIntent.FLAG_IMMUTABLE
        );

        alarmManager.cancel(pendingIntent);


    }
}
