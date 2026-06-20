package com.filimon_stefan.deskbudhydra.fragments;

import android.os.Bundle;
import android.view.LayoutInflater;
import android.view.View;
import android.view.ViewGroup;
import android.widget.TextView;

import androidx.annotation.NonNull;
import androidx.annotation.Nullable;
import androidx.fragment.app.Fragment;
import androidx.recyclerview.widget.LinearLayoutManager;
import androidx.recyclerview.widget.RecyclerView;

import com.filimon_stefan.deskbudhydra.R;
import com.filimon_stefan.deskbudhydra.adapters.IstoricAdapter;
import com.filimon_stefan.deskbudhydra.preparation.PrefsHelper;
import com.filimon_stefan.deskbudhydra.preparation.ZiIstoric;

import java.util.List;

public class FragmentHistory extends Fragment {
    private RecyclerView rvIstoric;
    private TextView tvIstoricGol;
    private IstoricAdapter adapter;

    private PrefsHelper prefs;

    @Nullable
    @Override
    public View onCreateView(@NonNull LayoutInflater inflater,
                             @Nullable ViewGroup container,
                             @Nullable Bundle savedInstanceState){
        return inflater.inflate(R.layout.fragment_history, container, false);
    }

    @Override
    public void onViewCreated(@NonNull View view, @Nullable Bundle savedInstanceState){
        super.onViewCreated(view,savedInstanceState);

        prefs = new PrefsHelper(requireContext());

        rvIstoric = view.findViewById(R.id.rv_istoric);
        tvIstoricGol = view.findViewById(R.id.tv_istoric_gol);

        rvIstoric.setLayoutManager(new LinearLayoutManager(requireContext()));
    }

    @Override
    public void onResume(){
        super.onResume();
        refreshIstoric();
    }

    private void refreshIstoric(){
        List<ZiIstoric> listaIstoric = prefs.getIstoric();

        if (listaIstoric.isEmpty()){
            rvIstoric.setVisibility(View.GONE);
            tvIstoricGol.setVisibility(View.VISIBLE);
        }else {
            rvIstoric.setVisibility(View.VISIBLE);
            tvIstoricGol.setVisibility(View.GONE);

            adapter = new IstoricAdapter(listaIstoric);
            rvIstoric.setAdapter(adapter);
        }
    }

    private void adaugaZiTest(){
        java.util.Random random = new java.util.Random();
        int zileInapoi = prefs.getIstoric().size()+1;

        java.time.LocalDate data = java.time.LocalDate.now().minusDays(zileInapoi);
        String dataIso = data.toString();
        String dataFormatata = data.format(
                java.time.format.DateTimeFormatter.ofPattern("MMMM d'th' yyyy"));

        int ml = 800 + random.nextInt(2000);
        int goal = 2000;

        ZiIstoric zi = new ZiIstoric(dataIso, dataFormatata, ml, goal);
        prefs.adaugaZiInIstoric(zi);

        refreshIstoric();
    }
}
