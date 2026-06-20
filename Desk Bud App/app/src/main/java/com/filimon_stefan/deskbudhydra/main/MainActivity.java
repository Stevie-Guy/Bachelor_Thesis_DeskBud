package com.filimon_stefan.deskbudhydra.main;

import android.Manifest;
import android.content.pm.PackageManager;
import android.os.Build;
import android.os.Bundle;

import androidx.activity.EdgeToEdge;
import androidx.appcompat.app.AppCompatActivity;
import androidx.core.graphics.Insets;
import androidx.core.view.ViewCompat;
import androidx.core.view.WindowInsetsCompat;
import androidx.viewpager2.widget.ViewPager2;

import com.filimon_stefan.deskbudhydra.R;
import com.filimon_stefan.deskbudhydra.adapters.ViewPageAdapter;
import com.filimon_stefan.deskbudhydra.notifications.NotificationScheduler;
import com.filimon_stefan.deskbudhydra.preparation.PrefsHelper;
import com.filimon_stefan.deskbudhydra.receivers.AlarmScheduler;
import com.google.android.material.tabs.TabLayout;
import com.google.android.material.tabs.TabLayoutMediator;

public class MainActivity extends AppCompatActivity {
    private TabLayout tabLayout;
    private ViewPager2 vPager;
    private ViewPageAdapter adapter;

    // Numele taburilor din XML
    private final String[] numeTaburi = {"Azi", "Istoric", "Calculator"};

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        EdgeToEdge.enable(this);
        setContentView(R.layout.activity_main);

        PrefsHelper prefs = new PrefsHelper(this);
        prefs.verificaNouaZi();
        AlarmScheduler.programeazaAlarma(this);

        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU){
            if (checkSelfPermission(Manifest.permission.POST_NOTIFICATIONS)!= PackageManager.PERMISSION_GRANTED){
                requestPermissions(new String[]{Manifest.permission.POST_NOTIFICATIONS}, 1);
            }
        }

        NotificationScheduler.programeazaNotificareDimineata(this);

        NotificationScheduler.resetTimerInactivitate(this);

        // Compatibilitate pentru noile device-uri edge to edge
        ViewCompat.setOnApplyWindowInsetsListener(findViewById(R.id.main), (v, insets) -> {
            Insets systemBars = insets.getInsets(WindowInsetsCompat.Type.systemBars());
            v.setPadding(systemBars.left, systemBars.top, systemBars.right, systemBars.bottom);
            return insets;
        });

        tabLayout = findViewById(R.id.layout_tabs);
        vPager = findViewById(R.id.view_pager);

        adapter = new ViewPageAdapter(this);
        vPager.setAdapter(adapter);

        new TabLayoutMediator(tabLayout, vPager,
                (tab, position) -> tab.setText(numeTaburi[position])
        ).attach();
    }
}