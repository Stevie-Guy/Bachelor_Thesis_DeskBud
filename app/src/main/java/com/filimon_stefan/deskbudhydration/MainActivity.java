package com.filimon_stefan.deskbudhydration;

import android.os.Bundle;

import androidx.activity.EdgeToEdge;
import androidx.appcompat.app.AppCompatActivity;
import androidx.core.graphics.Insets;
import androidx.core.view.ViewCompat;
import androidx.core.view.WindowInsetsCompat;
import androidx.viewpager2.widget.ViewPager2;

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

        // Compatibilitate pentru noile device-uri
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