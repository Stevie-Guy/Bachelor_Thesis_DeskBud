package com.filimon_stefan.deskbudhydra.notifications;

import android.app.NotificationChannel;
import android.app.NotificationManager;
import android.app.PendingIntent;
import android.content.Context;
import android.content.Intent;
import android.os.Build;

import androidx.core.app.NotificationCompat;
import androidx.core.content.ContextCompat;

import com.filimon_stefan.deskbudhydra.R;
import com.filimon_stefan.deskbudhydra.main.MainActivity;

public class NotificationHelper {
    public static final String CHANNEL_ID = "deskbud_hydra_channel";
    public static final String CHANNEL_NAME = "Hidratare";
    public static final int ID_NOTIFICARE_DIMINEATA = 100;
    public static final int ID_NOTIFICARE_INACTIVITATE = 200;

    public static void creeazaCanal(Context context){
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O){
            NotificationChannel channel = new NotificationChannel(
                    CHANNEL_ID,
                    CHANNEL_NAME,
                    NotificationManager.IMPORTANCE_DEFAULT
            );
            channel.setDescription("Reminder hidratare");

            NotificationManager manager = context.getSystemService(NotificationManager.class);
            if (manager != null){
                manager.createNotificationChannel(channel);
            }
        }
    }

    public static void trimiteNotificare(Context context, int notificationId, String titlu, String mesaj){
        creeazaCanal(context);

        // Intent care deschide aplicația la click (notificarea din bara gen)
        Intent intent = new Intent(context, MainActivity.class);
        intent.setFlags(Intent.FLAG_ACTIVITY_NEW_TASK | Intent.FLAG_ACTIVITY_CLEAR_TASK);
        PendingIntent pendingIntent = PendingIntent.getActivity(
                context, 0, intent,
                PendingIntent.FLAG_UPDATE_CURRENT | PendingIntent.FLAG_IMMUTABLE
        );

        NotificationCompat.Builder builder = new NotificationCompat.Builder(context, CHANNEL_ID)
                .setSmallIcon(R.drawable.water_bottle_logo)
                .setContentTitle(titlu)
                .setContentText(mesaj)
                .setStyle(new NotificationCompat.BigTextStyle().bigText(mesaj))
                .setPriority(NotificationCompat.PRIORITY_DEFAULT)
                .setContentIntent(pendingIntent)
                .setAutoCancel(true);

        NotificationManager manager = (NotificationManager) context.getSystemService(Context.NOTIFICATION_SERVICE);
        if (manager != null){
            manager.notify(notificationId, builder.build());
        }
    }
}
