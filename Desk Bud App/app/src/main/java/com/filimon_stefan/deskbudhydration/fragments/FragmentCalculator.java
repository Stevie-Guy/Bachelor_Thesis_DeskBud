package com.filimon_stefan.deskbudhydration.fragments;

import android.os.Bundle;
import android.view.LayoutInflater;
import android.view.View;
import android.view.ViewGroup;
import android.widget.Button;
import android.widget.ImageButton;
import android.widget.TextView;
import android.widget.Toast;

import androidx.annotation.NonNull;
import androidx.annotation.Nullable;
import androidx.fragment.app.Fragment;

import com.filimon_stefan.deskbudhydration.preparation.PrefsHelper;
import com.filimon_stefan.deskbudhydration.R;
import com.filimon_stefan.deskbudhydration.preparation.WaterGoalCalculator;
import com.google.android.material.card.MaterialCardView;
import com.google.android.material.dialog.MaterialAlertDialogBuilder;
import com.google.android.material.textfield.TextInputEditText;

public class FragmentCalculator extends Fragment {
    private TextInputEditText tietGreutate;
    private Button btnBarbat;
    private Button btnFemeie;
    private Button btnCalculeaza;
    private ImageButton btnInfo;
    private MaterialCardView cardRezultat;
    private TextView tvRezultatGoalLitri;
    private TextView tvRezultatGoalMililitri;
    private String genSelectat = "M"; // default am setat M
    private PrefsHelper prefs;

    @Nullable
    @Override
    public View onCreateView(@NonNull LayoutInflater inflater,
                             @Nullable ViewGroup container,
                             @Nullable Bundle savedInstanceState){
        return inflater.inflate(R.layout.fragment_calculator, container, false);
    }

    @Override
    public void onViewCreated(@NonNull View view, @Nullable Bundle savedInstanceState){
        super.onViewCreated(view, savedInstanceState);

        prefs = new PrefsHelper(requireContext());

        tietGreutate = view.findViewById(R.id.tiet_greutate);
        btnBarbat = view.findViewById(R.id.btn_calculator_barbat);
        btnFemeie = view.findViewById(R.id.btn_calculator_femeie);
        btnCalculeaza = view.findViewById(R.id.btn_calculeaza);
        btnInfo = view.findViewById(R.id.btn_info_formula);
        cardRezultat = view.findViewById(R.id.card_rezultat);
        tvRezultatGoalLitri = view.findViewById(R.id.tv_rezultat_goal);
        tvRezultatGoalMililitri = view.findViewById(R.id.tv_rezultat_goal_ml);

        // Persistenta cu ajutorul Shared Pref, daca deja exista valori
        if (prefs.getGreutate() > 0){
            tietGreutate.setText(String.valueOf(prefs.getGreutate()));
        }

        if (!prefs.getGen().isEmpty()){
            genSelectat = prefs.getGen();
        }

        toggleButoaneGen();

        if(prefs.aFolositCalculator()){
            afiseazaRezultat(prefs.getGoal());
        }
        
        btnBarbat.setOnClickListener(v -> {
            genSelectat = "M";
            toggleButoaneGen();
        });

        btnFemeie.setOnClickListener(v -> {
            genSelectat = "F";
            toggleButoaneGen();
        });

        btnCalculeaza.setOnClickListener(v -> calculeazaGoal());

        btnInfo.setOnClickListener(v -> afiseazaDialogFormule());
    }

    private void toggleButoaneGen(){
        if(genSelectat.equals("M")){
            btnBarbat.setBackgroundTintList(
                    getResources().getColorStateList(R.color.primary_buttons, null));
            btnBarbat.setTextColor(getResources().getColor(R.color.white, null));

            btnFemeie.setBackgroundTintList(
                    getResources().getColorStateList(R.color.white, null));
            btnFemeie.setTextColor(getResources().getColor(R.color.primary_buttons, null));
        }else{
            btnFemeie.setBackgroundTintList(
                    getResources().getColorStateList(R.color.primary_buttons, null));
            btnFemeie.setTextColor(getResources().getColor(R.color.white, null));

            btnBarbat.setBackgroundTintList(
                    getResources().getColorStateList(R.color.white, null));
            btnBarbat.setTextColor(getResources().getColor(R.color.primary_buttons, null));
        }
    }

    private void calculeazaGoal(){
        String greutateText;
        if (tietGreutate.getText() != null) {
            greutateText = tietGreutate.getText().toString().trim();
        }else {
            greutateText = "";
        }

        // Validam daca greutatea a fost introdusa
        if (greutateText.isEmpty()){
            Toast.makeText(requireContext(), "Introdu greutatea ta", Toast.LENGTH_LONG).show();
            return;
        }

        float greutate;
        try {
            greutate = Float.parseFloat(greutateText);
        } catch (NumberFormatException e){
            Toast.makeText(requireContext(), "Format greșit. Exemplu corect: 59.7", Toast.LENGTH_LONG).show();
            return;
        }

        if(greutate < 20 || greutate > 250){
            Toast.makeText(requireContext(), "Greutatea introdusă nu e validă. Va rugăm introduceți o valoare reală.", Toast.LENGTH_LONG).show();
        }

        // Calcularea goal-ului
        int goal = WaterGoalCalculator.calculeazaGoal(greutate, genSelectat);

        prefs.setGreutate(greutate);
        prefs.setGen(genSelectat);
        prefs.setGoal(goal);

        afiseazaRezultat(goal);
    }

    private void afiseazaRezultat(int goal){
        float litri = goal / 1000f;
        String textLitri = String.format("%.1f L", litri);
        String textMililitri = "(" + goal + " ml)";

        tvRezultatGoalLitri.setText(textLitri);
        tvRezultatGoalMililitri.setText(textMililitri);
        cardRezultat.setVisibility(View.VISIBLE);
    }

    private void afiseazaDialogFormule(){
        String mesaj = "Goal-ul zilnic se calculează în funcție de greutate și gen:\n\n" +
                "- Bărbați: greutate * 35 ml\n" +
                "- Femei: greutate * 31 ml\n\n" +
                "Pentru siguranță, goal-ul este limitat între 1600-5000 ml.";

        new MaterialAlertDialogBuilder(requireContext())
                .setTitle("Cum se calculează goal-ul?")
                .setMessage(mesaj)
                .setPositiveButton("Ok", null)
                .show();
    }
}
